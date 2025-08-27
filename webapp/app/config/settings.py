"""Configuration settings for the Human Presence Detection System"""

class NetworkConfig:
    """Configuration for network settings"""
    AP_SSID: str = None
    AP_PASSWORD: str = None
    AP_BROADCAST_IP: str = None

    TX_ESP32_IP: str = None             # IP address assigned by AP to ESP32
    TX_UDP_PORT: int = None             # Keep the port open using firewall
    TX_CSI_REQ_PAYLOAD: str = b'Wriple' # Frame length of 88
    TX_STOP_REQ_PAYLOAD: str = b'Stop'  # Frame length of 86
    TX_IP_REQ_PAYLOAD: str = b'Connect'
    TX_CAPTURE_INTERVAL: float = None   # Adjusted to be approximately 30 packets per second
    RECORD_PACKET_LIMIT: int = None     # 5 seconds of data per recording
    RX_SOCKET_TIMEOUT: float = 0.25     # Timeout used to stop listening
    TX_SOCKET_TIMEOUT: float = 0.1      # Timeout used to stop listening
    RX_BUFFER_SIZE: int = 4096          # Adjusted based on ESP32 CSI and sensor data size

    def to_dict(self) -> dict:
        return {
            'ap_ssid': self.AP_SSID,
            'ap_password': self.AP_PASSWORD,
            'ap_broadcast_ip': self.AP_BROADCAST_IP,
            'tx_esp32_ip': self.TX_ESP32_IP,
            'tx_udp_port': self.TX_UDP_PORT,
            'tx_capture_interval': self.TX_CAPTURE_INTERVAL,
            'record_packet_limit': self.RECORD_PACKET_LIMIT
        }

    def update(self, config: dict):
        self.AP_SSID = config.get('ap_ssid', self.AP_SSID)
        self.AP_PASSWORD = config.get('ap_password', self.AP_PASSWORD)
        self.AP_BROADCAST_IP = config.get('ap_broadcast_ip', self.AP_BROADCAST_IP)
        self.TX_ESP32_IP = config.get('tx_esp32_ip', self.TX_ESP32_IP)
        self.TX_UDP_PORT = config.get('tx_udp_port', self.TX_UDP_PORT)
        self.TX_CAPTURE_INTERVAL = config.get('tx_capture_interval', self.TX_CAPTURE_INTERVAL)
        self.RECORD_PACKET_LIMIT = config.get('record_packet_limit', self.RECORD_PACKET_LIMIT)


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
        'RSSI', 'Bandwidth', 'Channel', 'Antenna', 'Raw_CSI',
        'LD2420_Doppler_1', 'LD2420_Doppler_2', 'LD2420_Doppler_3', 'LD2420_Doppler_4',
        'LD2420_Doppler_5', 'LD2420_Doppler_6', 'LD2420_Doppler_7', 'LD2420_Doppler_8',
        'LD2420_Doppler_9', 'LD2420_Doppler_10', 'LD2420_Doppler_11', 'LD2420_Doppler_12',
        'LD2420_Doppler_13', 'LD2420_Doppler_14', 'LD2420_Doppler_15', 'LD2420_Doppler_16',
        'LD2420_Doppler_17', 'LD2420_Doppler_18', 'LD2420_Doppler_19', 'LD2420_Doppler_20'
    ]
    SETTING_FILE: str = 'setting/setting.json'


class VisualizerConfiguration:
    """Configuration for data visualizers"""
    AVERAGED: bool = True
    AVERAGED_WINDOWS: list = [(0, 10), (10, -1)]
    SUBCARRIER_COUNT: int = 192

    HEAT_SIGNAL_WINDOW: int = 30
    HEAT_AMP_START_SUB:int = 3
    HEAT_AMP_END_SUB:int = 88
    HEAT_PHASE_START_SUB:int = 6
    HEAT_PHASE_END_SUB:int = 27
    HEAT_PENALTY_FACTOR: int = 1
    HEAT_DIFF_THRESHOLD: int = 5

    CUTOFF:float = 0.1
    FS:int = 1
    ORDER:int = 5

    D3_STD_THRESHOLD: float = 1.75
    D3_VISUALIZER_SCALE: tuple = (-10, 10)

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
