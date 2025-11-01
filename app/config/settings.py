"""Configuration settings for the Human Presence Detection System"""

from pathlib import Path
import os

class NetworkConfig:
    """Configuration for network settings"""
    AP_SSID: str = 'WRIPLE'
    AP_PASSWORD: str = 'WRIPLE_ESP32'
    AP_BROADCAST_IP: str = None
    SERVER_IP_ADDR: str = None

    TX_ESP32_IP: str = None             # IP address assigned by AP to ESP32
    TX_PORT: int = 5001
    TX_CSI_REQ_PAYLOAD = b'Wriple'      # Frame length of 88
    TX_STOP_REQ_PAYLOAD = b'Stop'       # Frame length of 86
    TX_RECONNECT_PAYLOAD = b'Reconnect' # Frame length of 91
    TX_IP_BROADCAST_PAYLOAD = b'Broadcast'
    TX_INTERVAL: float = 0.016          # Adjusted to be approximately 30 packets per second
    TX_CONNECT_INTERVAL: float = 0.05   # Interval between IP request packets
    RECORD_PACKET_LIMIT: int = 250      # 5 seconds of data per recording
    RX_SOCKET_TIMEOUT: float = 0.25     # Timeout used to stop listening
    TX_SOCKET_TIMEOUT: float = 0.1      # Timeout used to stop listening
    RX_BUFFER_SIZE: int = 5120          # Adjusted based on ESP32 CSI and sensor data size

    def to_dict(self) -> dict:
        return {
            'ap_ssid': self.AP_SSID,
            'ap_password': self.AP_PASSWORD,
            'ap_broadcast_ip': self.AP_BROADCAST_IP,
            'tx_esp32_ip': self.TX_ESP32_IP,
            'tx_port': self.TX_PORT,
            'tx_interval': self.TX_INTERVAL,
            'record_packet_limit': self.RECORD_PACKET_LIMIT
        }

    def update(self, config: dict):
        self.AP_SSID = config.get('ap_ssid', self.AP_SSID)
        self.AP_PASSWORD = config.get('ap_password', self.AP_PASSWORD)
        self.AP_BROADCAST_IP = config.get('ap_broadcast_ip', self.AP_BROADCAST_IP)
        self.TX_ESP32_IP = config.get('tx_esp32_ip', self.TX_ESP32_IP)
        self.TX_PORT = config.get('tx_port', self.TX_PORT)
        self.TX_INTERVAL = config.get('tx_interval', self.TX_INTERVAL)
        self.RECORD_PACKET_LIMIT = config.get('record_packet_limit', self.RECORD_PACKET_LIMIT)


class RecordConfig:
    """Configuration for CSI data recording"""
    CSI_QUEUE_LIMIT: int = 180
    RDM_QUEUE_LIMIT: int = 12
    RECORD_PARAMETERS: list = [None, None, None, None, None, None, None, None, None]


class FileConfig:
    """Configuration for CSV file and its columns"""
    _BASE_DIR: Path = Path(__file__).resolve().parent.parent

    SETTING_FILE: str = os.path.join(_BASE_DIR, 'settings', 'settings.json')
    CSV_DIRECTORY: str = os.path.join(_BASE_DIR, 'data', 'record')
    CSV_FILE_PATTERN: str = r'^WRIPLE_DATA_.*$'
    CSV_FILE_PREFIX: str = 'WRIPLE_DATA_'
    CSV_COLUMNS: list = [
        'Presence', 'Target_Count', 'State', 'Activity', 'Angle', 'Distance',
        'Obstructed', 'Obstruction', 'Setup_Spacing',
        'Transmit_Timestamp', 'Received_Timestamp',
        'RSSI', 'Bandwidth', 'Channel', 'Antenna', 'Raw_CSI',
        'LD2420_Doppler_1', 'LD2420_Doppler_2', 'LD2420_Doppler_3', 'LD2420_Doppler_4',
        'LD2420_Doppler_5', 'LD2420_Doppler_6', 'LD2420_Doppler_7', 'LD2420_Doppler_8',
        'LD2420_Doppler_9', 'LD2420_Doppler_10', 'LD2420_Doppler_11', 'LD2420_Doppler_12',
        'LD2420_Doppler_13', 'LD2420_Doppler_14', 'LD2420_Doppler_15', 'LD2420_Doppler_16',
        'LD2420_Doppler_17', 'LD2420_Doppler_18', 'LD2420_Doppler_19', 'LD2420_Doppler_20'
    ]


class CsiConfig:
    """Configuration for data visualizers"""
    HEAT_SUBCARRIER_SLICES: list = [[30, 70]]
    AMPS_SUBCARRIER: list = [(2, 27), (38, 64), (65, 93), (100, 128)]

    HEAT_SIGNAL_WINDOW: int = 60
    HEAT_PENALTY_FACTOR: int = 1
    HEAT_DIFF_THRESHOLD: int = 5

    CUTOFF:float = 0.1
    FS:int = 1
    ORDER:int = 1


class RdmConfig:
    """Configuration for RDM data processing and visualization"""
    _BASE_DIR: Path = Path(__file__).resolve().parent.parent

    HEATMAP_MAX_SCALER: int = 10000
    GATE_DISTANCE: float = 0.7      # Meters
    ABSENCE_TOLERANCE: int = 6      # Number of consecutive 0m before reset
    SMOOTHING_ALPHA: float = 0.5    # 0.5 => Average of current and last non-zero

    GATES_DISTANCE_THRESHOLDS: list = [16000,5000,500,250,150,120,100,80,80,80,70,70,70,70,70,70]
    RDM_THRESHOLDS_PATH: str = os.path.join(_BASE_DIR, 'model', 'rdm_thresholds.json')

    # 20 * doppler with 16 gates
    RDM_PLACEHOLDER_DATA: list = [[0] * 16, [0] * 16, [0] * 16, [0] * 16,
                                  [0] * 16, [0] * 16, [0] * 16, [0] * 16,
                                  [0] * 16, [0] * 16, [0] * 16, [0] * 16,
                                  [0] * 16, [0] * 16, [0] * 16, [0] * 16]


class ModelConfig:
    """Configuration for machine learning models directories and paths"""
    _BASE_DIR: Path = Path(__file__).resolve().parent.parent

    RANDOM_FOREST_PATH: str = os.path.join(_BASE_DIR, 'model', 'rf_model.pkl')
    CONVLSTM_PATH: str = os.path.join(_BASE_DIR, 'model', 'convlstm_model.keras')
    SCALER_PCA_PATH: str = os.path.join(_BASE_DIR, 'model', 'scaler_pca_pipeline.pkl')

    PRED_SIGNAL_WINDOW: int = 120
    FEATURE_XHEIGHT: int = 4
    FEATURE_XWIDTH: int = 5
    PRED_THRESHOLD: float = 0.9079
