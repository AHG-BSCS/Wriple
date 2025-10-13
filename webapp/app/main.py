import threading
from flask import Flask
import numpy as np
import time

from app.config.settings import RecordingConfiguration, PredictionConfiguration
from app.core.csi_processor import CSIProcessor
from app.core.file_manager import FileManager
from app.core.model_manager import ModelManager
from app.core.network_manager import NetworkManager
from app.utils.packet_parser import PacketParser
from app.api.routes import create_api_routes
from app.utils.logger import setup_logger


class HumanDetectionSystem:
    """Main class that coordinates all components"""
    
    def __init__(self):
        # Initialize core components
        self.file_manager = FileManager()
        self.file_manager.load_settings()
        self.csi_processor = CSIProcessor()
        self.model_manager = ModelManager()
        self.network_manager = NetworkManager(self.file_manager)
        
        # Application state and counter
        self.is_recording = False
        self.is_monitoring = False
        self._is_ld2420_active = False
        self._is_esp32_active = False

        # Initialize parameters and data storage
        self.rssi = []
        self.rdm_data = []
        self.prev_inference = 0
        self.csi_queue_limit = RecordingConfiguration.MONITOR_QUEUE_LIMIT
        self.rdm_queue_limit = RecordingConfiguration.MMWAVE_QUEUE_LIMIT
        self.pred_signal_window = PredictionConfiguration.PRED_SIGNAL_WINDOW
        self.record_parameters = RecordingConfiguration.RECORD_PARAMETERS
        self.logger = setup_logger('HumanDetectionSystem')
    
    def record_data_packet(self, parsed_data, tx_timestamp):
        """
        Record data packet to CSV file

        Args:
            parsed_data: Parsed data from ESP32
            tx_timestamp: Timestamp of the transmitted packet
        """

        # row = [tx_timestamp] + self.record_parameters + parsed_data
        row = self.record_parameters + [tx_timestamp] + parsed_data
        self.file_manager.write_data(row)

    def parse_received_data(self, raw_data: bytes, tx_timestamp: int):
        """
        Process data received from ESP32
        
        Args:
            raw_data: Raw data bytes received from ESP32 including the data from other sensors
            tx_timestamp: Timestamp of the transmitted packet
        """
        # Extract radar and CSI data from parsed data
        parsed_data = PacketParser.parse_csi_data(raw_data)

        if self.is_monitoring:
            self.csi_processor.queue_csi(parsed_data[6])

            # Remove oldest rdm data if it exceeds the limits
            while len(self.rdm_data) > self.rdm_queue_limit:
                self.rdm_data.pop(0)

            if parsed_data[0]: # If ld24020 data is valid
                self.rdm_data.append(parsed_data[7:])

            while len(self.rssi) > self.csi_queue_limit:
                self.rssi.pop(0)
            self.rssi.append(parsed_data[2])
        
        # Record data to csv file if recording
        if self.is_recording:
            self.record_data_packet(parsed_data[1:], tx_timestamp)
    
    def start_capturing(self, is_recording: bool):
        """Start recording Wi-Fi CSI data into CSV file"""
        if not self.network_manager.check_wifi_connection():
            self.logger.error('Not connected to AP. Cannot capture packet')
            return
        
        if is_recording: self.is_recording = True
        else: self.is_monitoring = True

        threading.Thread(
            target=self.network_manager.start_receiving,
            args=(self.parse_received_data, self.is_recording),
            daemon=True
        ).start()
        self.network_manager.start_csi_transmission()
    
    def stop_operations(self):
        """Stop all recording/monitoring operations"""
        self.is_recording = False
        self.is_monitoring = False

        self.network_manager.stop_transmitting()
        self.network_manager.stop_listening()
        self.csi_processor.clear_queues()
        self.file_manager.close()
    
    def predict_presence(self) -> int:
        """
        Make presence prediction using ML model
        
        Returns:
            int: Presence prediction (1 for presence, 0 for absence)
        """
        if len(self.rssi) > self.pred_signal_window and self.model_manager.model_loaded:
            rssi_window = self.rssi[-120:]
            rssi_std = np.std(rssi_window)
            rssi_mean = np.mean(rssi_window)
            amps_window = self.csi_processor.get_amplitude_window()

            X = [float(rssi_mean), float(rssi_std)] + amps_window
            return self.model_manager.predict(X)
        else:
            return 'No'
    
    def get_system_status(self) -> dict:
        """
        Get current system components status
        
        Returns:
            dict: Dictionary with status of each system component
        """
        ap_status = self.network_manager.check_wifi_connection()
        if ap_status:
            if self.network_manager.check_esp32():
                self._is_esp32_active = True
                self._is_ld2420_active = PacketParser.is_ld2420_active()
            else:
                self._is_esp32_active = False
                self._is_ld2420_active = False

        return {
            'ap': ap_status,
            'esp32': self._is_esp32_active,
            'ld2420': self._is_ld2420_active,
            'model': self.model_manager.model_loaded
        }
    
    def get_monitor_status(self) -> dict:
        mode_status = (0 if self.is_recording and self.network_manager.is_receiving else 
                       1 if self.is_monitoring else -1)
        
        return {
            'modeStatus': mode_status,
            'packetCount': self.network_manager.packet_count,
            'packetLoss': self.network_manager.get_packet_loss(),
            'rssi': self.rssi[-1] if len(self.rssi) > 2 else 0,
            'exp': self.csi_processor.highest_diff
        }
    
    def get_presence_status(self) -> dict:
        return {
            'presence': self.predict_presence(),
            'targetDistance': 0, # Placeholder for target distance
        }
    
    def get_radar_status(self) -> dict:
        """
        Get radar data and predictions
        
        Returns:
            dict: Dictionary with radar data and presence prediction
        """
        mode_status = (0 if self.is_recording and self.network_manager.is_receiving else 
                       1 if self.is_monitoring else -1)
        
        return {
            'modeStatus': mode_status,
            'angle': 0,
            'distance': 0,
            'energy': 0
        }
    
    def set_recording_parameters(self, params: dict):
        """
        Set parameters for recording
        
        Args:
            params: Dictionary with recording parameters:
        """
        self.record_parameters = [
            int(params['class']),
            int(params['target_count']),
            int(params['state']),
            int(params['activity']),
            int(params['angle']),
            int(params['distance']),
            int(params['obstructed']),
            int(params['obstruction']),
            int(params['setup_spacing']),
        ]


def create_app():
    """Factory function to create Flask app"""
    app = Flask(__name__)
    # Initialize the detection system
    detection_system = HumanDetectionSystem()
    create_api_routes(app, detection_system)
    return app
