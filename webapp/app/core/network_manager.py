"""Network Communication Module"""

import socket
import subprocess
import threading
import time

from app.config.settings import NetworkConfig
from app.utils.logger import setup_logger


class NetworkManager:
    """
    Manages network communication with ESP32
    Handles UDP packet transmission, reception, and connection management
    """
    
    def __init__(self, file_manager):
        from app.core.file_manager import FileManager
        self.file_manager: FileManager = file_manager
        
        self._receiving = False
        self._transmitting = False
        self._port_established = False
        self._wifi_connected = False

        self._socket = None
        self._rx_packet_count = 0
        self._tx_packet_count = 0
        self._tx_timestamps = []

        self._logger = setup_logger('NetworkManager')
        self.init_socket()
    
    def find_ip_address(self) -> str:
        """
        Find the current IP address of the machine

        Returns:
            str: Current IP address or None if not found
        """
        try:
            ip_addr = socket.gethostbyname(socket.gethostname())
            # Fallback to ipconfig parsing if localhost is returned
            if ip_addr.startswith("127."):
                output = subprocess.run(['ipconfig'], capture_output=True, text=True)
                for line in output.stdout.splitlines():
                    if 'IPv4 Address' in line:
                        import re
                        m = re.search(r'IPv4 Address[^\:]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', line)
                        if m: return m.group(1)
                        else: return None
            else:
                return ip_addr
        except Exception:
            return None
        return None
    
    def update_broadcast_ip(self):
        """Update the broadcast IP based on current IP address"""
        NetworkConfig.SERVER_IP_ADDR = self.find_ip_address()
        
        if not NetworkConfig.SERVER_IP_ADDR:
            self._logger.error('Could not determine current IP address')
            NetworkConfig.AP_BROADCAST_IP = None
            return
        
        NetworkConfig.AP_BROADCAST_IP = NetworkConfig.SERVER_IP_ADDR[
                        :NetworkConfig.SERVER_IP_ADDR.rfind('.')] + '.255'
        
        self._logger.info(f'AP Broadcast IP: {NetworkConfig.AP_BROADCAST_IP}')

    def check_wifi_connection(self) -> bool:
        """
        Check if connected to the ESP32 AP
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            output = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'], 
                capture_output=True, text=True
            )
            if NetworkConfig.AP_SSID in output.stdout:
                self._wifi_connected = True
                
                if not NetworkConfig.AP_BROADCAST_IP:
                    self.update_broadcast_ip()
                return True
            
            self._wifi_connected = False
            return False
        except Exception as e:
            self._logger.error(f'Error checking AP connection: {e}')
            return False

    def check_esp32(self) -> bool:
        """
        Check if ESP32 is reachable by pinging its IP address
        
        Returns:
            bool: True if ESP32 is reachable, False otherwise
        """
        try:
            if self._wifi_connected and NetworkConfig.TX_ESP32_IP and self._port_established:
                output = subprocess.run(
                    ['ping', '-n', '1', NetworkConfig.TX_ESP32_IP],
                    capture_output=True, text=True
                )
                esp32_status = 'TTL=' in output.stdout
                # Set to None to reset with ESP32 on reboot
                if not esp32_status:
                    NetworkConfig.TX_ESP32_IP = None
                    self._logger.info('ESP32 IP is unreachable')
                return esp32_status
            else:
                if NetworkConfig.TX_ESP32_IP:
                    self.transmit_reconnection_packet()
                
                threading.Thread(target=self.transmit_ip_broadcast_packet, daemon=True).start()
                data, addr = self._socket.recvfrom(2)

                if addr[0] != NetworkConfig.TX_ESP32_IP:
                    NetworkConfig.TX_ESP32_IP = addr[0]
                    self._logger.info(f'New ESP32 IP: {NetworkConfig.TX_ESP32_IP}')
                    self.file_manager.save_settings()
                self._port_established = True
                return True
                
        except Exception as e:
            self._logger.error(f'ESP32 is unreachable: {e}')
            return False
    
    # Receiver

    def init_socket(self) -> bool:
        """
        Setup UDP socket for transmitting packets

        Returns:
            bool: True if socket setup is successful, False otherwise
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.settimeout(NetworkConfig.TX_SOCKET_TIMEOUT)
            return True
        except Exception as e:
            self._logger.error(f'Error setting up transmitter socket: {e}')
            return False
    
    def start_receiving(self, parse_received_data, is_recording):
        """
        Start listening for UDP packets from ESP32
        
        Args:
            parse_received_data: Function to call when data is received
            is_recording: Current mode
        """
        self._receiving = True
        self._logger.info('Listening...')
        
        while self._receiving:
            try:
                data, addr = self._socket.recvfrom(NetworkConfig.RX_BUFFER_SIZE)
                # data, addr = self._rx_socket.recvfrom(NetworkConfig.RX_BUFFER_SIZE)
                # Monitor Packet Count for automatic stopping during recording
                self._rx_packet_count += 1
                
                # Process data in separate thread
                threading.Thread(
                    target=parse_received_data, 
                    args=(data, self._tx_timestamps.pop(0)), 
                    daemon=True
                ).start()
                
                if is_recording and self._rx_packet_count >= NetworkConfig.RECORD_PACKET_LIMIT:
                    self._logger.info(f'Recording completed with {self._rx_packet_count} packets')
                    break
            
            # Implement a timeout to avoid continuous listening
            except socket.timeout:
                if not self._receiving:
                    break
                continue
            except Exception as e:
                self._logger.error(f'Error receiving packet: {e}')
                continue
        
        self.stop_listening()
        self.stop_transmitting()
    
    def stop_listening(self):
        """Stop listening for packets"""
        self._receiving = False
        self._logger.info(f'Receiving stopped at {self._rx_packet_count} packets')
        self._rx_packet_count = 0
    
    # Transmitter

    def transmit_csi_generating_packet(self):
        """Send a UDP packet to generate CSI data"""
        # Removed the error handling to reduce overhead
        while self._transmitting:
            self._socket.sendto(NetworkConfig.TX_CSI_REQ_PAYLOAD,
                                (NetworkConfig.TX_ESP32_IP, NetworkConfig.TX_PORT))
            self._tx_timestamps.append(time.time())
            self._tx_packet_count += 1
            time.sleep(NetworkConfig.TX_INTERVAL)
    
    def transmit_stop_csi_packet(self):
        """Send a single UDP packet to signal ESP32 to stop CSI request"""
        try:
            self._socket.sendto(NetworkConfig.TX_STOP_REQ_PAYLOAD,
                                   (NetworkConfig.TX_ESP32_IP, NetworkConfig.TX_PORT))
        except Exception as e:
            self._logger.error(f'Error sending stop packet: {e}')
    
    def transmit_reconnection_packet(self):
        """Send a single UDP packet to signal ESP32 to start CSI request"""
        try:
            self._socket.sendto(NetworkConfig.TX_RECONNECT_PAYLOAD,
                                   (NetworkConfig.TX_ESP32_IP, NetworkConfig.TX_PORT))
        except Exception as e:
            self._logger.error(f'Error sending start packet: {e}')
    
    def transmit_ip_broadcast_packet(self):
        """Send a single UDP packet to request ESP32 IP address"""
        tx_counter = 0
        while tx_counter < 5:
            try:
                self._socket.sendto(NetworkConfig.TX_IP_BROADCAST_PAYLOAD,
                                       (NetworkConfig.AP_BROADCAST_IP, NetworkConfig.TX_PORT))
                tx_counter += 1
                time.sleep(NetworkConfig.TX_CONNECT_INTERVAL)
            except Exception as e:
                self._logger.error(f'Error sending IP request packet: {e}')
    
    def start_csi_transmission(self):
        """Start continuous packet transmission at specified intervals"""
        self._transmitting = True
        threading.Thread(target=self.transmit_csi_generating_packet, daemon=True).start()
        self._logger.info('Transmitting...')
    
    def stop_transmitting(self):
        """Stop continuous packet transmission"""
        if self._tx_packet_count > 0:
            self._transmitting = False
            self._tx_packet_count = 0
            self._tx_timestamps.clear()
            self._logger.info('Transmission stopped')
            self.transmit_stop_csi_packet()

    @property
    def packet_loss(self) -> int:
        """
        Calculate packet loss rate based on transmitted and received packets
        
        Returns:
            float: Packet loss rate as a percentage
        """
        if self._tx_packet_count == 0:
            return 0.0
        
        loss = (self._tx_packet_count - self._rx_packet_count) / self._tx_packet_count
        return int(loss * 100)

    @property
    def is_receiving(self) -> bool:
        return self._receiving

    @property
    def packet_count(self) -> int:
        return self._rx_packet_count
