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
packet_count = 0
max_packets = 25
tx_interval = 0.1
threshold = 2

# csv_file_path = None
csv_file_path = None
sending_timestamp = []
amplitude = []
phase = []
COLUMN_NAMES = [
    'Transmit_Timestamp', 'Record_Timestamp', 'Type', 'Mode', 'Source_IP', 'RSSI', 'Rate', 'Sig_Mode', 'MCS', 'CWB', 'Smoothing', 
    'Not_Sounding', 'Aggregation', 'STBC', 'FEC_Coding', 'SGI', 'Noise_Floor', 'AMPDU_Cnt', 
    'Channel', 'Secondary_Channel', 'Received_Timestamp', 'Antenna', 'Signal_Length', 'RX_State', 
    'Real_Time_Set', 'Steady_Clock_Timestamp', 'Data_Length', 'Raw_CSI', 'Amplitude', 'Phase', 'Time_of_Flight'
]

def clean_and_filter_data(amplitudes, phases, amp_lower_threshold, amp_upper_threshold, 
                          phase_lower_threshold, phase_upper_threshold):
    cleaned_amplitudes = []
    cleaned_phases = []
    subcarriers = range(len(amplitudes))

    for i, amp, phase in zip(subcarriers, amplitudes, phases):
        # Remove null subcarriers
        if amp == 0: continue
        
        # # Retain outliers based on amplitude
        # if (amp < amp_lower_threshold[i]) or (amp > amp_upper_threshold[i]):
        #     cleaned_amplitudes.append(amp)
        #     cleaned_phases.append(phase)

        # # Retain outliers based on phase
        # if (phase < phase_lower_threshold[i]) or (phase > phase_upper_threshold[i]):
        #     cleaned_amplitudes.append(amp)
        #     cleaned_phases.append(phase)
        
        # Retain outliers based on amplitude and phase
        if ((amp < amp_lower_threshold[i]) or (amp > amp_upper_threshold[i]) and (phase < phase_lower_threshold[i]) or (phase > phase_upper_threshold[i])):
            cleaned_amplitudes.append(amp)
            cleaned_phases.append(phase)
        else:
            cleaned_amplitudes.append(0)
            cleaned_phases.append(0)

    return cleaned_amplitudes, cleaned_phases

def apply_wavelet_transform(csi_amplitude, csi_phase):
    transformed_amplitudes, transformed_phases = [], []

    for i in range(len(csi_amplitude)):
        csi_data = [a * np.exp(1j * p) for a, p in zip(csi_amplitude[i], csi_phase[i])]
        csi_data = pywt.swt(csi_data, 'db1', level=1)
        csi_data = pywt.iswt(csi_data, 'db1')

        # Separate amplitude and phase
        transformed_amplitudes.append(np.abs(csi_data))
        transformed_phases.append(np.angle(csi_data))
    
    return transformed_amplitudes, transformed_phases

def get_subcarrier_threshold(data_transposed):
    lower_threshold, upper_threshold = [], []

    for column in data_transposed:
        mean = np.mean(column)
        std_dev = np.std(column)

        lower_threshold.append(mean - threshold * std_dev)
        upper_threshold.append(mean + threshold * std_dev)

    return lower_threshold, upper_threshold

def filter_amp_phase():
    scaler = MinMaxScaler((-10, 10))
    filtered_positions = []

    try:
        # Convert string list to actual list
        csi_df = pd.read_csv(csv_file_path)
        csi_amplitude = csi_df['Amplitude'].apply(eval)  
        csi_phase = csi_df['Phase'].apply(eval)
    except KeyError:
        print("Error: 'Amplitude' or 'Phase' column not found in the file.")
        return

    amps_transposed = list(map(list, zip(*csi_amplitude)))
    phases_transposed = list(map(list, zip(*csi_phase)))

    scaled_amplitudes = scaler.fit_transform(amps_transposed).T
    scaled_phases = scaler.fit_transform(phases_transposed).T

    amp_lower_threshold, amp_upper_threshold = get_subcarrier_threshold(scaled_amplitudes.T)
    phase_lower_threshold, phase_upper_threshold = get_subcarrier_threshold(scaled_phases.T)

    # csi_amplitude, csi_phase = apply_wavelet_transform(csi_amplitude, csi_phase)
    
    for amp, phase in zip(scaled_amplitudes, scaled_phases):
        amp = np.array(amp)
        phase = np.array(phase)

        cleaned_amplitudes, cleaned_phases = clean_and_filter_data(
            amp[5:], phase[5:], 
            amp_lower_threshold[5:], amp_upper_threshold[5:], 
            phase_lower_threshold[5:], phase_upper_threshold[5:]
        )

        # This loop ensures that each subcarrier is plot in the same x-axis
        x = np.arange(-10, 10, 20/len(cleaned_amplitudes))
        z = cleaned_phases
        y = cleaned_amplitudes

        for i in range(len(x)):
            filtered_positions.append((float(x[i]), float(y[i]), float(z[i])))
    
    filtered_positions
    return filtered_positions


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
        phase = math.atan2(Q, I)  # atan2 handles quadrant ambiguity
        
        amplitudes.append(amplitude)
        phases.append(phase)
    
    return amplitudes, phases

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

            # Write to the CSV file with a lock to ensure thread safety
            with lock:
                with open(csv_file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(csi_data)
        else:
            global amplitude, phase
            amplitude.append(csi_data[-2])
            phase.append(csi_data[-1])
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

    if mode == 0:
        compute_time_of_flight()
        
    recording = False
    monitoring = False
    
    print('Stopped recording CSI data.')

def send_packets():
    try:
        if monitoring:
            send(UDP_PACKET)
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

    if mode == 'recording':
        recording = True
        prepare_csv_file()
        threading.Thread(target=listen_to_packets, daemon=True).start()
        send_packets()
    elif mode == 'monitoring':
        monitoring = True
        threading.Thread(target=listen_to_packets, daemon=True).start()
        send_packets()

    return f'Start {mode} CSI Data.'

@app.route('/recording_status', methods=['POST'])
def recording_status():
    return jsonify({
        'mode': 0 if recording else 1 if monitoring else -1,
        'total_packet': total_packet_count
    })

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, monitoring
    recording = False
    monitoring = False
    return 'Stop recording CSI Data.'

@app.route('/visualize', methods=['POST'])
def visualize_amp_phase():
    if not os.path.exists(csv_file_path):
        return jsonify({"error": "No CSV file found"}), 404
    
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

if __name__ == '__main__':
    # Check if the device is connected to the ESP32 AP
    while not check_connection(SSID):
        print('Waiting to connect to ESP32 AP')
        print('SSID:', SSID)
        print('Passord:', PASSWORD, '\n')
        time.sleep(5)
    else:
        print(f'Connected to {SSID}. Starting the server...')
    
    app.run(host='0.0.0.0', port=3000, debug=True)
    