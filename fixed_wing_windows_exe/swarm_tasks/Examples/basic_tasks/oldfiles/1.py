import wmi
import netifaces

def get_wifi_ip(iface_map):
    interfaces = netifaces.interfaces()
    # print(interfaces)
    for iface in netifaces.interfaces():
        try:
            #print(iface,iface_map[iface])
            # if iface in iface_map:
            adapter = iface_map[iface]
            # print(adapter)
            addrs = netifaces.ifaddresses(iface)
            #print(addrs)
            ipv4_info = addrs.get(netifaces.AF_INET, [])
            for addr in ipv4_info:
                ip = addr.get('addr')
                if ip and (adapter == "Ethernet" or adapter=="Wi-Fi" or iface == "eth0" or iface == "ensp20" or iface == "wlan0") and ip.startswith("192.168."):
                    return ip
        except Exception as e:
            print(f"Error on interface {iface}: {e}")
    return None

def get_interface_mapping():
    c = wmi.WMI()
    # print(c.Win32_NetworkAdapter()[1])
    mappings = {}
    for nic in c.Win32_NetworkAdapter():
        # print(nic)
        if nic.GUID:
            mappings[nic.GUID.upper()] = nic.NetConnectionID or nic.Name
    return get_wifi_ip(mappings)

# Example usage
iface_map = get_interface_mapping()
print(iface_map)
# for guid, name in iface_map.items():
#     print(f"{guid} -> {name}")
# ip_address = get_wifi_ip(iface_map)

# print(ip_address)