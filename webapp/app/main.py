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
from app.utils.logger import setup_logger
from app.utils.packet_parser import PacketParser


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
        self.is_recording = False
        self.is_monitoring = False
        self._is_ld2420_active = False
        self._is_esp32_active = False

        # Initialize parameters and data storage
        self.rssi = []
        self.csi_queue_limit = RecordConfig.CSI_QUEUE_LIMIT
        self.rdm_queue_limit = RecordConfig.RDM_QUEUE_LIMIT
        self.pred_signal_window = ModelConfig.PRED_SIGNAL_WINDOW
        self.record_parameters = RecordConfig.RECORD_PARAMETERS
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

            if parsed_data[0]: # If ld24020 data is valid
                self.rdm_processor.queue_rdm(parsed_data[7:])

            self.rssi.append(parsed_data[2])
            while len(self.rssi) > self.csi_queue_limit:
                self.rssi.pop(0)
        
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
        self.network_manager._start_csi_transmission()
    
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
            'model': self.model_manager.model_loaded,
            'rssi': self.rssi[-1] if self.rssi else 0
        }
    
    def get_monitor_status(self) -> dict:
        mode_status = (0 if self.is_recording and self.network_manager.is_receiving else 
                       1 if self.is_monitoring else -1)
        return {
            'modeStatus': mode_status,
            'packetCount': self.network_manager.packet_count,
            'rssi': self.rssi[-1] if self.rssi else 0
        }
    
    def get_presence_status(self) -> dict:
        if self.rssi:
            return {
                'presence': self.predict_presence(),
                'packetLoss': self.network_manager.packet_loss,
                'ampVariance': self.csi_processor.amplitude_variance
            }
        else:
            return {
                'presence': '?',
                'packetLoss': -1,
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
