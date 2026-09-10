from concurrent.futures import ThreadPoolExecutor, as_completed

from dronekit import connect, APIException


class UAV:

    def __init__(self, conn_str, heartbeat_timeout=3, max_workers=None):
        self.conn_str = conn_str
        self.heartbeat_timeout = heartbeat_timeout
        self.max_workers = max_workers or len(conn_str)
        self.drones = [None] * len(conn_str)
        self.connect_all()

    def get_positions(self, geoToCart, config):
        return [
            (
                *[
                    coord
                    for coord in geoToCart(
                        config.origin,
                        config.endDistance,
                        [
                            drone.location.global_relative_frame.lat,
                            drone.location.global_relative_frame.lon,
                        ],
                    )
                ],
            )
            for drone in self.drones
        ]

    def connect_all(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._connect_one, i, s): i
                for i, s in enumerate(self.conn_str)
            }
            for future in as_completed(futures):
                future.result()  # re-raises any unhandled exception, if you want strictness

        connected = sum(1 for d in self.drones if d is not None)
        print(f"Number of Drones Connected: {connected}/{len(self.conn_str)}")

    def _connect_one(self, index, conn_string):
        try:
            vehicle = connect(conn_string, heartbeat_timeout=self.heartbeat_timeout)

            self.drones[index] = vehicle
            print(f"Drone {index} connected ({conn_string})")
        except APIException:
            print(f"Drone {index} failed: no heartbeat ({conn_string})")
        except Exception as e:
            print(f"Drone {index} failed: {e} ({conn_string})")

    def Loiter_param(self):
        return max(
            (drone.parameters["WP_LOITER_RAD"] for drone in self.drones), default=None
        )
