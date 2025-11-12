"""System Command Utilities"""

import os
import subprocess
import shutil

@staticmethod
def _run_cmd(cmd):
    """Run a command and return the output"""
    try:
        if os.name == 'nt':
            return subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).stdout
        return subprocess.run(cmd, capture_output=True, text=True).stdout
    except Exception as e:
        return None

@staticmethod
def _ssid_connected_windows(ap_ssid):
    """Check if connected to the specified SSID on Windows"""
    # Example output: "SSID : MySSID"
    output = _run_cmd(["netsh", "wlan", "show", "interfaces"])
    return ap_ssid in output

@staticmethod
def _ssid_connected_macos(ap_ssid):
    """Check if connected to the specified SSID on macOS"""
    airport_paths = [
        shutil.which("airport"),
        "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    ]
    airport = next((p for p in airport_paths if p and os.path.exists(p)), None)
    if airport:
        # Example output: " SSID: MySSID"
        output = _run_cmd([airport, "-I"])
        return ap_ssid in output

    # Fallback: Common device is en0 but on some machines it can be en1
    for dev in ("en0", "en1"):
        if shutil.which("networksetup"):
            # Example output: "Current Wi-Fi Network: MySSID"
            output = _run_cmd(["networksetup", "-getairportnetwork", dev])
            if output:
                return ap_ssid in output

@staticmethod
def _ssid_connected_linux(ap_ssid):
    """Check if connected to the specified SSID on Linux"""
    if shutil.which("iwgetid"):
        # Example output: "MySSID"
        output = _run_cmd(["iwgetid", "-r"])
        return ap_ssid in output

    if shutil.which("nmcli"):
        # Example output: "yes:MySSID" or "no:"
        output = _run_cmd(["nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi"])
        return ap_ssid in output

@staticmethod
def check_ap_connection(ap_ssid, system):
    """
    Check if connected to the specified SSID based on the OS.

    Args:
        ap_ssid (str): SSID of the Access Point to check connection for
        system (str): Operating system name (e.g., 'Windows', 'Darwin', 'Linux')

    Returns:
        bool: True if connected to the specified SSID, False otherwise
    """
    if system == 'Windows':
        return _ssid_connected_windows(ap_ssid)
    if system == 'Darwin':
        return _ssid_connected_macos(ap_ssid)
    if system == 'Linux':
        return _ssid_connected_linux(ap_ssid)
    return False

@staticmethod
def get_local_ip():
    """Get the local IP address on macOS.
    
    Returns:
        str: Local IP address or None if not found
    """
    try:
        output = subprocess.check_output('ifconfig en0', shell=True).decode()
        for line in output.splitlines():
            if "inet " in line and "127.0.0.1" not in line:
                return line.split()[1]
    except:
        print(f'SYSTEM COMMAND: Command failed to execute.')
    return None

@staticmethod
def ping_esp32(esp32_ip, system):
    """
    Ping a host once.

    Args:
        esp32_ip (str): IP address of the ESP32 to ping
        system (str): Operating system name (e.g., 'Windows', 'Darwin', 'Linux')

    Returns:
        bool: True if the host is reachable, False otherwise
    """
    if system == 'Windows':
        output = _run_cmd(['ping', '-n', '1', esp32_ip])
        return 'TTL=' in output
    if system in ('Linux', 'Darwin'):
        if shutil.which('ping'):
            output = _run_cmd(['ping', '-c', '1', esp32_ip])
            return '1 received' in output or '1 packets received' in output
        return False
    return False
