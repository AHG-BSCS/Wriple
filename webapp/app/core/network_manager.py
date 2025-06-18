"""
Network Communication Module
Handles UDP packet transmission, reception, and connection management
"""

import socket
import subprocess
import threading
import time
from scapy.all import Raw, IP, UDP, send
from config.settings import NetworkConfiguration
from utils.logger import setup_logger


class NetworkManager:
    """Manages network communication with ESP32"""
    
    def __init__(self):
        self.config = NetworkConfiguration()
        self.socket = None
        self._tx_timestamps = []
        self._is_listening = False
        self.is_transmitting = False
        self._packet_count = 0
        self.logger = setup_logger('NetworkManager')

        self.udp_packet = IP(dst=self.config.TX_ESP32_IP) / \
                         UDP(sport=self.config.TX_UDP_PORT, 
                             dport=self.config.RX_ESP32_PORT) / \
                         Raw(load=self.config.TX_PAYLOAD)

    def check_wifi_connection(self):
        """Check if connected to the ESP32 AP"""
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'], 
                capture_output=True, text=True
            )
            if self.config.AP_SSID in result.stdout:
                return True
            
            self.logger.warning(f"Not connected to AP: {self.config.AP_SSID}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking AP connection: {e}")
            return False
    
    # Receiver

    def setup_socket(self):
        """Setup UDP socket for receiving packets"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.config.TX_UDP_PORT))
            self.socket.settimeout(self.config.RX_SOCKET_TIMEOUT)
            return True
        except Exception as e:
            self.logger.error(f"Error setting up socket: {e}")
            return False
    
    def start_listening(self, parse_received_data, record_packet_limit=None):
        """
        Start listening for UDP packets
        
        Args:
            parse_received_data: Function to call when data is received
            record_packet_limit: Maximum number of packets to receive (None for unlimited)
        """
        if not self.setup_socket():
            return
        
        self._is_listening = True
        self.logger.info("Listening for packets...")
        
        while self._is_listening:
            try:
                data, addr = self.socket.recvfrom(self.config.RX_BUFFER_SIZE)
                self._packet_count += 1
                
                # Process data in separate thread
                threading.Thread(
                    target=parse_received_data, 
                    args=(data, 
                    self._tx_timestamps.pop(0)), 
                    daemon=True
                ).start()
                
                if record_packet_limit and self._packet_count >= record_packet_limit:
                    self.logger.info(f'Recording completed with {self._packet_count} packets')
                    break
                    
            # Implement a timeout to avoid continuous listening
            except socket.timeout:
                if not self._is_listening:
                    break
                continue
            except Exception as e:
                self.logger.error(f"Error receiving packet: {e}")
                continue
        
        self.stop_listening()
    
    def stop_listening(self):
        """Stop listening for packets"""
        self._is_listening = False
        self._packet_count = 0
        if self.socket:
            self.socket.close()
            self.socket = None
        self.logger.info('Stopped listening for packets.')
    
    # Transmitter

    def send_single_packet(self):
        """Send a single UDP packet"""
        try:
            send(self.udp_packet, verbose=False)
            tx_time = time.time()
            tx_time = int(tx_time * 1_000_000) % 1_000_000_000
            self._tx_timestamps.append(tx_time)
        except Exception as e:
            self.logger.error(f"Error sending packet: {e}")
    
    def start_transmitting(self):
        """Start continuous packet transmission"""
        self.is_transmitting = True
        
        def _transmit():
            if self.is_transmitting:
                self.send_single_packet()
                
                # Schedule next transmission
                threading.Timer(self.config.TX_INTERVAL, _transmit).start()
        
        _transmit()
        self.logger.info("Started packet transmission")
    
    def stop_transmitting(self):
        """Stop continuous packet transmission"""
        self.is_transmitting = False
        self.logger.info("Stopped packet transmission")

    @property
    def is_listening(self) -> bool:
        """Check if the manager is currently listening for packets"""
        return self._is_listening

    @property
    def packet_count(self) -> int:
        """Get the current packet count"""
        return self._packet_count