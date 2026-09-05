from flockwave.gps.vectors import GPSCoordinate

home_pos: list = []
goal_points: list = []
goal_table: list = []
return_goal_table: list = []
grid_path_table: list = []
Takeoff_Alt: str = 2.5
logCounter: int = 0
log_file_path: str = ""
area_covered: int = 0
minutes: int = 0
seconds: int = 0
removed_uav_grid_file_name = []
removed_uav_grid_path_length = []
gimbal_target = []
mission = []
mission_index: int = 0
speed_match = False
reached_height = False

vtol_takeoff_height = {
    # 5:30,
    # 7:35,
    # 8:40,
    # 11:45,
    # 14:50,
    # 15:30,
    # 20:35,
    # 22:40,
    # 24:45,
    # 25:50,
    1: 30,
    2: 35,
    3: 40,
    4: 45,
    5: 50,
    6: 30,
    7: 35,
    8: 40,
    9: 45,
    10: 50,
    11: 55,
    12: 60,
    13: 65,
    14: 70,
    15: 75,
}
alts: dict[int, int] = {
    1: 50,
    2: 60,
    3: 70,
    4: 80,
    5: 90,
    6: 100,
    7: 110,
    8: 120,
    9: 130,
    10: 140,
    11: 150,
    12: 160,
    13: 170,
    14: 180,
    15: 190,
}

drone = {
    # 5:1,
    # 7:2,
    # 8:3,
    # 11:4,
    # 14:5,
    # 15:6,
    # 20:7,
    # 22:8,
    # 24:9,
    # 25:10,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: 11,
    12: 12,
    13: 13,
    14: 14,
    15: 15,
}


vtol_rtl_height = {
    # 5:50,
    # 7:60,
    # 8:70,
    # 11:80,
    # 14:90,
    # 15:50,
    # 20:60,
    # 22:70,
    # 24:80,
    # 25:90,
    1: 30,
    2: 35,
    3: 40,
    4: 45,
    5: 50,
    6: 30,
    7: 35,
    8: 40,
    9: 45,
    10: 50,
}

past_distance: int | float = 0.0
plat: float = 0.0
plon: float = 0.0

trail: bool = False
target_confirmation = GPSCoordinate(lat=0, lon=0, amsl=None, ahl=None, agl=None)

airspeed_failure_ms = 26

radius = 200
clock_anticlock = 1


def changeRadius(rad):
    global radius
    radius = rad


def getRadius():
    global radius
    return radius


def changeClockOrAnticlock(clock):
    global clock_anticlock
    clock_anticlock = clock


def getClock():
    global clock_anticlock
    return clock_anticlock


def changeAlts(paramalts):
    global alts
    alts = paramalts
    return alts


def changeSingleAlt(id, alt):
    global alts
    alts[id] = alt
    return alts


def getAlts():
    global alts
    return alts


def changeReachHeight(value: bool):
    global reached_height
    reached_height = value


def getReachHeight():
    global reached_height
    return reached_height


def get_target_confirm():
    global target_confirmation
    return


def update_target_confirmation(lat, lon):
    global target_confirmation
    target_confirmation.lat = lat
    target_confirmation.lon = lon


def update_trail() -> None:
    global trail
    trail = True


def get_trail() -> bool:
    global trail
    return trail


def update_past_distance(dis: int | float, plat1: float, plon1: float) -> None:
    global past_distance, plat, plon
    past_distance = dis
    plat = plat1
    plon = plon1


def get_past_distance() -> tuple[int | float]:
    global past_distance, plat, plon
    return (past_distance, plat, plon)


def update_coverage_time(area_covered1, minutes1, seconds1) -> None:
    global area_covered, minutes, seconds
    area_covered = area_covered1
    minutes = minutes1
    seconds = seconds1


def update_mission_index():
    global mission_index
    mission_index += 1


def get_mission_index():
    global mission_index
    return mission_index


def update_mission(add_mission):
    global mission
    mission.append(add_mission)


def empty_mission():
    global mission
    mission = []


def get_mission():
    global mission
    return mission


def get_coverage_time():
    return [area_covered, minutes, seconds]


def update_logCounter():
    global logCounter
    logCounter = 1


def get_logCounter():
    global logCounter
    return logCounter


def update_log_file_path(file_path):
    global log_file_path
    log_file_path = file_path


def get_log_file_path():
    global log_file_path
    return log_file_path


def update_home(home_pos_val):
    global home_pos
    home_pos = home_pos_val


def get_home():
    global home_pos
    return home_pos


def update_goal_points(goal_ponits_val):
    global goal_points
    goal_points = goal_ponits_val


def get_goal_points():
    global goal_points
    return goal_points


def update_goal_table(goal_table_val):
    global goal_table
    goal_table.append(goal_table_val)


def get_goal_table():
    global goal_table
    return goal_table


def update_return_goal_table(return_goal_table_val):
    global return_goal_table
    return_goal_table.append(return_goal_table_val)


def get_return_goal_table():
    global return_goal_table
    return return_goal_table


def update_grid_path_table(grid_path_table_val):
    global grid_path_table
    grid_path_table = grid_path_table_val


def get_grid_path_table():
    global grid_path_table
    return grid_path_table


def update_Takeoff_Alt(alt):
    global Takeoff_Alt
    Takeoff_Alt = alt


def getTakeoffAlt():
    global Takeoff_Alt
    return Takeoff_Alt


def update_RemovedUAVfilename(filename, grid_path_length):
    global removed_uav_grid_file_name, removed_uav_grid_path_length
    removed_uav_grid_file_name = filename
    removed_uav_grid_path_length = grid_path_length


def getRemovedUAVfilename():
    global removed_uav_grid_file_name
    return removed_uav_grid_file_name


def getRemovedUAVgridpathlength():
    global removed_uav_grid_path_length
    return removed_uav_grid_path_length


def find_value_in_dict(value_to_find, data_dict):
    for key, values in data_dict.items():
        if value_to_find in values:
            return key
    return None


class GobalVariable:
    vtol_takeoff_height: dict[int, int]
    alts: dict[int, int]
    drone: dict[int, int]

    def __init__(self):
        self.vtol_takeoff_height = {
            1: 30,
            2: 35,
            3: 40,
            4: 45,
            5: 50,
            6: 30,
            7: 35,
            8: 40,
            9: 45,
            10: 50,
        }

        self.alts = {
            1: 50,
            2: 60,
            3: 70,
            4: 80,
            5: 90,
            6: 100,
            7: 110,
            8: 120,
            9: 130,
            10: 140,
        }

        self.drone = {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 6,
            7: 7,
            8: 8,
            9: 9,
            10: 10,
        }

    def getAlts(self):
        return self.alts

    def getVtolAlts(self):
        return self.vtol_takeoff_height

    def getDrone(self):
        return self.drone
