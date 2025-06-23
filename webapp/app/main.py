import threading
from flask import Flask

from config.settings import FlaskConfiguration, RecordingConfiguration, VisualizerConfiguration
from core.csi_processor import CSIProcessor
from core.file_manager import FileManager
from core.model_manager import ModelManager
from core.network_manager import NetworkManager
from utils.packet_parser import PacketParser
from api.routes import create_api_routes
from utils.logger import setup_logger


class HumanDetectionSystem:
    """Main class that coordinates all components"""
    
    def __init__(self):
        # Initialize core components
        self.csi_processor = CSIProcessor()
        self.file_manager = FileManager()
        self.model_manager = ModelManager()
        self.network_manager = NetworkManager()
        
        # Application state and counter
        self.is_recording = False
        self.is_monitoring = False

        # Initialize parameters and data storage
        self.radar_data = VisualizerConfiguration.RADAR_DATA
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
        self.csi_processor.buffer_amplitude_phase(parsed_data[3])
        self.radar_data = [parsed_data[1], parsed_data[4], parsed_data[5], parsed_data[6]]
        
        # Record data to csv file if recording
        if self.is_recording:
            self.record_data_packet(parsed_data, tx_timestamp)
    
    def start_recording_mode(self):
        """Start recording Wi-Fi CSI data into CSV file"""
        if not self.network_manager.check_wifi_connection():
            self.logger.error('Not connected to ESP32 AP, cannot start recording')
            return
        
        self.is_recording = True
        self.file_manager.init_new_csv()
        self.csi_processor.set_max_packets(0)
        self.network_manager.start_transmitting()

        threading.Thread(
            target=self.network_manager.start_listening,
            args=(self.parse_received_data, RecordingConfiguration.RECORD_PACKET_LIMIT),
            daemon=True
        ).start()
    
    def start_monitoring_mode(self):
        """Start monitoring WI-Fi CSI data without recording"""
        if not self.network_manager.check_wifi_connection():
            self.logger.error('Not connected to ESP32 AP, cannot start monitoring')
            return
        
        self.is_monitoring = True
        self.csi_processor.set_max_packets(0)
        self.network_manager.start_transmitting()

        threading.Thread(
            target=self.network_manager.start_listening,
            args=(self.parse_received_data,),
            daemon=True
        ).start()
    
    def stop_operations(self):
        """Stop all recording/monitoring operations"""
        self.is_recording = False
        self.is_monitoring = False
        
        self.network_manager.stop_transmitting()
        self.network_manager.stop_listening()
        self.csi_processor.clear_queues()
    
    def predict_presence(self) -> int:
        """
        Make presence prediction using ML model
        
        Returns:
            int: Presence prediction (1 for presence, 0 for absence)
        """
        if self.model_manager.model_loaded:
            features = self.csi_processor.get_amplitude_window()
            return self.model_manager.predict(features)
        else:
            return 0
    
    def get_system_status(self) -> dict:
        """
        Get current system components status
        
        Returns:
            dict: Dictionary with status of each system component
        """
        return {
            'esp32': 1,  # Temporary placeholder for ESP32 status
            'ap': self.network_manager.check_wifi_connection(),
            'rd03d': 1,  # Temporary placeholder for RD03D status
            'port': 1,   # Temporary placeholder for port status
            'model': self.model_manager.model_loaded
        }
    
    def get_radar_status(self) -> dict:
        """
        Get radar data and predictions
        
        Returns:
            dict: Dictionary with radar data and presence prediction
        """
        presence_prediction = self.predict_presence()
        mode_status = (0 if self.is_recording and self.network_manager.is_listening else 
                      1 if self.is_monitoring else -1)
        
        return {
            'presence': presence_prediction,
            'target1': self.radar_data[1],
            'target2': self.radar_data[2],
            'target3': self.radar_data[3],
            'totalPacket': self.network_manager.packet_count,
            'rssi': self.radar_data[0],
            'modeStatus': mode_status
        }
    
    def set_recording_parameters(self, params: dict) -> bool:
        """
        Set parameters for recording
        
        Args:
            params: Dictionary with recording parameters including:
                - class_label: Label for the presence class
                - target_count: Number of targets to record
                - angle: Angle of the target
                - line_of_sight: Line of sight angle from the radar center point of view
                - distance_t1: Distance to target
        
        Returns:
            bool: True if parameters were set successfully, False otherwise
        """
        try:
            self.record_parameters = [
                params['class_label'],
                params['target_count'],
                float(params['angle']) - float(params['line_of_sight']),
                float(params['distance_t1'])
            ]
            self.logger.info(f'Recording parameters set')
            return True
        except (ValueError, TypeError) as e:
            self.logger.error(f'Error setting recording parameters exception: {e}')
            return False


def create_app():
    """Factory function to create Flask app"""
    app = Flask(__name__)
    # Initialize the detection system
    detection_system = HumanDetectionSystem()
    create_api_routes(app, detection_system)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=FlaskConfiguration.DEBUG,
        host=FlaskConfiguration.HOST,
        port=FlaskConfiguration.PORT
    )
