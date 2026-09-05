

import socket, struct, time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('', 12002)  #receive from .....rx.py
sock.bind(server_address)
sock.setblocking(0)

while(True):
    try:       
    	#print("&&&&&")     
        # Joystick reading
        data, address = sock.recvfrom(1050)
        print ("msg", data)
        time.sleep(0.5)
        if(data=='rtl'):
        	print("rtl break")
        	break
        if(data=='velocity'):
        	print("velocity!!!!")
        	break
        if(data=='same'):
        	print("same!!!!")
        	break
        if(data=='search'):
        	break
    except:
       # print("SSS")
        pass

