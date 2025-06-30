"""Configuration settings for the Human Presence Detection System"""

class NetworkConfiguration:
    """Configuration for network settings"""
    AP_SSID: str = 'Wriple'
    AP_PASSWORD: str = 'Wr!ple@ESP32'
    TX_ESP32_IP: str = '192.168.4.1'
    TX_UDP_PORT: int = 5000
    TX_PAYLOAD: str = 'Wriple' # 88 frame length
    # TX_MONITOR_INTERVAL: float = 0.1
    TX_MONITOR_INTERVAL: float = 0.333
    TX_RECORD_INTERVAL: float = 0.333
    RX_ESP32_PORT: int = 5001
    RX_SOCKET_TIMEOUT: float = 0.5
    RX_BUFFER_SIZE: int = 4096


class RecordingConfiguration:
    """
    Configuration for CSI data recording
    Packet and queue limits are based on TX interval
    """
    MONITOR_QUEUE_LIMIT: int = 10
    RECORD_PACKET_LIMIT: int = 60
    MMWAVE_QUEUE_LIMIT: int = 12
    # 0: Class, 1: Target, 2: Angle, 4: Distance
    RECORD_PARAMETERS: list = [None, None, None, None, None]


class FileConfiguration:
    """Configuration for CSV file and its columns"""
    CSV_DIRECTORY: str = 'data/recorded'
    CSV_FILE_PATTERN: str = r'^MMWAVE_DATA_.*$'
    CSV_FILE_PREFIX: str = 'MMWAVE_DATA_'
    CSV_COLUMNS: list = [
        'Presence', 'Target_Count', 'Obstructed', 'Angle', 'Distance',
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
    # 20 * doppler with 16 gates
    MMWAVE_DATA: list = [[0] * 16, [0] * 16, [0] * 16, [0] * 16,
                        [0] * 16, [0] * 16, [0] * 16, [0] * 16,
                        [0] * 16, [0] * 16, [0] * 16, [0] * 16,
                        [0] * 16, [0] * 16, [0] * 16, [0] * 16]
    GATE_THRESHOLDS = [
        (60000, 40000), (30000, 20000), (400, 200), (300, 250),
        (250, 150), (250, 150), (250, 150), (250, 150),
        (300, 150), (250, 150), (250, 150), (250, 150),
        (250, 100), (200, 100), (200, 100), (200, 100)
    ]

class ModelConfiguration:
    """Configuration for machine learning models directories and paths"""
    MODEL_DIR: str = 'model'
    LOGREG_PATH: str = 'model/wriple_v3_LogReg.pkl'
    RANDFOR_PATH: str = 'model/wriple_v3_RandFor.pkl'
    ADABOOST_PATH: str = 'model/wriple_v3_AdaBoost.pkl'
    CONVLSTM_PATH: str = 'model/wriple_v3_ConvLSTM.keras'
    TCN_PATH: str = 'model/wriple_v3_TCN.keras'
    THRESHOLD_PATH: str = 'model/wriple_v3_Threshold.json'


class PredictionConfiguration:
    """Configuration for data preprocessing and prediction"""
    SIGNAL_WINDOW: int = 7


class FlaskConfiguration:
    """Configuration for Flask application"""
    DEBUG: bool = True
    HOST: str = '0.0.0.0'
    PORT: int = 5000
