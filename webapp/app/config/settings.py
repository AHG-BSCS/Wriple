"""Configuration settings for the Human Presence Detection System"""

class NetworkConfiguration:
    """Configuration for network settings"""
    AP_SSID: str = 'Wriple'
    AP_PASSWORD: str = 'Wr!ple@ESP32'
    TX_ESP32_IP: str = '192.168.4.1'
    TX_UDP_PORT: int = 5000
    TX_PAYLOAD: str = 'Wiremap'
    TX_INTERVAL: float = 0.5
    RX_ESP32_PORT: int = 5001
    RX_SOCKET_TIMEOUT: float = 0.5
    RX_BUFFER_SIZE: int = 4096


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
        'Presence', 'Target_Count', 'Angle', 'Distance',
        'Transmit_Timestamp', 'Received_Timestamp', 'RSSI', 'Channel',
        'Raw_CSI',
        'RD03D_Target_1', 'RD03D_Target_2', 'RD03D_Target_3',
        'LD2420_Doppler_1', 'LD2420_Doppler_2', 'LD2420_Doppler_3', 'LD2420_Doppler_4',
        'LD2420_Doppler_5', 'LD2420_Doppler_6', 'LD2420_Doppler_7', 'LD2420_Doppler_8',
        'LD2420_Doppler_9', 'LD2420_Doppler_10', 'LD2420_Doppler_11', 'LD2420_Doppler_12',
        'LD2420_Doppler_13', 'LD2420_Doppler_14', 'LD2420_Doppler_15', 'LD2420_Doppler_16',
        'LD2420_Doppler_17', 'LD2420_Doppler_18', 'LD2420_Doppler_19', 'LD2420_Doppler_20'
    ]


class VisualizerConfiguration:
    """Configuration for data visualizers"""
    AVERAGED: bool = True
    AVERAGED_WINDOWS: list = [(0, 10), (10, -1)]
    SUBCARRIER_COUNT: int = 306
    AMP_HEATMAP_START = 127
    AMP_HEATMAP_END = 148
    PHASE_HEATMAP_START = 6
    PHASE_HEATMAP_END = 27
    D3_STD_THRESHOLD: float = 1.75
    D3_VISUALIZER_SCALE: tuple = (-10, 10)
    # 0: RSSI, 1: Target 1, 2: Target 2, 3: Target 3
    RADAR_DATA: list = [0, [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]


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
