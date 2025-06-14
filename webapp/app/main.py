import threading
from flask import Flask

from config.settings import FlaskConfiguration, PredictionConfiguration, RecordingConfiguration, VisualizerConfiguration
from core.csi_processor import CSIProcessor
from core.network_manager import NetworkManager
from core.data_recorder import DataRecorder
from utils.model_loader import ModelLoader
from utils.packet_parser import PacketParser
from api.routes import create_api_routes
from utils.logger import setup_logger


class HumanDetectionSystem:
    """Main class that coordinates all components"""
    
    def __init__(self):
        # Initialize core components
        self.csi_processor = CSIProcessor()
        self.network_manager = NetworkManager()
        self.data_recorder = DataRecorder()
        self.model_loader = ModelLoader()
        
        # Application state and counter
        self.is_recording = False
        self.is_monitoring = False
        self.total_packet_count = 0
        self.presence_prediction = 0

        # Initialize parameters and data storage
        self.tx_timestamps = []
        self.signal_window = PredictionConfiguration.SIGNAL_WINDOW
        self.radar_data = VisualizerConfiguration.RADAR_DATA
        self.record_parameters = RecordingConfiguration.RECORD_PARAMETERS
        # self.ml_predictor = self.model_loader.load_models()

        self.logger = setup_logger('HumanDetectionSystem')
    
    def parse_received_data(self, raw_data):
        """Process data received from ESP32"""
        try:
            data_str = raw_data.decode('utf-8').strip()
            parsed_data = PacketParser.parse_csi_data(data_str)
            
            # Extract radar and CSI data
            self.radar_data = PacketParser.extract_radar_data(parsed_data)
            amplitudes, phases = self.csi_processor.compute_csi_amplitude_phase(parsed_data[-1])
            self.csi_processor.add_to_queue(amplitudes, phases)
            
            # Record data to csv file if recording
            if self.is_recording:
                self.record_data_packet(parsed_data)
            
            self.total_packet_count += 1
            
        except Exception as e:
            self.logger.error(f'Error parsing received data: {e}')
    
    def record_data_packet(self, parsed_data):
        """Record data packet to CSV file"""
        # Add recording metadata
        timestamp = self.tx_timestamps.pop(0)
        complete_data = [timestamp] + self.record_parameters + parsed_data
        self.data_recorder.write_data(complete_data)
    
    def start_recording_mode(self):
        """Start recording Wi-Fi CSI data into CSV file"""
        self.is_recording = True
        self.data_recorder.prepare_new_file()
        self.csi_processor.set_max_packets(RecordingConfiguration.RECORD_PACKET_LIMIT)
        self.tx_timestamps = self.network_manager.start_transmitting()

        threading.Thread(
            target=self.network_manager.start_listening,
            args=(self.parse_received_data, RecordingConfiguration.RECORD_PACKET_LIMIT),
            daemon=True
        ).start()
    
    def start_monitoring_mode(self):
        """Start monitoring WI-Fi CSI data without recording"""
        self.is_monitoring = True
        self.csi_processor.set_max_packets(RecordingConfiguration.MONITOR_QUEUE_LIMIT)
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
        self.total_packet_count = 0
        
        self.network_manager.stop_transmitting()
        self.network_manager.stop_listening()
        self.csi_processor.clear_queues()
    
    def predict_presence(self):
        """Make presence prediction using ML model"""
        if (self.model_loader.is_model_loaded 
            and self.csi_processor.get_queue_size() >= self.signal_window * 2):
            # Get the latest data for prediction
            features = self.csi_processor.amplitude_queue[:self.signal_window]
            self.presence_prediction = self.ml_predictor.predict(features)
    
    def get_system_status(self):
        """Get current system components status"""
        return {
            'esp32': 1,  # Temporary placeholder for ESP32 status
            'ap': self.network_manager.check_wifi_connection(),
            'rd03d': 1,  # Temporary placeholder for RD03D status
            'port': 1,   # Temporary placeholder for port status
            'model': self.model_loader.is_model_loaded
        }
    
    def get_radar_status(self):
        """Get radar data and predictions"""
        self.predict_presence()
        
        mode_status = (0 if self.is_recording and self.network_manager.is_listening else 
                      1 if self.is_monitoring else -1)
        
        return {
            'presence': self.presence_prediction,
            'radarX': self.radar_data[1],
            'radarY': self.radar_data[2],
            'radarSpeed': self.radar_data[3],
            'radarDistRes': self.radar_data[4],
            'totalPacket': self.total_packet_count,
            'rssi': self.radar_data[0],
            'modeStatus': mode_status
        }
    
    def set_recording_parameters(self, params: dict):
        """Set parameters for recording"""
        try:
            self.record_parameters = [
                int(params.get('class_label', 0)),
                int(params.get('target_count', 0)),
                float(params.get('angle', 0.0)) - float(params.get('line_of_sight', 0.0)),
                float(params.get('distance_t1', 0.0))
            ]
            self.logger.info(f"Recording parameters set")
            return True
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error setting recording parameters exception: {e}")
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
