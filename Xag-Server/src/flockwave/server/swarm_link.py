"""Reliable server -> swarm command link (sender half).

`ReliableUdp` is a drop-in for the plain UDP socket swarm.py used to send
commands with: it keeps the `sendto(bytes, address)` signature, but wraps the
payload in a sequenced envelope and waits for the swarm's ACK, retransmitting
until it arrives (stop-and-wait, so commands are delivered in order and at
most once -- the receiver drops duplicates). The receiver half is
medur_swarm/communication/reliable.py; keep the two in sync.

    cmd: {"k":"cmd","v":1,"sid":<session>,"seq":N,"epoch":E,"p":<payload>}
    ack: {"k":"ack","sid":<session>,"seq":N,"ok":bool,"why":str}

sendto() returns True once ACKed and False if the swarm never answered (or
refused the command). Failures are also appended to the list installed by
`collect_failures()` so the request handler can report them to the GUI instead
of claiming success.
"""

import contextvars
import json
import os
import socket
import threading
import time
import uuid

ACK_TIMEOUT = float(os.environ.get("SWARM_ACK_TIMEOUT", "0.25"))
RETRIES = int(os.environ.get("SWARM_RETRIES", "4"))
MAX_PAYLOAD = 60000

_failures = contextvars.ContextVar("swarm_link_failures", default=None)


def collect_failures():
    """Start collecting delivery failures for the current request; returns
    the (initially empty) list that sendto() appends to."""
    failures = []
    _failures.set(failures)
    return failures


class ReliableUdp:
    def __init__(self, timeout=ACK_TIMEOUT, retries=RETRIES):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._timeout = timeout
        self._retries = retries
        self._sid = uuid.uuid4().hex[:12]
        self._seq = 0
        self._lock = threading.Lock()
        self.epoch = 0

    def _fail(self, address, payload, reason):
        print("[swarm_link] NOT DELIVERED to %s: %s (%s)" % (address, reason, payload[:60]))
        failures = _failures.get()
        if failures is not None:
            failures.append({"address": "%s:%s" % address, "reason": reason})
        return False

    def sendto(self, data, address):
        payload = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else str(data)
        if len(payload) > MAX_PAYLOAD:
            return self._fail(address, payload, "payload_too_large")
        with self._lock:
            self._seq += 1
            seq = self._seq
            packet = json.dumps(
                {"k": "cmd", "v": 1, "sid": self._sid, "seq": seq, "epoch": self.epoch, "p": payload},
                separators=(",", ":"),
            ).encode("utf-8")
            for _ in range(self._retries):
                self._sock.sendto(packet, address)
                deadline = time.monotonic() + self._timeout
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    self._sock.settimeout(remaining)
                    try:
                        reply, _src = self._sock.recvfrom(2048)
                        ack = json.loads(reply.decode("utf-8"))
                    except socket.timeout:
                        break
                    except (OSError, ValueError):
                        continue  # e.g. ICMP port-unreachable on Windows; keep retrying
                    if ack.get("k") == "ack" and ack.get("sid") == self._sid and ack.get("seq") == seq:
                        if ack.get("ok"):
                            return True
                        return self._fail(address, payload, ack.get("why") or "rejected")
            return self._fail(address, payload, "no_ack")
