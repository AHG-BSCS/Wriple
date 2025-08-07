"""Network Communication Module"""

import socket
import subprocess
import threading
import time
from scapy.all import Raw, IP, UDP, send
from config.settings import NetworkConfiguration
from utils.logger import setup_logger


class NetworkManager:
    """
    Manages network communication with ESP32
    Handles UDP packet transmission, reception, and connection management
    """
    
    def __init__(self):
        # Receiver related variables
        self._is_listening = False
        self._socket = None
        self._packet_count = 0

        # Transmitter related variables
        self._is_transmitting = False
        self._tx_timestamps = []
        self._tx_capture_interval = NetworkConfiguration.TX_CAPTURE_INTERVAL
        self._record_packet_limit = NetworkConfiguration.RECORD_PACKET_LIMIT
        self._tx_buffer_size = NetworkConfiguration.RX_BUFFER_SIZE
        self._udp_packet = IP(dst=NetworkConfiguration.TX_ESP32_IP) / \
                         UDP(sport=NetworkConfiguration.TX_UDP_PORT, 
                             dport=NetworkConfiguration.TX_UDP_PORT) / \
                         Raw(load=NetworkConfiguration.TX_PAYLOAD)
        
        self._ap_ssid = NetworkConfiguration.AP_SSID
        self._logger = setup_logger('NetworkManager')

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
            if self._ap_ssid in result.stdout:
                return True
            
            self._logger.warning(f'Not connected to AP: {self._ap_ssid}')
            return False
        except Exception as e:
            self._logger.error(f'Error checking AP connection: {e}')
            return False
    
    # Receiver

    def setup_socket(self) -> bool:
        """
        Setup UDP socket for receiving packets

        Returns:
            bool: True if socket setup is successful, False otherwise
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(('0.0.0.0', NetworkConfiguration.TX_UDP_PORT))
            self._socket.settimeout(NetworkConfiguration.RX_SOCKET_TIMEOUT)
            return True
        except Exception as e:
            self._logger.error(f'Error setting up socket: {e}')
            return False
    
    def start_listening(self, parse_received_data, is_recording):
        """
        Start listening for UDP packets from ESP32
        
        Args:
            parse_received_data: Function to call when data is received
            is_recording: Current mode
        """
        if not self.setup_socket():
            return
        
        self._is_listening = True
        self._logger.info('Listening for packets...')
        
        while self._is_listening:
            try:
                data, addr = self._socket.recvfrom(self._tx_buffer_size)
                # Monitor Packet Count for automatic stopping during recording
                self._packet_count += 1
                
                # Process data in separate thread
                threading.Thread(
                    target=parse_received_data, 
                    args=(data, 
                    self._tx_timestamps.pop(0)), 
                    daemon=True
                ).start()
                
                if is_recording and self._packet_count >= self._record_packet_limit:
                    self._logger.info(f'Recording completed with {self._packet_count} packets')
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
        self._packet_count = 0
        if self._socket:
            self._socket.close()
            self._socket = None
        self._logger.info('Stopped listening for packets.')
    
    # Transmitter

    def send_single_packet(self):
        """Send a single UDP packet"""
        try:
            send(self._udp_packet, verbose=False)
            tx_time = time.time()
            tx_time = int(tx_time * 1_000_000) % 1_000_000_000
            self._tx_timestamps.append(tx_time)
        except Exception as e:
            self._logger.error(f'Error sending packet: {e}')
    
    def request_captured_data(self):
        """Start continuous packet transmission at specified intervals"""
        self._is_transmitting = True
        
        def _transmit():
            if self._is_transmitting:
                self.send_single_packet()
                
                # Schedule next transmission
                threading.Timer(self._tx_capture_interval, _transmit).start()
        
        _transmit()
        self._logger.info('Started packet transmission')
    
    def stop_transmitting(self):
        """Stop continuous packet transmission"""
        self._is_transmitting = False
        self._requesting_csi = False
        self._logger.info('Stopped packet transmission')

    def stop_csi_request(self):
        self._requesting_csi = False
        self._logger.info('Stopped CSI request')

    @property
    def is_listening(self) -> bool:
        """
        Check if the manager is currently listening for packets
        Returns:
            bool: True if listening, False otherwise
        """
        return self._is_listening

    @property
    def packet_count(self) -> int:
        """
        Get the current packet count
        Returns:
            int: Number of packets received
        """
        return self._packet_count
