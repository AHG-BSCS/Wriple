import csv
import math
import socket
import subprocess
import threading
import time
from flask import Flask, render_template
from scapy.all import datetime

app = Flask(__name__)
lock = threading.Lock()

SSID = 'Wiremap'
PASSWORD = 'WiReMap@ESP32'
ESP32_IP = '192.168.4.1' # Default IP address of the ESP32 AP
# PAYLOAD = 'Wiremap' # For future purposes
# ESP32_PORT = 5001 # For future purposes

listening = False
total_packet_count = 0
packet_count = 0

CSV_FILE = 'webapp/dataset/csi_data.csv'
COLUMN_NAMES = [
    'Recording_Timestamp', 'Type', 'Mode', 'Source_IP', 'RSSI', 'Rate', 'Sig_Mode', 'MCS', 'CWB', 'Smoothing', 
    'Not_Sounding', 'Aggregation', 'STBC', 'FEC_Coding', 'SGI', 'Noise_Floor', 'AMPDU_Cnt', 
    'Channel', 'Secondary_Channel', 'Received_Timestamp', 'Antenna', 'Signal_Length', 'RX_State', 
    'Real_Time_Set', 'Steady_Clock_Timestamp', 'Data_Length', 'CSI_Data', 'CSI_Amplitude', 'CSI_Phase'
]

def check_connection(ssid):
    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, shell=True)
    return ssid in result.stdout

def initialize_csv():
    try:
        with open(CSV_FILE, mode='x', newline='') as file:  # 'x' ensures the file is created and not overwritten
            writer = csv.writer(file)
            writer.writerow(COLUMN_NAMES)
    except FileExistsError:
        pass

def compute_csi_amplitude_phase(csi_data):
    # Compute amplitude and phase from raw CSI data.
    # param csi_data: List of raw CSI values (alternating I and Q components).
    # return: Two lists - amplitudes and phases for each subcarrier.
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

def listen_for_packets():
    global listening, packet_count
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(('0.0.0.0', 5000))

    print('Recording CSI data...')
    while listening:
        data, addr = client.recvfrom(2048) # Adjusted buffer size for CSI Data
        packet_count += 1
        received_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        threading.Thread(target=process_data, args=(data, received_time)).start()

def process_data(data, received_time):
    try:
        data_str = data.decode('utf-8').strip()
        row = parse_csi_data(data_str)
        row.insert(0, received_time)

        # Write to the CSV file with a lock to ensure thread safety
        with lock:
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(row)
    except Exception as e:
        print(f'Error processing data: {e}')

def packet_counter():
    global total_packet_count, packet_count
    total_packet_count += packet_count

    if (listening):
        print('Packets received in 1s:', packet_count)
        packet_count = 0 # Reset the packet counter
        print('Total packets received:', total_packet_count)
        threading.Timer(1.0, packet_counter).start()
    else:
        total_packet_count = 0
        packet_count = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_recording', methods=['POST'])
def start_csi():
    global listening
    listening = True
    threading.Thread(target=listen_for_packets, daemon=True).start()
    packet_counter()
    return 'Start recording CSI Data.'

@app.route('/stop_recording', methods=['POST'])
def stop_csi():
    global listening
    listening = False
    return 'Stop recording CSI Data.'

if __name__ == '__main__':
    # Check if the device is connected to the ESP32 AP
    while not check_connection(SSID):
        print('Waiting to connect to ESP32 AP')
        print('SSID:', SSID)
        print('Passord:', PASSWORD, '\n')
        time.sleep(5)

    print(f'Connected to {SSID}. Starting the server...')
    initialize_csv()
    app.run(debug=True)
    