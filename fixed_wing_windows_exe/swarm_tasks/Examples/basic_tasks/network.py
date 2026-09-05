import netifaces
import platform
import subprocess
import json


class NetworkIP:

    @staticmethod
    def _is_valid_ip(ip):
        """
        Check whether the IP is usable.
        """
        if not ip:
            return False

        if ip.startswith("127."):
            return False

        if ip.startswith("169.254."):
            return False

        return True

    # ==========================================================
    # WINDOWS
    # ==========================================================

    @classmethod
    def _get_windows_ip(cls):
        """
        Windows IP selection priority:
        1. Physical Ethernet
        2. Physical Wi-Fi

        Excludes:
        - WSL vEthernet
        - Hyper-V virtual adapters
        - VirtualBox
        - VMware
        - VPN/tunnel adapters
        - Loopback
        - APIPA
        """

        command = """
        $result = @()

        $adapters = Get-NetAdapter | Where-Object {
            $_.Status -eq 'Up' -and
            $_.Virtual -eq $false -and
            $_.Name -notmatch 'vEthernet' -and
            $_.Name -notmatch 'WSL' -and
            $_.Name -notmatch 'Hyper-V' -and
            $_.Name -notmatch 'VirtualBox' -and
            $_.Name -notmatch 'VMware' -and
            $_.Name -notmatch 'VPN' -and
            $_.Name -notmatch 'TAP' -and
            $_.Name -notmatch 'TUN'
        }

        foreach ($adapter in $adapters) {

            $ip = Get-NetIPAddress `
                -InterfaceIndex $adapter.ifIndex `
                -AddressFamily IPv4 `
                -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.IPAddress -notlike '127.*' -and
                    $_.IPAddress -notlike '169.254.*'
                } |
                Select-Object -First 1

            if ($ip) {

                $result += [PSCustomObject]@{
                    Name = $adapter.Name
                    MediaType = $adapter.MediaType
                    IP = $ip.IPAddress
                }
            }
        }

        $result | ConvertTo-Json
        """

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    command
                ],
                capture_output=True,
                text=True,
                check=True
            )

            output = result.stdout.strip()

            if not output:
                return None

            adapters = json.loads(output)

            # PowerShell returns a dict when only one adapter exists
            if isinstance(adapters, dict):
                adapters = [adapters]

            # ----------------------------------
            # Priority 1: Physical Ethernet
            # ----------------------------------
            for adapter in adapters:
                if (
                    adapter.get("MediaType") == "802.3"
                    and cls._is_valid_ip(adapter.get("IP"))
                ):
                    return adapter["IP"]

            # ----------------------------------
            # Priority 2: Physical Wi-Fi
            # ----------------------------------
            for adapter in adapters:
                if (
                    adapter.get("MediaType") == "Native 802.11"
                    and cls._is_valid_ip(adapter.get("IP"))
                ):
                    return adapter["IP"]

        except Exception as e:
            print("Windows IP detection error:", e)

        return None


    # ==========================================================
    # LINUX
    # ==========================================================

    @classmethod
    def _get_linux_ip(cls, keywords):

        for interface in netifaces.interfaces():

            interface_name = interface.lower()

            # Check interface type
            if not any(
                keyword in interface_name
                for keyword in keywords
            ):
                continue

            try:
                addresses = netifaces.ifaddresses(interface)

                for address in addresses.get(
                    netifaces.AF_INET,
                    []
                ):

                    ip = address.get("addr")

                    if cls._is_valid_ip(ip):
                        return ip

            except (ValueError, KeyError):
                continue

        return None


    # ==========================================================
    # MAIN FUNCTION
    # ==========================================================

    @classmethod
    def get_ip(cls):

        system = platform.system()

        # ---------------------------
        # WINDOWS
        # ---------------------------
        if system == "Windows":

            ip = cls._get_windows_ip()

            if ip:
                return ip

        # ---------------------------
        # LINUX
        # ---------------------------
        elif system == "Linux":

            # Priority 1: Ethernet
            ip = cls._get_linux_ip(
                (
                    "eth",
                    "enp",
                    "eno",
                    "ens",
                    "enx",
                )
            )

            if ip:
                return ip

            # Priority 2: Wi-Fi
            ip = cls._get_linux_ip(
                (
                    "wlan",
                    "wlp",
                )
            )

            if ip:
                return ip

        # ---------------------------
        # FALLBACK
        # ---------------------------
        return "127.0.0.1"


if __name__ == "__main__":

    ip = NetworkIP.get_ip()

    print("Selected IP:", ip)
