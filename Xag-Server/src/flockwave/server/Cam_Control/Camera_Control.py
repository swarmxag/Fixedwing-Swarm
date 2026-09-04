import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def camera_control(msg, cameraip):
    global sock
    sock.sendto(msg, ("192.168.0.119", 14551))
    return True
