"""Import the REAL medur_swarm package (main loop, dispatcher, runner,
lifecycle, sockets) with only the hardware-facing third-party modules faked.
Used by the lifecycle / recovery test nodes."""

import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
BASIC = os.path.dirname(PKG)
EXE = os.path.abspath(os.path.join(BASIC, "..", "..", ".."))


class _Any:
    def __getattr__(self, name):
        return _Any()

    def __call__(self, *a, **k):
        return _Any()

    def __iter__(self):
        return iter(())


def install():
    for p in (EXE, BASIC):
        if p not in sys.path:
            sys.path.insert(0, p)
    for name in ("dronekit", "netifaces", "wmi", "pymavlink", "pymavlink.mavutil"):
        if name not in sys.modules:
            m = types.ModuleType(name)
            m.__getattr__ = lambda attr, _m=name: _Any()
            sys.modules[name] = m
    try:
        import matplotlib

        matplotlib.use("Agg")
    except Exception:
        pass
