import trio


class TrioSocket:
    def __init__(self):
        self.sock = trio.socket.socket(trio.socket.AF_INET, trio.socket.SOCK_DGRAM)
        self.ListenToCommand = trio.socket.socket(
            trio.socket.AF_INET, trio.socket.SOCK_DGRAM
        )
        self.status1 = []
        self.status2 = []

        self.armed = False

        self.DET = False

        self.health = False

        self.charging = False

    def map_status(state, status_map):
        result = []
        for bit_position, name, true_value, byte_index in status_map:
            bit = int(state[7 - bit_position])
            is_active = bit == true_value
            result.append((bit_position, name, true_value, byte_index, is_active))
        return result

    async def send_command(self, msg):
        send_addr = ("192.168.0.70", 5000)
        await self.ListenToCommand.sendto(msg.encode(), send_addr)
        await trio.sleep(0.5)
        data, add = await self.ListenToCommand.recvfrom(1024)
        print(data.decode().split(" | "))
        part = data.decode().split(" | ")[0]
        # return True
        print(part)
        bytes_value = bytes.fromhex(part.split(" ")[1])
        print(bytes_value.decode("ascii", errors="ignore").startswith("ACK"))
        try:
            if part.split(" ")[0] == "PWOF":
                self.health = False
                self.charging = False
                self.DET = False
            if part.split(" ")[0] == "DET":
                if bytes_value.decode("ascii", errors="ignore").startswith("ACK"):
                    self.DET = True
                    return True
                if bytes_value.decode("ascii", errors="ignore").startswith("NACK"):
                    self.DET = False
                    return False
            if bytes_value.decode("ascii", errors="ignore").startswith("ACK"):
                return True
            if bytes_value.decode("ascii", errors="ignore").startswith("NACK"):
                return False
        except Exception as e:
            print("Exception: ", e)
            return False

    # async def udpCommandListener(self):
    #     listen_add = ("0.0.0.0", 5001)
    #     await self.ListenToCommand.bind(listen_add)
    #     while True:
    #         data, addr = await self.sock.recvfrom(1024)
    #         parts = data.decode().split(" | ")
    #         for part in parts:
    #             response = part.split(" ")
    #             data = response[1]
    #             bytes_value = bytes.fromhex(data)
    #             if bytes_value.decode("ascii", errors="ignore") == "ACK":
    #                 print()

    async def udp_listener(self):
        listen_addr = ("192.168.2.117", 6000)
        # Create a UDP socket
        await self.sock.bind(listen_addr)
        print("UDP 6000")
        while True:
            data, addr = await self.sock.recvfrom(1024)
            # Split and decode
            parts = data.decode().split(" | ")
            for part in parts:
                response = part.split(" ")
                data = response[1]
                cmd = response[0]
                bytes_value = bytes.fromhex(data)
                if cmd == "HLT":
                    if bytes_value.decode("ascii", errors="ignore").startswith("ACK"):
                        try:
                            armed = False
                            state1 = format(bytes_value[3], "08b")
                            state2 = format(bytes_value[4], "08b")
                            # if state1[4] == "1" or state2[4] == "1":
                            if state1[5] == "1":
                                self.DET = True
                            else:
                                self.DET = False
                            print(self.DET)
                            if state1[4] == "1":
                                armed = True
                            if state1[2] == "1":
                                self.charging = True
                            else:
                                self.charging = False

                            self.armed = armed
                            self.status1 = state1
                            self.status2 = state2
                            print(state1, state2)
                            # Check health
                            unhealthy = False
                            for i in range(8):
                                if i in (1, 4, 5):
                                    continue
                                # if state1[i] == "1" or state2[i] == "1":
                                if state1[i] == "1":
                                    unhealthy = True
                            self.health = not unhealthy
                        except Exception as e:
                            print("Exception :", e)
                            pass

    # async def udp_listener(self):
    #     listen_addr = ("192.168.0.145", 6000)
    #     # Create a UDP socket
    #     await self.sock.bind(listen_addr)
    #     print("UDP 6000")
    #     while True:
    #         data, addr = await self.sock.recvfrom(1024)
    #         # Split and decode
    #         parts = data.decode().split(" | ")
    #         for part in enumerateparts:
    #             response = part.split(" ")
    #             data = response[1]
    #             cmd = response[0]
    #             bytes_value = bytes.fromhex(data)
    #             if cmd == "HLT":
    #                 if bytes_value.decode("ascii", errors="ignore").startswith("ACK"):
    #                     try:

    #                         state1 = format(bytes_value[3], "08b")
    #                         # status1 = self.map_status(state1, self.status_map1)
    #                         state2 = format(bytes_value[4], "08b")
    #                         # status2 = self.map_status(state2, self.status_map2)
    #                         print(state1, state2)
    #                         print(state1[4])
    #                         self.status1 = state1
    #                         self.status2 = state2
    #                     except Exception as e:
    #                         print("Exception :", e)
    #                         pass


"""

----------------------------------- RASPBERRYPI -----------------------------------
pi@raspberrypi:~/Documents/SDAL/DoubleChannel $ python main.py 
Serial Port Connected to: /dev/ttyUSB0
Serial Port Connected to: /dev/ttyUSB1
Sending Command: 0x484c54e8
DoubleChannel UDP server listening on 0.0.0.0:5000
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Received command 'ARM' from ('192.168.0.145', 58020)
--- Channel 0 (/dev/ttyUSB0) ---
Sending Command: 0x41524de0
send_command b'ARM\xe0'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
--- Channel 1 (/dev/ttyUSB1) ---
Sending Command: 0x41524de0
send_command b'ARM\xe0'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
b'ARM  | ARM 41434b0808df41434b0808df41434b0810e741434b0810e741434b0810e7'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Received command 'DET' from ('192.168.0.145', 58020)
--- Channel 0 (/dev/ttyUSB0) ---
Sending Command: 0x444554dd
send_command b'DET\xdd'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
b'DET '
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Received command 'DET' from ('192.168.0.145', 58020)
--- Channel 0 (/dev/ttyUSB0) ---
Sending Command: 0x444554dd
send_command b'DET\xdd'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Error reading response: device reports readiness to read but returned no data (device disconnected or multiple access on port?)
b'DET '
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Received command 'ABORT' from ('192.168.0.145', 58020)
--- Channel 0 (/dev/ttyUSB0) ---
Sending Command: 0x414254d7
send_command b'ABT\xd7'
--- Channel 1 (/dev/ttyUSB1) ---
Sending Command: 0x414254d7
send_command b'ABT\xd7'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
b'ABORT 41434bcf | ABORT 41434bcf'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
Sending Command: 0x484c54e8
send_command b'HLT\xe8'
^CUser interrupted.
Closing serial Port
Closing serial Port
Exception in thread Thread-1:
Traceback (most recent call last):
  File "/usr/lib/python3.9/threading.py", line 954, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.9/threading.py", line 892, in run
    self._target(*self._args, **self._kwargs)
  File "/home/pi/Documents/SDAL/DoubleChannel/main.py", line 18, in send_health_receive
    channel.serial_port.reset_input_buffer()
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 660, in reset_input_buffer
    raise PortNotOpenError()
serial.serialutil.PortNotOpenError: Attempting to use a port that is not open


----------------------------------- server -----------------------------------
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
{'type': 'X-SDAL', 'message': 'ABORT'}
00000000 00000000
0
00000000 00000000
0
['ABORT 41434bcf', 'ABORT 41434bcf']
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
00000000 00000000
0
{'type': 'X-SDAL', 'message': 'ARM'}
00000000 00000000
0
00000000 00000000
0
['ARM ', 'ARM 41434b0808df41434b0808df41434b0810e741434b0810e741434b0810e7']
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
{'type': 'X-SDAL', 'message': 'DET'}
00001000 00001000
1
00001000 00001000
1
['DET ']
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
00001000 00001000
1
{'type': 'X-SDAL', 'message': 'DET'}
['DET ']
00001001 00001001
1
{'type': 'X-SDAL', 'message': 'ABORT'}
['ABORT 41434bcf', 'ABORT 41434bcf']
00000000 00000000
0
00000000 00000000
0

"""
