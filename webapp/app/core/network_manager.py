"""Network Communication Module"""

import socket
import subprocess
import threading
import time
from config.settings import NetworkConfig
from utils.logger import setup_logger


class NetworkManager:
    """
    Manages network communication with ESP32
    Handles UDP packet transmission, reception, and connection management
    """
    
    def __init__(self, file_manager):
        from core.file_manager import FileManager
        self.file_manager: FileManager = file_manager
        
        self._is_listening = False
        self._port_established = False
        self._wifi_connected = False
        self._rx_socket = None
        self._tx_socket = None
        self._packet_transmit_count = 0
        self._packet_received_count = 0

        # Transmitter related variables
        self._is_transmitting = False
        self._tx_timestamps = []

        self._logger = setup_logger('NetworkManager')
        self.setup_tx_socket()

    def check_wifi_connection(self) -> bool:
        """
        Check if connected to the ESP32 AP
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'], 
                capture_output=True, text=True
            )
            if NetworkConfig.AP_SSID in result.stdout:
                self._wifi_connected = True
                return True
            
            self._logger.warning(f'Not connected to AP: {NetworkConfig.AP_SSID}')
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
                result = subprocess.run(
                    ['ping', '-n', '1', NetworkConfig.TX_ESP32_IP],
                    capture_output=True, text=True
                )

                esp32_status = 'TTL=' in result.stdout
                # Set to None to reset with ESP32 on reboot
                if not esp32_status:
                    NetworkConfig.TX_ESP32_IP = None
                    self._logger.info('ESP32 IP is unreachable')
                return esp32_status
            else:
                self.transmit_start_request_packet()
                threading.Thread(target=self.transmit_esp32_ip_request_packet, daemon=True).start()
                data, addr = self._tx_socket.recvfrom(2)
                NetworkConfig.TX_ESP32_IP = addr[0]
                self._port_established = True
                self.file_manager.save_settings()
                return True
                
        except Exception as e:
            self._logger.error(f'ESP32 is unreachable: {e}')
            return False
    
    # Receiver

    def setup_rx_socket(self) -> bool:
        """
        Setup UDP socket for receiving packets

        Returns:
            bool: True if socket setup is successful, False otherwise
        """
        try:
            self._rx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._rx_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._rx_socket.bind(('0.0.0.0', NetworkConfig.TX_PORT))
            self._rx_socket.settimeout(NetworkConfig.RX_SOCKET_TIMEOUT)
            return True
        except Exception as e:
            self._logger.error(f'Error setting up socket: {e}')
            return False
    
    def setup_tx_socket(self) -> bool:
        """
        Setup UDP socket for transmitting packets

        Returns:
            bool: True if socket setup is successful, False otherwise
        """
        try:
            self._tx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._tx_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._tx_socket.settimeout(NetworkConfig.TX_SOCKET_TIMEOUT)
            return True
        except Exception as e:
            self._logger.error(f'Error setting up transmitter socket: {e}')
            return False
    
    def start_listening(self, parse_received_data, is_recording):
        """
        Start listening for UDP packets from ESP32
        
        Args:
            parse_received_data: Function to call when data is received
            is_recording: Current mode
        """
        if not self.setup_rx_socket():
            return
        
        self._is_listening = True
        self._logger.info('Listening for packets...')
        
        while self._is_listening:
            try:
                data, addr = self._tx_socket.recvfrom(NetworkConfig.RX_BUFFER_SIZE)
                # data, addr = self._rx_socket.recvfrom(NetworkConfig.RX_BUFFER_SIZE)
                # Monitor Packet Count for automatic stopping during recording
                self._packet_received_count += 1
                
                # Process data in separate thread
                threading.Thread(
                    target=parse_received_data, 
                    args=(data, self._tx_timestamps.pop(0)), 
                    daemon=True
                ).start()
                
                if is_recording and self._packet_received_count >= NetworkConfig.RECORD_PACKET_LIMIT:
                    self._logger.info(f'Recording completed with {self._packet_received_count} packets')
                    break
            
            # Implement a timeout to avoid continuous listening
            except socket.timeout:
                if not self._is_listening:
                    break
                continue
            except Exception as e:
                self._logger.error(f'Error receiving packet: {e}')
                continue
        
        self.stop_listening()
        self.stop_transmitting()
    
    def stop_listening(self):
        """Stop listening for packets"""
        self._is_listening = False
        self._packet_received_count = 0
        if self._rx_socket:
            self._rx_socket.close()
            self._rx_socket = None
        self._logger.info('Stopped listening for packets.')
    
    # Transmitter

    def transmit_csi_request_packet(self):
        """Send a single UDP packet to generate CSI data"""
        try:
            self._tx_socket.sendto(NetworkConfig.TX_CSI_REQ_PAYLOAD,
                                   (NetworkConfig.TX_ESP32_IP, NetworkConfig.TX_PORT))
            tx_time = time.time()
            tx_time = int(tx_time * 1_000_000) % 1_000_000_000
            self._tx_timestamps.append(tx_time)
            self._packet_transmit_count += 1
        except Exception as e:
            self._logger.error(f'Error sending request packet: {e}')
    
    def transmit_stop_request_packet(self):
        """Send a single UDP packet to signal ESP32 to stop CSI request"""
        try:
            self._tx_socket.sendto(NetworkConfig.TX_STOP_REQ_PAYLOAD,
                                   (NetworkConfig.TX_ESP32_IP, NetworkConfig.TX_PORT))
        except Exception as e:
            self._logger.error(f'Error sending stop packet: {e}')
    
    def transmit_start_request_packet(self):
        """Send a single UDP packet to signal ESP32 to start CSI request"""
        try:
            self._tx_socket.sendto(NetworkConfig.TX_START_REQ_PAYLOAD,
                                   (NetworkConfig.TX_ESP32_IP, NetworkConfig.TX_PORT))
        except Exception as e:
            self._logger.error(f'Error sending start packet: {e}')
    
    def transmit_esp32_ip_request_packet(self):
        """Send a single UDP packet to request ESP32 IP address"""
        tx_counter = 0
        while tx_counter < 5:
            try:
                self._tx_socket.sendto(NetworkConfig.TX_IP_REQ_PAYLOAD,
                                       (NetworkConfig.AP_BROADCAST_IP, NetworkConfig.TX_PORT))
                tx_counter += 1
                time.sleep(NetworkConfig.TX_CONNECT_INTERVAL)
            except Exception as e:
                self._logger.error(f'Error sending IP request packet: {e}')
    
    def request_captured_data(self):
        """Start continuous packet transmission at specified intervals"""
        self._is_transmitting = True
        
        def _transmit():
            if self._is_transmitting:
                self.transmit_csi_request_packet()
                # Schedule transmission using threading to avoid blocking
                threading.Timer(NetworkConfig.TX_CAPTURE_INTERVAL, _transmit).start()
        
        _transmit()
        self._logger.info('Started packet transmission')
    
    def stop_transmitting(self):
        """Stop continuous packet transmission"""
        if self._packet_transmit_count > 0:
            self._is_transmitting = False
            self._requesting_csi = False
            self._packet_transmit_count = 0
            self.transmit_stop_request_packet()
            self._logger.info('Stopped packet transmission')

    def get_packet_loss_rate(self) -> int:
        """
        Calculate packet loss rate based on transmitted and received packets
        
        Returns:
            float: Packet loss rate as a percentage (rounded to two decimal places)
        """
        if self._packet_transmit_count == 0:
            return 0.0
        
        loss = (self._packet_transmit_count - self._packet_received_count) / self._packet_transmit_count
        return int(loss * 100)

    @property
    def is_listening(self) -> bool:
        """
        Check if the manager is currently listening for packets
        Returns:
            bool: True if listening, False otherwise
        """
        return self._is_listening

    @property
    def packet_received_count(self) -> int:
        """
        Get the current packet count
        Returns:
            int: Number of packets received
        """
        return self._packet_received_count
