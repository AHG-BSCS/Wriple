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


class NetworkManager:
    """Manages network communication with ESP32"""
    
    def __init__(self):
        self.config = NetworkConfiguration()
        self.socket = None
        self.is_listening = False
        self.is_transmitting = False
        
        # Create UDP packet for transmission
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
            
            return False
        except Exception as e:
            print(f"Error checking AP connection: {e}")
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
            print(f"Error setting up socket: {e}")
            return False
    
    def start_listening(self, parse_received_data, record_packet_limit=None):
        """
        Start listening for UDP packets
        
        Args:
            parse_received_data: Function to call when data is received
            record_packet_limit: Maximum number of packets to receive (None for unlimited)
        """
        if not self.setup_socket():
            return False
        
        self.is_listening = True
        packet_count = 0
        
        print("Started listening for packets...")
        
        while self.is_listening:
            try:
                data, addr = self.socket.recvfrom(self.config.RX_BUFFER_SIZE)
                packet_count += 1
                
                # Process data in separate thread
                threading.Thread(target=parse_received_data, args=(data,), daemon=True).start()
                
                if record_packet_limit and packet_count >= record_packet_limit:
                    print('Recording completed')
                    break
                    
            # Implement a timeout to avoid continuous listening
            except socket.timeout:
                if not self.is_listening:
                    break
                continue
            except Exception as e:
                print(f"Error receiving packet: {e}")
                continue
        
        self.stop_listening()
        print("Stopped listening for packets.")
        return packet_count
    
    def stop_listening(self):
        """Stop listening for packets"""
        self.is_listening = False
        if self.socket:
            self.socket.close()
            self.socket = None
    
    # Transmitter

    def send_single_packet(self):
        """
        Send a single UDP packet
        
        Returns:
            int or None: Timestamp, None otherwise
        """
        try:
            send(self.udp_packet, verbose=False)
            
            tx_time = time.time()
            return int((tx_time * 1_000_000) % 1_000_000_000)
            
        except Exception as e:
            print(f"Error sending packet: {e}")
            return None
    
    def start_transmitting(self):
        """
        Start continuous packet transmission
        
        Returns:
            list: Timestamps, empty list otherwise
        """
        self.is_transmitting = True
        tx_timestamps = []
        print('Started transmitting packets...')
        
        def _transmit():
            if self.is_transmitting:
                timestamp = self.send_single_packet()
                tx_timestamps.append(timestamp)
                
                # Schedule next transmission
                threading.Timer(self.config.TX_INTERVAL, _transmit).start()
        
        _transmit()
        return tx_timestamps
    
    def stop_transmitting(self):
        """Stop continuous packet transmission"""
        self.is_transmitting = False
        print("Stopped transmitting packets.")
