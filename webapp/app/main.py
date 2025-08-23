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
        self._is_ld2420_active = True
        self._is_esp32_active = True

        # Initialize parameters and data storage
        self.rssi = 0
        self.mmwave_data = []
        self.mmwave_queue_limit = RecordingConfiguration.MMWAVE_QUEUE_LIMIT
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
            self.csi_processor.queue_amplitude_phase(parsed_data[6])

            # Remove oldest mmwave data if it exceeds the limit
            while len(self.mmwave_data) > self.mmwave_queue_limit:
                self.mmwave_data.pop(0)

            if parsed_data[0]: # If ld24020 data is valid
                self.mmwave_data.append(parsed_data[7:])

            self.rssi = parsed_data[2]
        
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
        self.network_manager.request_captured_data()

        threading.Thread(
            target=self.network_manager.start_listening,
            args=(self.parse_received_data, self.is_recording),
            daemon=True
        ).start()
    
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
        if self.model_manager.model_loaded:
            features = []

            for data in self.mmwave_data:
                features.append(data[9:12])

            return self.model_manager.predict(features)
        else:
            return 'No'
    
    def get_system_status(self) -> dict:
        """
        Get current system components status
        
        Returns:
            dict: Dictionary with status of each system component
        """
        if self.network_manager.check_esp32():
            self._is_esp32_active = True
            self._is_ld2420_active = PacketParser.is_ld2420_active()
        else:
            self._is_esp32_active = False
            self._is_ld2420_active = False

        return {
            'ap': self.network_manager.check_wifi_connection(),
            'esp32': self._is_esp32_active,
            'ld2420': self._is_ld2420_active,
            'port': self.network_manager.is_udp_port_opened,
            'model': self.model_manager.model_loaded
        }
    
    def get_monitor_status(self) -> dict:
        presence_prediction = self.predict_presence()
        mode_status = (0 if self.is_recording and self.network_manager.is_listening else 
                       1 if self.is_monitoring else -1)
        
        return {
            'modeStatus': mode_status,
            'presence': presence_prediction,
            'targetDistance': 0,  # Placeholder for target distance
            'packetCount': self.network_manager.packet_received_count,
            'packetLoss': self.network_manager.get_packet_loss_rate(),
            'rssi': self.rssi,
            'expValue': 0
            # 'exp': self.mmwave_data[10][3]
        }
    
    def get_radar_status(self) -> dict:
        """
        Get radar data and predictions
        
        Returns:
            dict: Dictionary with radar data and presence prediction
        """
        mode_status = (0 if self.is_recording and self.network_manager.is_listening else 
                       1 if self.is_monitoring else -1)
        
        return {
            'modeStatus': mode_status,
            'angle': 0,
            'distance': 0,
            'energy': 0
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
                - distance: Distance to target
        
        Returns:
            bool: True if parameters were set successfully, False otherwise
        """
        try:
            self.record_parameters = [
                int(params['class_label']),
                int(params['target_count']),
                int(params['state']),
                int(params['activity']),
                int(params['angle']),
                int(params['distance']),
                int(params['obstructed']),
                int(params['obstruction']),
                int(params['spacing']),
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
