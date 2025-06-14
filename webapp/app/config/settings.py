"""Configuration settings for the Human Presence Detection System"""

class NetworkConfiguration:
    """Configuration for network settings"""
    AP_SSID: str = 'Wiremap'
    AP_PASSWORD: str = 'WiReMap@ESP32'
    TX_ESP32_IP: str = '192.168.4.1'
    TX_UDP_PORT: int = 5000
    TX_PAYLOAD: str = 'Wiremap'
    TX_INTERVAL: float = 0.05
    RX_ESP32_PORT: int = 5001
    RX_SOCKET_TIMEOUT: float = 1.0
    RX_BUFFER_SIZE: int = 2048


class RecordingConfiguration:
    """
    Configuration for CSI data recording
    Packet and queue limits are based on TX interval
    """
    MONITOR_QUEUE_LIMIT: int = 20
    RECORD_PACKET_LIMIT: int = 240
    # 0: Class, 1: Target, 2: Angle, 4: Distance
    RECORD_PARAMETERS: list = [None, None, None, None, None]


class FileConfiguration:
    """Configuration for CSV file and its columns"""
    CSV_DIRECTORY: str = 'data/recorded'
    CSV_FILE_PATTERN: str = r'^CSI_DATA_.*$'
    CSV_FILE_PREFIX: str = 'CSI_DATA_'
    CSV_COLUMNS: list = [
        'Transmit_Timestamp', 'Presence', 'Target_Count', 'Angle', 'Distance', 
        'RSSI', 'Rate', 'MCS', 'Channel', 'Received_Timestamp',
        'Target1_X', 'Target1_Y', 'Target1_Speed', 'Target1_Resolution', 
        'Target2_X', 'Target2_Y', 'Target2_Speed', 'Target2_Resolution', 
        'Target3_X', 'Target3_Y', 'Target3_Speed', 'Target3_Resolution', 'Raw_CSI'
    ]


class VisualizerConfiguration:
    """Configuration for data visualizers"""
    AVERAGED: bool = True
    AVERAGED_WINDOWS: list = [(0, 10), (10, -1)]
    SUBCARRIER_COUNT: int = 306
    D3_STD_THRESHOLD: float = 1.75
    D3_VISUALIZER_SCALE: tuple = (-10, 10)
    MAX_PACKET: int = 100
    # 0: RSSI, 1: X, 2: Y, 3: Speed, 4: Resolution
    RADAR_DATA: list = [0, [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]


class ModelConfiguration:
    """Configuration for machine learning models directories and paths"""
    MODEL_DIR: str = 'model'
    SCALER_PATH: str = 'model/wriple_v2-std.pkl'
    PCA_PATH: str = 'model/wriple_v2-lg.pkl'
    LOGREG_PATH: str = 'model/wriple_v2-pca.pkl'


class PredictionConfiguration:
    """Configuration for data preprocessing and prediction"""
    SIGNAL_WINDOW: int = 5


class FlaskConfiguration:
    """Configuration for Flask application"""
    DEBUG: bool = True
    HOST: str = '0.0.0.0'
    PORT: int = 5000
