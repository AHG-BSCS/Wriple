import threading

import numpy as np
from flask import Flask

from app.api.routes import create_api_routes
from app.config.settings import RecordConfig, ModelConfig
from app.core.csi_processor import CSIProcessor
from app.core.file_manager import FileManager
from app.core.model_manager import ModelManager
from app.core.network_manager import NetworkManager
from app.core.rdm_processor import RDMProcessor
from app.utils.packet_parser import parse_csi_data


class HumanDetectionSystem:
    """Main class that coordinates all components"""
    
    def __init__(self):
        # Initialize core components
        self.file_manager = FileManager()
        self.file_manager.load_settings()
        self.csi_processor = CSIProcessor()
        self.rdm_processor = RDMProcessor()
        self.model_manager = ModelManager()
        self.network_manager = NetworkManager(self.file_manager)
        
        # Application state and counter
        self._recording = False
        self._monitoring = False
        self._ld2420_status = False
        self._ld2420_miss_count = -1
        self._esp32_status = False

        # Initialize parameters and data storage
        self._rssi = []
        self._csi_queue_limit = RecordConfig.CSI_QUEUE_LIMIT
        self._pred_signal_window = ModelConfig.PRED_SIGNAL_WINDOW
        self._record_parameters = RecordConfig.RECORD_PARAMETERS

    def record_data_packet(self, parsed_data, tx_timestamp):
        """
        Record data packet to CSV file

        Args:
            parsed_data: Parsed data from ESP32
            tx_timestamp: Timestamp of the transmitted packet
        """

        # row = [tx_timestamp] + self.record_parameters + parsed_data
        row = self._record_parameters + [tx_timestamp] + parsed_data
        self.file_manager.write_data(row)

    def parse_received_data(self, raw_data: bytes, tx_timestamp: int):
        """
        Process data received from ESP32
        
        Args:
            raw_data: Raw data bytes received from ESP32 including the data from other sensors
            tx_timestamp: Timestamp of the transmitted packet
        """
        # Extract radar and CSI data from parsed data
        parsed_data = parse_csi_data(raw_data, self._ld2420_miss_count)

        if parsed_data is None:
            return
        
        self._ld2420_miss_count = parsed_data[1]

        if self._monitoring:
            self.csi_processor.queue_csi(parsed_data[7])

            if parsed_data[0]: # If ld24020 data is valid
                self.rdm_processor.queue_rdm(parsed_data[8:])

            self._rssi.append(parsed_data[3])
            while len(self._rssi) > self._csi_queue_limit:
                self._rssi.pop(0)
        
        # Record data to csv file if recording
        if self._recording:
            self.record_data_packet(parsed_data[2:], tx_timestamp)
    
    def start_capturing(self, is_recording: bool):
        """Start recording Wi-Fi CSI data into CSV file"""
        if not self.network_manager.check_wifi_connection():
            return
        
        if is_recording: self._recording = True
        else: self._monitoring = True

        threading.Thread(
            target=self.network_manager.start_receiving,
            args=(self.parse_received_data, self._recording),
            daemon=True
        ).start()
        self.network_manager._start_csi_transmission()
    
    def stop_operations(self):
        """Stop all recording/monitoring operations"""
        self._recording = False
        self._monitoring = False

        self.network_manager.stop_transmitting()
        self.network_manager.stop_listening()
        self.csi_processor.clear_queues()
        self.file_manager.close()
        self._rssi = []
    
    def predict_presence(self) -> int:
        """
        Make presence prediction using ML model
        
        Returns:
            int: Presence prediction (1 for presence, 0 for absence)
        """
        if len(self._rssi) > self._pred_signal_window and self.model_manager.model_loaded:
            rssi_window = self._rssi[-120:]
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
                self._esp32_status = True
                self._ld2420_status = self._ld2420_miss_count < 30
            else:
                self._esp32_status = False
                self._ld2420_status = False

        return {
            'ap': ap_status,
            'esp32': self._esp32_status,
            'ld2420': self._ld2420_status,
            'model': self.model_manager.model_loaded,
            'rssi': self._rssi[-1] if self._rssi else 0
        }
    
    def get_monitor_status(self) -> dict:
        mode_status = (0 if self._recording and self.network_manager.is_receiving else 
                       1 if self._monitoring else -1)
        return {
            'modeStatus': mode_status,
            'packetCount': self.network_manager.packet_count,
            'rssi': self._rssi[-1] if self._rssi else 0
        }
    
    def get_presence_status(self) -> dict:
        if self._rssi:
            return {
                'presence': self.predict_presence(),
                'packetLoss': self.network_manager.packet_loss,
                'ampVariance': self.csi_processor.amplitude_variance
            }
        else:
            return {
                'presence': '?',
                'packetLoss': self.network_manager.packet_loss,
                'ampVariance': 0.0
            }
    
    def get_radar_status(self) -> dict:
        """
        Get radar data and predictions
        
        Returns:
            dict: Dictionary with radar data and presence prediction
        """
        return {
            'distance': self.rdm_processor.estimate_distance(),
        }
    
    def set_recording_parameters(self, params: dict):
        """
        Set parameters for recording
        
        Args:
            params: Dictionary with recording parameters:
        """
        self._record_parameters = [
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
