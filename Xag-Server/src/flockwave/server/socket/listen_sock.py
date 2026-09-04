import socket, json
from datetime import datetime
from .globalVariable import *

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ("", 12009)  # receive from .....rx.py
sock.bind(server_address)
sock.setblocking(0)

def run_socket():
    with open(get_log_file_path(), "a") as file:
        while True:

            # #print("filepath",filepath)
            try:
                data, address = sock.recvfrom(1024)
                data = data.decode()
                current_time = datetime.now().strftime("%H:%M:%S")
                if (
                    (data == "start")
                    or (data == "aggregate")
                    or (data == "return")
                    or (data == "same altitude")
                    or (data == "different altitude")
                    or (data == "disperse")
                    or (data == "stop")
                    or (data == "search")
                    or (data == "circle formation")
                    or (data.startswith("Drone"))
                    or (data.startswith("vehicle"))
                    or (data.startswith("Vehicle"))
                    or (data.startswith("master_num"))
                    or (data.startswith("pos_array"))
                    or (data.startswith("Drone"))
                    or (data.startswith("home"))
                    or (data.startswith("Data"))
                    or (data == "rtl")
                    or (data == "goal")
                    or (data == "specific_bot_goal")
                    or (data == "CSV Cleared")
                    or (data.startswith("remove_bot"))
                    or (data.endswith("vehicle removed"))
                ):
                    #print(str(data), " command received")
                    file.write("{}\t{}\n".format(current_time,str(data)))
                    file.flush()
                    

                if data.startswith("home_pos"):
                    message_with_array = data
                    message = message_with_array[
                        :8
                    ]  # Assuming "home_pos" is 8 characters long
                    array_data = message_with_array[8:]
                    # Deserialize the array data
                    home_pos_data = json.loads(array_data)
                    update_home(home_pos_data)
                    
                    
                    file.write("{}\t{}\n".format(current_time,home_pos_data))
                    file.flush()
                    continue

                if data.startswith("goal_points"):
                    message_with_array = data
                    array_data = message_with_array[11:]
                    goal_points = json.loads(array_data)
                    update_goal_points(goal_points)
                    file.write("{}\tgoal_points{}\n".format(current_time,goal_points))
                    file.flush()

                if data.startswith("search,"):
                    a = data.split(",")
                    area_covered = a[1]
                    search_time = a[2]
                    grid_path_array_str = ",".join(a[3:])
                    grid_path_table = json.loads(grid_path_array_str)
                    update_grid_path_table(grid_path_table)
                    
                    minutes = int(float(search_time) // 60)
                    seconds = int(float(search_time) % 60)
                    update_coverage_time(area_covered, minutes, seconds)
                
                    
                if data.startswith("remove_uav_grid_path_file_name"):
                    a = data.split(",")
                    file_name=(a[1])
                    grid_path_length=(a[2])
                    if file_name not in getRemovedUAVfilename:
                        update_RemovedUAVfilename(file_name,grid_path_length)
                    
                a = data.split(",")
                # #print('a',a[-1],type(a[-1]))

                if a[-1].strip().startswith("path"):
                    last_element = a.pop()
                    #print("last_element", last_element, type(last_element))
                    if last_element.strip().startswith("path"):
                        h = int(last_element[4:])
                        if h not in get_goal_table():
                            update_goal_table(h)
                if a[-1].strip().startswith("return_path"):
                    # Remove the last element (which is "path4")
                    last_element = a.pop()
                    if last_element.strip().startswith("return_path"):
                        h = int(last_element[11:])
                        if h not in get_return_goal_table():

                            update_return_goal_table(h)
     
                if a[-1].strip().startswith("grid_path"):
                    last_element = a.pop()
                    if last_element.strip().startswith("grid_path"):
                        h = int(last_element[9:])
                        if h not in get_grid_path_table():
                            #print("h$$$$$$$$$$$", h)
                            update_grid_path_table(h)
                       
                # a = [value.strip("{}") for value in a]  # Remove curly braces
            except BlockingIOError:
                pass
            except Exception as e:
                print(e)
            except KeyboardInterrupt:
                print("keyboard")
                break
            except:
                pass