import os
import re
import csv
import math
import numpy as np
import pandas as pd
import pywt
import socket
import subprocess
import time
import threading
from sklearn.preprocessing import MinMaxScaler
from scapy.all import Raw, IP, UDP, send
from scipy.signal import butter, filtfilt
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)
lock = threading.Lock()

SSID = 'Wiremap'
PASSWORD = 'WiReMap@ESP32'
ESP32_IP = '192.168.4.1' # Default IP address of the ESP32 AP
PAYLOAD = 'Wiremap' # Signal Length is 89
ESP32_PORT = 5001
UDP_PACKET = IP(dst=ESP32_IP)/UDP(sport=5000, dport=ESP32_PORT)/Raw(load=PAYLOAD)

recording = False
monitoring = False
total_packet_count = 0
max_packets = 200
max_monitoring_packets = 100
tx_interval = 0.01

scaler = MinMaxScaler((-10, 10))
std_threshold = 1.75
cutoff_frequency = 0.1
sampling_rate = 1.0

csv_file_path = None
sending_timestamp = []
amplitude_queue = pd.Series(dtype='object')
phase_queue = pd.Series(dtype='object')
activity = None
class_label = None
COLUMN_NAMES = [
    'Transmit_Timestamp', 'Record_Timestamp', 'Type', 'Mode', 'Activity', 'Movement', 'Source_IP', 'RSSI', 'Rate', 'Sig_Mode', 'MCS', 'CWB', 'Smoothing', 
    'Not_Sounding', 'Aggregation', 'STBC', 'FEC_Coding', 'SGI', 'Noise_Floor', 'AMPDU_Cnt', 
    'Channel', 'Secondary_Channel', 'Received_Timestamp', 'Antenna', 'Signal_Length', 'RX_State', 
    'Real_Time_Set', 'Steady_Clock_Timestamp', 'Data_Length', 'Raw_CSI', 'Amplitude', 'Phase', 'Time_of_Flight'
]

def clean_and_filter_data(amplitudes, phases, amp_lower_threshold, amp_upper_threshold, 
                          phase_lower_threshold, phase_upper_threshold):
    cleaned_amplitudes = []
    cleaned_phases = []
    subcarriers = range(len(amplitudes))

    # Retain outliers based on amplitude and phase
    for i, amp, phase in zip(subcarriers, amplitudes, phases):
        if ((amp < amp_lower_threshold[i]) or (amp > amp_upper_threshold[i]) and (phase < phase_lower_threshold[i]) or (phase > phase_upper_threshold[i])):
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

def butter_highpass(order=5):
    nyquist = 0.5 * sampling_rate
    normal_cutoff = cutoff_frequency / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def highpass_filter(data):
    b, a = butter_highpass()
    y = filtfilt(b, a, data)
    return y

def filter_amp_phase():
    filtered_positions = []

    if monitoring:
        csi_amplitude = amplitude_queue
        csi_phase = phase_queue
    else:
        try:
            csi_df = pd.read_csv(csv_file_path)
            csi_amplitude = csi_df['Amplitude'].apply(eval)
            csi_phase = csi_df['Phase'].apply(eval)
        except KeyError:
            print("Error: 'Amplitude' or 'Phase' column not found in the file.")
            return

    # Apply high-pass filter to amplitude and phase data
    # csi_amplitude = csi_amplitude.apply(lambda x: highpass_filter(np.array(x)))
    # csi_phase = csi_phase.apply(lambda x: highpass_filter(np.array(x)))

    # Transpose to make subcarriers as rows
    amps_transposed = list(map(list, zip(*csi_amplitude)))
    phases_transposed = list(map(list, zip(*csi_phase)))

    # Limit the number of subcarriers to plot for the most relevant ones
    # amplitudes[64:65] + amplitudes[66:123] + amplitudes[127:184] + amplitudes[185:186]
    # amps_transposed = amps_transposed[54:166]
    # phases_transposed = phases_transposed[53:166]
    # amps_transposed = amps_transposed[:53]
    # phases_transposed = phases_transposed[:53]

    # Scaled because of d3 visualization
    scaled_amplitudes = scaler.fit_transform(amps_transposed).T
    scaled_phases = scaler.fit_transform(phases_transposed).T

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
            filtered_positions.append((float(x[i]), float(y[i]), float(z[i])))
    
    return filtered_positions

def compute_csi_amplitude_phase(csi_data):
    '''
    Compute amplitude and phase from raw CSI data.
    param csi_data: List of raw CSI values (alternating I and Q components).
    return: Two lists - amplitudes and phases for each subcarrier.
    '''
    global amplitude_queue, phase_queue
    amplitudes = []
    phases = []
    
    # Ensure the data length is even (pairs of I and Q)
    if len(csi_data) % 2 != 0:
        raise ValueError('CSI data length must be even (pairs of I and Q values).')
    
    for i in range(0, len(csi_data), 2):
        I = csi_data[i]
        Q = csi_data[i + 1]
        
        amplitude = math.sqrt(I**2 + Q**2)
        phase = math.atan2(Q, I)  # atan2 handles quadrant ambiguity
        
        amplitudes.append(amplitude)
        phases.append(phase)
    
    # Specifically choosen ranges of subcarrier for accuracy
    filtered_amplitude = amplitudes[6:32] + amplitudes[33:59] + amplitudes[64:65] + amplitudes[66:123] + amplitudes[127:184] + amplitudes[185:186] + amplitudes[187:244] + amplitudes[248:305]
    filtered_phase = phases[6:32] + phases[33:59] + phases[64:65] + phases[66:123] + phases[127:184] + phases[185:186] + phases[187:244] + phases[248:305]

    if monitoring:
        if len(amplitude_queue) >= max_monitoring_packets:
            amplitude_queue = amplitude_queue.iloc[1:].reset_index(drop=True)
            phase_queue = phase_queue.iloc[1:].reset_index(drop=True)

        amplitude_queue = pd.concat([amplitude_queue, pd.Series([filtered_amplitude])], ignore_index=True)
        phase_queue = pd.concat([phase_queue, pd.Series([filtered_phase])], ignore_index=True)
    
    return filtered_amplitude, filtered_phase

def parse_csi_data(data_str):
    parts = data_str.split(',')
    csi_data_start = data_str.find('[')
    csi_data_end = data_str.find(']')

    # Extract CSI data as a string of integers
    csi_data = data_str[csi_data_start + 1:csi_data_end].strip().split(' ')
    csi_data = list(filter(None, csi_data))  # Remove empty strings

    try:
        csi_data = [int(x) for x in csi_data]
        amplitudes, phases = compute_csi_amplitude_phase(csi_data)
    except ValueError:
        csi_data, amplitudes, phases = [], [], []

    return parts[:25] + [csi_data, amplitudes, phases]

def compute_time_of_flight():
    '''
    Compute time of flight for each CSI data row.
    This is currectly not accurate and needs to be improved.
    '''
    tx_delay = tx_interval * 1_000_000
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

def process_data(data, rx_time):
    try:
        data_str = data.decode('utf-8').strip()
        csi_data = parse_csi_data(data_str)
        if (recording):
            csi_data.insert(0, sending_timestamp.pop(0))
            csi_data.insert(1, rx_time)
            csi_data.insert(4, activity)
            csi_data.insert(5, class_label)

            # Write to the CSV file with a lock to ensure thread safety
            with lock:
                with open(csv_file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(csi_data)
    except Exception as e:
        print(f'Error processing data: {e}')
    
def listen_to_packets():
    global recording, monitoring, total_packet_count
    mode = 0 if recording else 1
    packet_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    packet_listener.bind(('0.0.0.0', 5000))
    packet_listener.settimeout(1.0)

    print('Recording CSI data...')
    while recording or monitoring:
        try:
            data, addr = packet_listener.recvfrom(2048) # Adjusted buffer size for CSI Data
            if monitoring:
                total_packet_count += 1
                threading.Thread(target=process_data, args=(data, None)).start()
                continue

            total_packet_count += 1
            rx_time = time.time()
            rx_time = int((rx_time * 1_000_000) % 1_000_000_000)

            if total_packet_count <= max_packets:
                threading.Thread(target=process_data, args=(data, rx_time)).start()
            else:
                total_packet_count = 0
                break
        except socket.timeout:
            if not recording and not monitoring:
                break
            else:
                continue
        except KeyboardInterrupt:
            break
        except Exception:
            print('Packet size is larger than buffer size. Restarting...')
            continue

    if mode == 0:
        compute_time_of_flight()
        
    recording = False
    monitoring = False
    
    print('Stopped recording CSI data.')

def send_packets():
    try:
        if monitoring:
            send(UDP_PACKET, verbose=False)
            threading.Timer(tx_interval, send_packets).start()
        elif recording and not monitoring and total_packet_count <= max_packets:
            # Get the sending timestamp as accurate as possible
            send(UDP_PACKET)
            tx_time = time.time()
            tx_time = int((tx_time * 1_000_000) % 1_000_000_000)
            sending_timestamp.append(tx_time)
            threading.Timer(tx_interval, send_packets).start()
        else:
            print('Stopped sending packets.')
    except KeyboardInterrupt:
        pass

def prepare_csv_file():
    global csv_file_path
    csv_dir = 'app/dataset'
    files = os.listdir(csv_dir)
    
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
            writer.writerow(COLUMN_NAMES)
    except FileExistsError:
        pass

def check_connection(ssid):
    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, shell=True)
    return ssid in result.stdout


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/start_recording/<mode>', methods=['GET'])
def start_recording(mode):
    global recording, monitoring
    try:
        if mode == 'recording':
            if activity is None or class_label is None:
                raise Exception('Activity and Class is missing!')
            
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

@app.route('/recording_status', methods=['POST'])
def recording_status():
    return jsonify({
        'mode': 0 if recording else 1 if monitoring else -1,
        'total_packet': total_packet_count
    })

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, monitoring, total_packet_count
    recording = False
    monitoring = False
    total_packet_count = 0
    return 'Stop recording CSI Data.'

@app.route('/visualize', methods=['POST'])
def visualize_amp_phase():
    try:
        filtered_signal = filter_amp_phase()
        return jsonify({"filtered_signal": filtered_signal})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/list_csv_files', methods=['GET'])
def list_attendance_files():
    attendance_files = [f for f in os.listdir('app/dataset') if f.endswith('.csv')]
    return jsonify(attendance_files)

@app.route('/visualize_csv/<filename>', methods=['GET'])
def visualize_csv(filename):
    global csv_file_path
    csv_file_path = os.path.join('app/dataset', filename)

    if not os.path.exists(csv_file_path):
        return jsonify({"error": "File not found"}), 404
    return 'CSV file set for visualization.'

@app.route('/set_activity/<act>', methods=['GET'])
def set_activity(act):
    global activity
    if act != 'None':
        activity = act
    else:
        activity = None
    return f'set {act} as activity.'

@app.route('/set_class/<target_class>', methods=['GET'])
def set_class(target_class):
    global class_label
    if target_class != 'None':
        class_label = int(target_class)
    else:
        class_label = None
    return f'set {target_class} as target class.'

@app.route('/set_threshold/<threshold>', methods=['GET'])
def set_threshold(threshold):
    global std_threshold
    std_threshold = float(threshold)
    return f'set {threshold} as threshold.'

if __name__ == '__main__':
    # Ensure that the device is connectted to ESP32 AP since starting disconnected can cause packet sending error.
    while not check_connection(SSID):
        print('Waiting to connect to ESP32 AP')
        print('SSID:', SSID)
        print('Passord:', PASSWORD, '\n')
        time.sleep(5)
    else:
        print(f'Connected to {SSID}. Starting the server...')
    
    app.run(host='0.0.0.0', port=3000, debug=True)
    