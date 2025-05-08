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
from sklearn.preprocessing import MinMaxScaler
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
CSV_DIRECTORY = 'app/dataset/data_recorded'
DATASET_COLUMNS = []
FEATURES_COLUMNS = []

MM_SCALER = MinMaxScaler((-10, 10))
WINDOW_RANGE = [(0, 10), (10, -1)]
WINDOW_SIZE = 35
# SUBCARRIER_COUNT = 57
# SMOOTH_SUBCARRIER_COUNT = int(57 / (WINDOW_SIZE * 0.1))
SMOOTH_SUBCARRIER_COUNT = 23 # TODO: The value was estimated based on missing columns. Find the correct calculation.
# START_SUBCARRIER = 132
# END_SUBCARRIER = 246
START_SUBCARRIER = 70
END_SUBCARRIER = 368
PREPROCESS = True

recording = False
monitoring = False
total_packet_count = 0
max_monitoring_packets = MONITORING_PACKET_LIMIT

transmit_timestamp = []
amplitude_queue = []
phase_queue = []
radar_x_coord = [0, 0, 0]
radar_y_coord = [0, 0, 0]
radar_speed = [0, 0, 0]
radar_dist_res = [0, 0, 0]
rssi = 0

model = None
prediction = None
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

def aggregate_amps_features(data):
    features = []
    features.extend(np.std(data, axis=0))
    return np.array(features)

def aggregate_phases_features(data):
    features = []
    features.extend(np.std(data, axis=0))
    features.extend(np.percentile(data, 75, axis=0))
    features.extend(np.var(data, axis=0))
    return np.array(features)

def get_subcarrier_threshold(data_transposed):
    lower_threshold, upper_threshold = [], []

    for column in data_transposed:
        mean = np.mean(column)
        std_dev = np.std(column)

        lower_threshold.append(mean - std_threshold * std_dev)
        upper_threshold.append(mean + std_threshold * std_dev)

    return lower_threshold, upper_threshold

def filter_amp_phase():
    global max_monitoring_packets, prediction
    signal_coordinates = []

    # Load the data if file was selected for visualization
    if max_monitoring_packets == RECORDING_PACKET_LIMIT:
        try:
            csi_df = pd.read_csv(csv_file_path)
            raw_csi = csi_df['Raw_CSI'].apply(eval)

            for csi_data in raw_csi:
                compute_csi_amplitude_phase(csi_data[START_SUBCARRIER:END_SUBCARRIER])
        except Exception as e:
            print("Error: 'Amplitude' or 'Phase' column not found in the file.", e)
            return
    
    if len(amplitude_queue) < RECORDING_PACKET_LIMIT:
        return

    csi_amplitude = pd.Series(amplitude_queue)
    csi_phase = pd.Series(phase_queue)
    
    if model:
        amps_features = [aggregate_amps_features(amplitude_queue[start:end]) for start, end in WINDOW_RANGE]
        phases_features = [aggregate_phases_features(phase_queue[start:end]) for start, end in WINDOW_RANGE]

        rows = []

        for amp_features, phase_features in zip(amps_features, phases_features):
            row = np.concatenate([amp_features, phase_features])
            rows.append(row)

        X_test = pd.DataFrame(rows, columns=FEATURES_COLUMNS)
        predictions = model.predict(X_test)
        prediction = 0 if 0 in predictions else 1

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

def compute_csi_amplitude_phase(csi_data):
    '''
    Compute amplitude and phase from raw CSI data.
    param csi_data: List of raw CSI values (alternating I and Q components).
    return: Two lists - amplitudes and phases for each subcarrier.
    '''
    amplitudes = []
    phases = []
    
    # Ensure the data length is even (pairs of I and Q)
    if len(csi_data) % 2 != 0:
        raise ValueError('CSI data length must be even (pairs of I and Q values).')
    
    for i in range(0, len(csi_data), 2):
        I = csi_data[i]
        Q = csi_data[i + 1]
        
        amplitude = math.sqrt(I**2 + Q**2)
        phase = math.atan2(Q, I)
        
        amplitudes.append(amplitude)
        phases.append(phase)
    
    if PREPROCESS:
        # Use phase unwrapping to prevent discontinuities in phase
        phases = np.unwrap(phases)

        # Compute moving average of the last 100 packets
        amplitudes = np.convolve(amplitudes, np.ones(WINDOW_SIZE) / WINDOW_SIZE, mode='valid')
        phases = np.convolve(phases, np.ones(WINDOW_SIZE) / WINDOW_SIZE, mode='valid')
    
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
    csi_data = data_str[csi_data_start + 1:csi_data_end].strip().split(' ')
    csi_data = list(filter(None, csi_data))  # Remove empty strings
    
    try:
        csi_data = [int(x) for x in csi_data]
        if monitoring:
            compute_csi_amplitude_phase(csi_data[START_SUBCARRIER:END_SUBCARRIER])
    except ValueError:
        csi_data = []

    # Use -1 to exclude the unformatted Raw CSI data
    return parts[:-1] + [csi_data]

def compute_time_of_flight():
    '''
    Compute time of flight for each CSI data row.
    This is currectly not accurate and needs to be improved.
    '''
    tx_delay = TX_INTERVAL * 1_000_000
    tof_list = []
    csi_df = pd.read_csv(csv_file_path)

    for i in range(1, len(csi_df)):
        previous_row = csi_df.iloc[i - 1]
        current_row = csi_df.iloc[i]

        prev_tx_time = previous_row['Transmit_Timestamp']
        curr_tx_time = current_row['Transmit_Timestamp']
        prev_rx_time = previous_row['Received_Timestamp']
        curr_rx_time = current_row['Received_Timestamp']

        # Calculate the difference in microseconds
        tx_offset = curr_tx_time - prev_tx_time
        rx_offset = curr_rx_time - prev_rx_time

        # Subtract the time in takes to transmit to the time of receiving
        adjust_rx_time = curr_rx_time - tx_offset

        # Calculate the difference in received times
        tof = prev_rx_time - adjust_rx_time
        tof_seconds = tof / 1_000_000
        tof_list.append(tof_seconds)

    # Note: The first row will not have a ToF value
    csi_df['Time_of_Flight'] = [float('nan')] + tof_list
    csi_df.to_csv(csv_file_path, index=False)
    return csi_df

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
    global DATASET_COLUMNS, FEATURES_COLUMNS

    DATASET_COLUMNS = ['Transmit_Timestamp', 'Presence', 'Target_Count', 'Angle', 'Distance', 
                       'RSSI', 'Rate', 'MCS', 'Channel', 'Received_Timestamp',
                       'Target1_X', 'Target1_Y', 'Target1_Speed', 'Target1_Resolution', 
                       'Target2_X', 'Target2_Y', 'Target2_Speed', 'Target2_Resolution', 
                       'Target3_X', 'Target3_Y', 'Target3_Speed', 'Target3_Resolution', 'Raw_CSI']

    FEATURES_COLUMNS = [f'AM_Std{i + 1}' for i in range(SMOOTH_SUBCARRIER_COUNT)] + \
                       [f'PH_Std{i + 1}' for i in range(SMOOTH_SUBCARRIER_COUNT)] + \
                       [f'PH_Per{i + 1}' for i in range(SMOOTH_SUBCARRIER_COUNT)] + \
                       [f'PH_Var{i + 1}' for i in range(SMOOTH_SUBCARRIER_COUNT)]

def check_model():
    global model
    model_path = 'app/model/no_model.pkl'
    if os.path.exists(model_path):
        model = joblib.load(model_path)
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
    global recording, monitoring, prediction
    prediction = None

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
            "prediction": prediction,
            "signalCoordinates": signal_coordinates,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_radar_data', methods=['POST'])
def get_radar_data():
    try:
        return jsonify({
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
    app.run(debug=True)
