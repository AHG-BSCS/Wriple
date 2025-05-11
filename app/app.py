import os
import re
import csv
import joblib
import math
import numpy as np
import pandas as pd
import socket
import subprocess
import time
import threading
# from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from scapy.all import Raw, IP, UDP, send
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
lock = threading.Lock()

SSID = 'Wiremap'
PASSWORD = 'WiReMap@ESP32'
ESP32_IP = '192.168.4.1' # Default IP address of the ESP32 AP
PAYLOAD = 'Wiremap' # Signal Length is 89
ESP32_PORT = 5001
UDP_PACKET = IP(dst=ESP32_IP)/UDP(sport=5000, dport=ESP32_PORT)/Raw(load=PAYLOAD)
MONITORING_PACKET_LIMIT = 20
RECORDING_PACKET_LIMIT = 240 # 12 seconds of data
TX_INTERVAL = 0.05

csv_file_path = None
CSV_DIRECTORY = 'app/dataset/recorded'
DATASET_COLUMNS = None
X_TEST_COLUMNS = None

MM_SCALER = MinMaxScaler((-10, 10))
STD_SCALER = StandardScaler()
pca = None

WINDOW_RANGE = [(0, 10), (10, -1)]
SUBCARRIER_COUNT = 306
SMOOTH = True

recording = False
monitoring = False
total_packet_count = 0
max_monitoring_packets = 20

transmit_timestamp = []
amplitude_queue = []
phase_queue = []
radar_x_coord = [0, 0, 0]
radar_y_coord = [0, 0, 0]
radar_speed = [0, 0, 0]
radar_dist_res = [0, 0, 0]
rssi = 0

model = None
presence_pred = 0
target_count = None
class_label = None
line_of_sight = None
angle = None
distance_t1 = None
std_threshold = 1.75

esp32_status = 1
ap_status = None
rd03d_status = 1
port_status = 1
model_status = None

def clean_and_filter_data(amplitudes, phases, amp_lower_threshold, amp_upper_threshold, 
                          phase_lower_threshold, phase_upper_threshold):
    cleaned_amplitudes = []
    cleaned_phases = []
    subcarriers = range(len(amplitudes))

    # Retain outliers based on amplitude and phase
    for i, amp, phase in zip(subcarriers, amplitudes, phases):
        if ((amp < amp_lower_threshold[i]) or (amp > amp_upper_threshold[i]) and 
            (phase < phase_lower_threshold[i]) or (phase > phase_upper_threshold[i])):
            cleaned_amplitudes.append(amp)
            cleaned_phases.append(phase)
        else:
            cleaned_amplitudes.append(0)
            cleaned_phases.append(0)

    return cleaned_amplitudes, cleaned_phases

def get_subcarrier_threshold(data_transposed):
    lower_threshold, upper_threshold = [], []

    for column in data_transposed:
        mean = np.mean(column)
        std_dev = np.std(column)

        lower_threshold.append(mean - std_threshold * std_dev)
        upper_threshold.append(mean + std_threshold * std_dev)

    return lower_threshold, upper_threshold

def filter_amp_phase():
    global max_monitoring_packets, presence_pred
    signal_coordinates = []

    # Load the data if file was selected for visualization
    if max_monitoring_packets == RECORDING_PACKET_LIMIT:
        try:
            csi_df = pd.read_csv(csv_file_path)
            csi_df['Raw_CSI'] = csi_df['Raw_CSI'].apply(eval)
            csi_df['Raw_CSI'].apply(compute_csi_amplitude_phase)
        except Exception as e:
            print("Error: 'Amplitude' or 'Phase' column not found in the file.", e)
            return
    
    if len(amplitude_queue) < RECORDING_PACKET_LIMIT:
        return

    csi_amplitude = pd.Series(amplitude_queue)
    csi_phase = pd.Series(phase_queue)
    
    predict_presence(csi_df)

    # Transpose to make subcarriers as rows
    amps_transposed = list(map(list, zip(*csi_amplitude)))
    phases_transposed = list(map(list, zip(*csi_phase)))

    # Scaled because of d3 visualization
    scaled_amplitudes = MM_SCALER.fit_transform(amps_transposed).T
    scaled_phases = MM_SCALER.fit_transform(phases_transposed).T

    # Get the threshold for each subcarrier
    amp_lower_threshold, amp_upper_threshold = get_subcarrier_threshold(scaled_amplitudes.T)
    phase_lower_threshold, phase_upper_threshold = get_subcarrier_threshold(scaled_phases.T)
    
    for amp, phase in zip(scaled_amplitudes, scaled_phases):
        amp = np.array(amp)
        phase = np.array(phase)

        # Limit the number of data to plot for better performance using standard deviation threshold
        amp, phase = clean_and_filter_data(
            amp, phase, 
            amp_lower_threshold, amp_upper_threshold, 
            phase_lower_threshold, phase_upper_threshold
        )

        # Ensures that each subcarrier is plot in the same x-axis
        x = np.arange(-10, 10, 20/len(amp))
        z = phase
        y = amp

        for i in range(len(x)):
            if z[i] == 0:
                continue
            signal_coordinates.append((float(x[i]), float(y[i]), float(z[i])))
    
    if not monitoring:
        # Reset the monitoring limit and data queue after recording
        max_monitoring_packets = MONITORING_PACKET_LIMIT
        amplitude_queue.clear()
        phase_queue.clear()
    
    return signal_coordinates

def predict_presence():
    global presence_pred
    signal_queue_length = len(amplitude_queue)
    if model and signal_queue_length > 5:
        rows = []
        frame_set = [(i, i + 5) for i in range(0, signal_queue_length, 2)]
        amplitude_features = [np.percentile(amplitude_queue[start:end], 25, axis=0) for start, end in frame_set]

        X_test = pd.DataFrame(amplitude_features, columns=X_TEST_COLUMNS)
        X_test = STD_SCALER.fit_transform(X_test)
        X_pca = pca.transform(X_test)

        y_pred = model.predict(X_pca)
        presence_pred = 0 if 0 in y_pred else 1

def compute_csi_amplitude_phase(csi_data):
    amplitudes = []
    phases = []
    
    if len(csi_data) % 2 != 0: raise ValueError('CSI data length must be even (I/Q pairs).')
    for i in range(0, len(csi_data), 2):
        I = csi_data[i]
        Q = csi_data[i + 1]
        amplitudes.append(math.sqrt(I**2 + Q**2))
        phases.append(math.atan2(Q, I))
    
    # Remove old signals if the queue exceeds the limit
    while len(amplitude_queue) >= max_monitoring_packets:
        amplitude_queue.pop(0)
        phase_queue.pop(0)

    amplitude_queue.append(amplitudes)
    phase_queue.append(phases)

def parse_csi_data(data_str):
    parts = data_str.split(',')
    csi_data_start = data_str.find('[')
    csi_data_end = data_str.find(']')

    # Extract CSI data as a string of integers
    raw_csi = data_str[csi_data_start + 1:csi_data_end].strip().split(' ')
    raw_csi = list(filter(None, raw_csi))  # TODO: Evaluate if needed: Remove empty strings
    
    try:
        raw_csi = [int(x) for x in raw_csi]
        if monitoring:
            compute_csi_amplitude_phase(raw_csi)
    except ValueError:
        raw_csi = []

    # Use -1 to exclude the unformatted Raw CSI data
    return parts[:-1] + [raw_csi]

def process_data(data, m):
    global max_monitoring_packets, rssi
    try:
        data_str = data.decode('utf-8').strip()
        csi_data = parse_csi_data(data_str)
        rssi = csi_data[0]

        radar_x_coord.clear()
        radar_x_coord.append(csi_data[5])
        radar_x_coord.append(csi_data[9])
        radar_x_coord.append(csi_data[13])

        radar_y_coord.clear()
        radar_y_coord.append(csi_data[6])
        radar_y_coord.append(csi_data[10])
        radar_y_coord.append(csi_data[14])

        radar_speed.clear()
        radar_speed.append(csi_data[7])
        radar_speed.append(csi_data[11])
        radar_speed.append(csi_data[15])

        radar_dist_res.clear()
        radar_dist_res.append(csi_data[8])
        radar_dist_res.append(csi_data[12])
        radar_dist_res.append(csi_data[16])

        if (recording):
            csi_data.insert(0, transmit_timestamp.pop(0))
            csi_data.insert(1, class_label)
            csi_data.insert(2, target_count)
            csi_data.insert(3, angle - line_of_sight)
            csi_data.insert(4, distance_t1)
            max_monitoring_packets = RECORDING_PACKET_LIMIT

            # Write to the CSV file with a lock to ensure thread safety
            with lock:
                with open(csv_file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(csi_data)
    except Exception as e:
        print(f'Error processing data: {e}')
    
def listen_to_packets():
    global recording, monitoring, total_packet_count, max_monitoring_packets
    mode = 0 if recording else 1
    packet_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    packet_listener.bind(('0.0.0.0', 5000))
    packet_listener.settimeout(1.0)

    print('Recording CSI data...')
    while recording or monitoring:
        try:
            # Adjusted buffer size for CSI Data. May rarely cause buffer overflow.
            data, addr = packet_listener.recvfrom(2048)
            total_packet_count += 1
            if monitoring:
                threading.Thread(target=process_data, args=(data, True)).start()
                continue
            elif total_packet_count <= RECORDING_PACKET_LIMIT:
                threading.Thread(target=process_data, args=(data, True)).start()
            else:
                total_packet_count = 0
                break
        except socket.timeout:
            if not recording and not monitoring:
                max_monitoring_packets = 100
                total_packet_count = 0
                break
            else:
                continue
        except KeyboardInterrupt:
            break
        except OverflowError:
            total_packet_count = 0
            continue
        except Exception:
            print('Packet size is larger than buffer size. Restarting...')
            continue

    # if mode == 0:
    #     compute_time_of_flight()
    
    recording = False
    monitoring = False
    
    print('Stopped recording CSI data.')

def send_packets():
    try:
        if monitoring:
            send(UDP_PACKET, verbose=False)
            threading.Timer(TX_INTERVAL, send_packets).start()
        elif recording and not monitoring and total_packet_count <= RECORDING_PACKET_LIMIT:
            # Get the sending timestamp as accurate as possible
            send(UDP_PACKET, verbose=False)
            tx_time = time.time()
            tx_time = int((tx_time * 1_000_000) % 1_000_000_000)
            transmit_timestamp.append(tx_time)
            threading.Timer(TX_INTERVAL, send_packets).start()
        else:
            print('Stopped sending packets.')
    except KeyboardInterrupt:
        pass

def prepare_csv_file():
    global csv_file_path
    csv_dir = CSV_DIRECTORY
    files = os.listdir(csv_dir)

    if DATASET_COLUMNS is None: set_columns()
    
    # Filter files that match the pattern CSI_DATA_XXX
    pattern = re.compile(r'^CSI_DATA_.*$')
    matching_files = [f for f in files if pattern.match(f)]
    
    # Extract the numeric part and find the highest number
    if matching_files:
        numbers = [int(f[9:12]) for f in matching_files if f[9:12].isdigit()]
        next_number = max(numbers) + 1
    else:
        next_number = 1
    
    csv_file_path = os.path.join(csv_dir, f'CSI_DATA_{next_number:03d}.csv')

    try:
        with open(csv_file_path, mode='x', newline='') as file:  # 'x' ensures the file is created and not overwritten
            writer = csv.writer(file)
            writer.writerow(DATASET_COLUMNS)
    except FileExistsError:
        pass

def set_columns():
    global DATASET_COLUMNS, X_TEST_COLUMNS

    DATASET_COLUMNS = ['Transmit_Timestamp', 'Presence', 'Target_Count', 'Angle', 'Distance', 
                       'RSSI', 'Rate', 'MCS', 'Channel', 'Received_Timestamp',
                       'Target1_X', 'Target1_Y', 'Target1_Speed', 'Target1_Resolution', 
                       'Target2_X', 'Target2_Y', 'Target2_Speed', 'Target2_Resolution', 
                       'Target3_X', 'Target3_Y', 'Target3_Speed', 'Target3_Resolution', 'Raw_CSI']

    X_TEST_COLUMNS = [f'Amp_25%_S{i+1}' for i in range(SUBCARRIER_COUNT)]

def check_model():
    global model, pca
    model_path = 'app/model/wriple_v2_(presence).pkl'
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        pca = joblib.load('app/model/wriple_v2_(pca).pkl')
        return 1
    else:
        return 0

def check_connection():
    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, shell=True)
    return SSID in result.stdout

@app.route('/check_system_status', methods=['POST'])
def check_system_status():
    global ap_status, model_status
    ap_status = 1 if check_connection() else 0

    if model is None: model_status = check_model()

    return jsonify({
        'esp32': esp32_status,
        'ap': ap_status,
        'rd03d': rd03d_status,
        'port': port_status,
        'model': model_status
    })

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/start_recording/<mode>', methods=['GET'])
def start_recording(mode):
    global recording, monitoring

    try:
        if mode == 'recording':
            if target_count is None or class_label is None or line_of_sight is None or angle is None or distance_t1 is None:
                raise Exception('Missing or invalid data for recording.')
            
            recording = True
            prepare_csv_file()
            threading.Thread(target=listen_to_packets, daemon=True).start()
            send_packets()
        elif mode == 'monitoring':
            monitoring = True
            threading.Thread(target=listen_to_packets, daemon=True).start()
            send_packets()

        return jsonify({"mode": mode})
    except Exception as e:
        return jsonify({'status': 'error'}), 400

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, monitoring, total_packet_count
    recording = False
    monitoring = False
    total_packet_count = 0
    amplitude_queue.clear()
    phase_queue.clear()
    return 'Stop recording CSI Data.'

@app.route('/visualize_data', methods=['POST'])
def visualize_data():
    try:
        signal_coordinates = filter_amp_phase()
        return jsonify({
            "signalCoordinates": signal_coordinates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_radar_data', methods=['POST'])
def get_radar_data():
    predict_presence()
    try:
        return jsonify({
            'presence': presence_pred,
            'radarX': radar_x_coord, # -13856 ~ +13856
            'radarY': radar_y_coord, # 0 ~ 8000
            'radarSpeed': radar_speed,
            'radarDistRes': radar_dist_res,
            'totalPacket': total_packet_count,
            'rssi': rssi,
            'modeStatus': 0 if recording else 1 if monitoring else -1,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/list_csv_files', methods=['GET'])
def list_csv_files():
    attendance_files = [f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')]
    return jsonify(attendance_files)

@app.route('/visualize_csv_file/<filename>', methods=['GET'])
def visualize_csv_file(filename):
    global csv_file_path, max_monitoring_packets
    csv_file_path = os.path.join(CSV_DIRECTORY, filename)
    max_monitoring_packets = RECORDING_PACKET_LIMIT

    if not os.path.exists(csv_file_path):
        return jsonify({"error": "File not found"}), 404
    else:
        return 'CSV file set for visualization.'

@app.route('/set_recording_data', methods=['POST'])
def set_recording_data():
    global class_label, target_count, line_of_sight, angle, distance_t1
    data = request.get_json()

    try:
        class_label = None
        target_count = None
        line_of_sight = None
        angle = None
        distance_t1 = None

        class_label = int(data.get('presence', 0))
        target_count = int(data.get('target', ''))
        line_of_sight = float(data.get('los', 0.0))
        angle = float(data.get('angle', 0.0))
        distance_t1 = float(data.get('distance', 0.0))
    except Exception as e:
        return jsonify({"status": "error"})

    return jsonify({"status": "success"})

@app.route('/fetch_amplitude_data', methods=['POST'])
def fetch_amplitude_data():
    try:
        if not amplitude_queue:
            return jsonify({"latestAmplitude": []})

        latest_amplitudes = amplitude_queue[-1]
        subcarriers = len(latest_amplitudes)
        amplitude_points = [[x, 0, float(latest_amplitudes[x])] for x in range(subcarriers)]

        return jsonify({
            "latestAmplitude": amplitude_points
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/fetch_phase_data', methods=['POST'])
def fetch_phase_data():
    try:
        if not phase_queue:
            return jsonify({"latestPhase": []})

        latest_phases = phase_queue[-1]
        subcarriers = len(latest_phases)
        phase_points = [[x, 0, float(latest_phases[x])] for x in range(subcarriers)]

        return jsonify({
            "latestPhase": phase_points
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    set_columns()
    app.run(debug=True)
