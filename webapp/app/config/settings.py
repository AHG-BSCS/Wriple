"""Configuration settings for the Human Presence Detection System"""

class NetworkConfiguration:
    """Configuration for network settings"""
    AP_SSID: str = 'Wriple'
    AP_PASSWORD: str = 'Wr!ple@ESP32'
    AP_INTERFACE: str = 'Wi-Fi'
    AP_STATIC_IP: str = '192.168.11.222'
    AP_SUBNET_MASK: str = '255.255.255.0'
    AP_GATEWAY: str = '192.168.11.236'
    AP_DNS: str = '8.8.8.8'

    TX_ESP32_IP: str = '192.168.11.163' # IP address assigned by AP to ESP32
    TX_UDP_PORT: int = 5000             # Keep the port open using firewall
    TX_CSI_REQ_PAYLOAD: str = 'Wriple'  # Frame length of 88
    TX_STOP_REQ_PAYLOAD: str = 'Stop'   # Frame length of 86
    TX_CAPTURE_INTERVAL: float = 0.015  # Adjusted to meet the 30 packets per second
    RECORD_PACKET_LIMIT: int = 150      # 5 seconds of data per recording
    RX_SOCKET_TIMEOUT: float = 0.25     # Timeout used to stop listening
    RX_BUFFER_SIZE: int = 4096          # Adjusted based on ESP32 CSI and sensor data size


class RecordingConfiguration:
    """
    Configuration for CSI data recording
    Packet and queue limits are based on TX interval
    """
    MONITOR_QUEUE_LIMIT: int = 90
    MMWAVE_QUEUE_LIMIT: int = 12
    RECORD_PARAMETERS: list = [None, None, None, None, None, None, None, None, None]


class FileConfiguration:
    """Configuration for CSV file and its columns"""
    CSV_DIRECTORY: str = 'data/recorded'
    CSV_FILE_PATTERN: str = r'^WRIPLE_DATA_.*$'
    CSV_FILE_PREFIX: str = 'WRIPLE_DATA_'
    CSV_COLUMNS: list = [
        'Presence', 'Target_Count', 'State', 'Activity', 'Angle', 'Distance',
        'Obstructed', 'Obstruction', 'Spacing',
        'Transmit_Timestamp', 'Received_Timestamp',
        'RSSI', 'Channel', 'Raw_CSI',
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
    SUBCARRIER_COUNT: int = 192

    HEAT_SIGNAL_WINDOW: int = 10
    HEAT_AMP_START_SUB:int = 3
    HEAT_AMP_END_SUB:int = 88
    HEAT_PHASE_START_SUB:int = 6
    HEAT_PHASE_END_SUB:int = 27
    HEAT_PENALTY_FACTOR: int = 1
    HEAT_DIFF_THRESHOLD: int = 3

    CUTOFF:float = 0.1
    FS:int = 1
    ORDER:int = 5

    D3_STD_THRESHOLD: float = 1.75
    D3_VISUALIZER_SCALE: tuple = (-10, 10)

    # 0: RSSI, 1: EXP, 2: Target 1, 3: Target 2, 4: Target 3
    RADAR_DATA: list = [0, 0, [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    # 20 * doppler with 16 gates
    MMWAVE_DATA: list = [[0] * 16, [0] * 16, [0] * 16, [0] * 16,
                        [0] * 16, [0] * 16, [0] * 16, [0] * 16,
                        [0] * 16, [0] * 16, [0] * 16, [0] * 16,
                        [0] * 16, [0] * 16, [0] * 16, [0] * 16]


class ModelConfiguration:
    """Configuration for machine learning models directories and paths"""
    MODEL_DIR: str = 'model'
    LOGREG_PATH: str = 'model/wriple_v3_LogReg.pkl'
    RANDFOR_PATH: str = 'model/wriple_v3_RandFor.pkl'
    ADABOOST_PATH: str = 'model/wriple_v3_AdaBoost.pkl'
    CONVLSTM_PATH: str = 'model/wriple_v3_ConvLSTM.keras'
    TCN_PATH: str = 'model/wriple_v3_TCN.keras'

    THRESHOLD_MODEL_PATH: str = 'model/wriple_v3_Thres_Model.json'
    THRESHOLD_MMWAVE_VIZ_PATH: str = 'model/wriple_v3_Thres_Visual.json'


class PredictionConfiguration:
    """Configuration for data preprocessing and prediction"""
    PRED_SIGNAL_WINDOW: int = 7


class FlaskConfiguration:
    """Configuration for Flask application"""
    DEBUG: bool = False
    HOST: str = '0.0.0.0'
    PORT: int = 3000
