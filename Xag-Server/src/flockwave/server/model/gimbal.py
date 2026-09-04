import binascii, socket, time, math, threading
from functools import lru_cache

from flockwave.gps.vectors import GPSCoordinate
from typing import Self


class Gimbal:
    """
    Class for Gimbal Connection and Calculation

    params:
        host: string | None
        port: int | None
        postion: GPSCoordinate
    """

    host: str
    port: int
    position: GPSCoordinate

    def __init__(
        self:Self, host="192.168.6.121", port=2000, position=GPSCoordinate(0, 0, 0, 0)
    ) -> None:
        self.host = host
        self.port = port
        self.tlat = -35.344588
        self.tlon = 149.174320
        self.connected = False
        self.position = position
        self.bearing = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        packet = bytearray(
            [
                0xEB,
                0x90,
                0x07,
                0x55,
                0xAA,
                0xDC,
                0x04,
                0x10,
                0x00,
                0x14,
                0x3,
            ]
        )
        self.bytePacket = bytes(packet)


        # threading.Thread(
        #     target=self.connect_to_gimbal,
        # ).start()

    def calculate_coords(self: Self) -> None:
        while self.connected:
            self.socket.sendall(self.bytePacket)
            if not self.is_connected():
                break
            data, address = self.socket.recvfrom(1024)
            self.get_latlon(data)

    def is_connected(self: Self) -> bool:
        try:
            self.socket.send(b"")
            self.connected = True
        except socket.error:
            self.connected = False
            return False
        return True

    def connect_to_gimbal(self: Self) -> None:
        try:
            # self.socket.connect((self.host, self.port))
            time.sleep(1)
            print("Connected to gimbal")
            self.connected = True
            self.run_in_background_thread()
        except socket.error as e:
            print(f"Connection failed: {e}")
            self.connected = False

    @lru_cache(maxsize=None)
    def hex_to_signed_int(self: Self, hex_str: str) -> int:
        """
        Converts a little-endian hexadecimal string to a signed integer.
        """
        value = int(hex_str, 16)
        if value >= 2 ** (len(hex_str) * 4 - 1):
            value -= 2 ** (len(hex_str) * 4)
        return value

    def extract_imu_angle(self: Self, data: str) -> tuple[float, float] | None:
        """
        Extracts and calculates the IMU angles from the provided data string.
        """
        if len(data) in [94, 108]:
            tlat = data[34:42]
            tlon = data[42:50]
            tlat = self.hex_to_signed_int(tlat)
            tlon = self.hex_to_signed_int(tlon)

            return tlat / 1e7, tlon / 1e7

    def get_latlon(self: Self, data_1: bytes) -> None:
        response_hex = binascii.hexlify(data_1).decode("utf-8")
        if len(response_hex) in [94, 108]:
            tlat, tlon = self.extract_imu_angle(response_hex)
            self.tlat = tlat
            self.tlon = tlon

    def get_target_coords(self: Self) -> tuple[float, float]:
        """
        Returns the Target Latitude and Longitude of the Gimbal.
        """
        return self.tlat, self.tlon

    def get_gps_bearing_loop(self: Self) -> None:
        """
        Calculate the GPS bearing with every 0.5sec.
        """
        while self.connected:
            self.bearing = self.get_gps_bearing(
                self.position.lat, self.position.lon, self.tlat, self.tlon
            )
            time.sleep(0.5)  # Reduce the frequency of recalculations

    @lru_cache(maxsize=None)
    def get_gps_bearing(
        self: Self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate and cache the GPS bearing based on coordinates.
        """
        rlat1 = lat1 * (math.pi / 180)
        rlat2 = lat2 * (math.pi / 180)
        rlon1 = lon1 * (math.pi / 180)
        rlon2 = lon2 * (math.pi / 180)

        # formula for bearing.
        y = math.sin(rlon2 - rlon1) * math.cos(rlat2)
        x = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(
            rlat2
        ) * math.cos(rlon2 - rlon1)
        bearing = math.atan2(y, x)  # bearing in radians
        bearing_degrees = bearing * (180 / math.pi)
        return bearing_degrees

    def run_in_background_thread(self: Self) -> None:
        # thread1 = threading.Thread(target=self.calculate_coords, daemon=True)
        thread2 = threading.Thread(target=self.get_gps_bearing_loop, daemon=True)
        # self.connection_event.wait()
        try:
            # thread1.start()
            thread2.start()
        except KeyboardInterrupt:
            self.socket.close()
