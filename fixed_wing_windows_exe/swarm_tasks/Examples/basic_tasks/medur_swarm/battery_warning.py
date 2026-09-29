drones = [
    {"id": 1, "battery": 85, "altitude": 120, "rssi": -55},
    {"id": 2, "battery": 42, "altitude": 118, "rssi": -72},
    {"id": 3, "battery": 18, "altitude": 121, "rssi": -85},
    {"id": 4, "battery": 67, "altitude": 119, "rssi": -61},
]

for drone in drones:
    if drone["battery"] > 50:
        battery_status = "Battery Good"
    elif drone["battery"] >= 20 and drone["battery"] <= 50:
        battery_status = "Low"
    elif drone["battery"] < 20:
        battery_status = "Critical"

    if drone["rssi"] > -60:
        rssi_status = "Good"

    elif drone["rssi"] <= -60 and drone["rssi"] >= -75:
        rssi_status = "Weak"

    elif drone["rssi"] <= -75:
        rssi_status = "Critical"

    if battery_status == "Battery Good" and rssi_status == "Good":
        overall_status = "Healthy"

    elif battery_status == "Low" and rssi_status == "Weak":
        overall_status = "Warning"

    else:
        overall_status = "Critical"
