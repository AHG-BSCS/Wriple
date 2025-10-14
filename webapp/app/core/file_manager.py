"""File Manager Module"""

import csv
import datetime
import json
import os
import re
import threading

from app.config.settings import FileConfiguration
from app.config.settings import NetworkConfig
from app.utils.logger import setup_logger


class FileManager:
    """Handles CSV file CRUD operations and management"""

    def __init__(self):
            self._csv_file_path = None
            self._selected_csv_file = None
            self._csv_buffer = []
            self._lock = threading.Lock()
            self._logger = setup_logger('FileManager')
            
            # Ensure directory exists
            os.makedirs(FileConfiguration.CSV_DIRECTORY, exist_ok=True)
    
    def get_next_filename(self) -> str:
        """
        Generate the next available CSV filename
        
        Returns:
            str: Full path to the next CSV file
        """
        try:
            files = os.listdir(FileConfiguration.CSV_DIRECTORY)
            pattern = re.compile(FileConfiguration.CSV_FILE_PATTERN)
            matching_files = [f for f in files if pattern.match(f)]
            
            if matching_files:
                # Extract numeric parts and find the highest number
                numbers = []
                for f in matching_files:
                    match = re.search(r'(\d+)', f)
                    if match:
                        numbers.append(int(match.group(1)))
                
                next_number = max(numbers) + 1 if numbers else 1
            else:
                next_number = 1
            
            filename = f'{FileConfiguration.CSV_FILE_PREFIX}{next_number:03d}.csv'
            self._logger.info(f'Writing on {filename}.')
            return os.path.join(FileConfiguration.CSV_DIRECTORY, filename)
            
        except Exception as e:
            self._logger.error(f'Error generating new csv filename: {e}')
            # Fallback filename
            return os.path.join(FileConfiguration.CSV_DIRECTORY, f'{FileConfiguration.CSV_FILE_PREFIX}ERROR.csv')
    
    def list_csv_files(self) -> list:
        """
        Retrieve all CSV files in the recording directory

        Returns:
            list: Sorted list of CSV filenames
        """
        try:
            files = os.listdir(FileConfiguration.CSV_DIRECTORY)
            csv_files = [f for f in files if f.endswith('.csv')]
            return sorted(csv_files)
        except Exception as e:
            self._logger.error(f'Error listing CSV files: {e}')
            return []
    
    def read_csv_file_meta(self, filename: str) -> dict:
        self._selected_csv_file = os.path.join(FileConfiguration.CSV_DIRECTORY, filename)
        
        self._logger.info(f'{filename} was selected')
        if os.path.exists(self._selected_csv_file):
            self._logger.info(f'{filename} was selected')
            with open(self._selected_csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)

                # Check if required headers exist
                headers = ['Presence', 'Activity', 'Angle', 'Distance', 'Obstruction']
                for header in headers:
                    if header not in reader.fieldnames:
                        self._logger.error(f'Missing required header: {header}')
                        return None
                
                # Read first data row for metadata
                first_row = next(reader, None)
                metadata = {key: first_row[key] for key in headers if key in first_row}
                metadata = self.convert_metadata_to_category(metadata)

                # Count the number of samples
                row_count = sum(1 for _ in reader) + 1 if first_row else 0
                metadata['packet_count'] = row_count
                
                # Calculate the sampling rate based on transmit timestamps
                file.seek(0)
                next(reader)  # Skip header
                timestamps = [float(row['Transmit_Timestamp']) for row in reader]
                metadata['sampling_rate'] = self.compute_sampling_rate(timestamps)
                
                # Convert the transmit timestamp to a readable date
                record_date = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
                metadata['recording_date'] = record_date
                return metadata
        else:
            return None

    def compute_sampling_rate(self, timestamps):
        if len(timestamps) >= 2:
            time_diffs = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            sampling_rate = 1 / avg_time_diff
            return round(sampling_rate, 2)
        else:
            return 'Missing'
    
    def convert_metadata_to_category(self, metadata: dict) -> dict:
        """Convert metadata string values to numerical categories"""
        category_map = {
            # 'Presence': {'No': '0', 'Yes': '1'},
            # 'Activity': {'N/A': '0', 'Stand': '1', 'Sit': '2', 'Walking': '3', 'Running': '4'},
            # 'Angle': {'N/A': '0', '-60° to -21°': '1', '-20° to -6°': '2', '-5° to +5°': '3', '+6° to +20°': '4', '+21° to +60°': '5'},
            # 'Obstruction': {'None': '0', 'Concrete': '1', 'Wood': '2', 'Metal': '3'}
            'Presence': {'0': 'No', '1': 'Yes'},
            'Activity': {'0': 'N/A', '1': 'Stand', '2': 'Sit', '3': 'Walking', '4': 'Running'},
            'Angle': {'0': 'N/A', '1': '-60° to -21°', '2': '-20° to -6°', '3': '-5° to +5°', '4': '+6° to +20°', '5': '+21° to +60°'},
            'Obstruction': {'0': 'None', '1': 'Concrete', '2': 'Wood', '3': 'Metal'}
        }
        
        categorized = {}
        for key, value in metadata.items():
            if key in category_map and value in category_map[key]:
                categorized[key] = category_map[key][value]
            elif key == 'Distance':
                categorized[key] = value + 'm' if value != '0' else 'N/A'
            else:
                print(type(value))
                self._logger.warning(f'Unknown metadata field or value: {key}={value}')
        
        return categorized
    
    def init_new_csv(self) -> bool:
        """
        Prepare a new CSV file for recording
        
        Returns:
            bool: True if file was created successfully, False otherwise
        """
        self._csv_file_path = self.get_next_filename()
        
        try:
            # Create file with column names as headers
            with open(self._csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(FileConfiguration.CSV_COLUMNS)
            
            return True
        except Exception as e:
            self._logger.error(f'Error creating CSV file: {e}')
            self._csv_file_path = None
            return False
    
    def write_data(self, data_row: list) -> bool:
        """
        Write a data row to the CSV file
        
        Args:
            data_row: List of data values to write

        Returns: 
            bool: True if write was successful, False otherwise
        """
        try:
            with self._lock:
                self._csv_buffer.append(data_row)
                if len(self._csv_buffer) >= NetworkConfig.RECORD_PACKET_LIMIT:
                    self.flush_buffer()
            return True
        except Exception as e:
            self._logger.error(f'Error writing to CSV file: {e}')
            return False

    def flush_buffer(self):
        if not self._csv_buffer:
            return
        
        try:
            self.init_new_csv()
            with open(self._csv_file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(self._csv_buffer)
            self._csv_buffer.clear()
        except Exception as e:
            self._logger.error(f'Error flushing buffer to CSV file: {e}')

    def close(self):
        with self._lock:
            self.flush_buffer()

    def load_settings(self):
        """Load settings from JSON file and apply relevant values."""
        try:
            with open(FileConfiguration.SETTING_FILE, mode='r', encoding='utf-8') as file:
                data: dict = json.load(file)
                NetworkConfig.update(NetworkConfig, data['NetworkConfiguration'])
        except Exception as e:
            self._logger.error(f'Error loading settings from {FileConfiguration.SETTING_FILE}: {e}')
            # Manually set the default values
            NetworkConfig.AP_SSID = 'WRIPLE'
            NetworkConfig.AP_PASSWORD = 'WRIPLE_ESP32'
            NetworkConfig.AP_BROADCAST_IP = None
            NetworkConfig.TX_ESP32_IP = None
            NetworkConfig.TX_PORT = 5001
            NetworkConfig.TX_INTERVAL = 0.016
            NetworkConfig.RECORD_PACKET_LIMIT = 250

    def save_settings(self):
        """Save current settings to JSON file."""
        settings = {
            'NetworkConfiguration': NetworkConfig.to_dict(NetworkConfig)
        }

        tmp_file = FileConfiguration.SETTING_FILE + '.tmp'
        try:
            # Create temporary file first
            os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
            with open(tmp_file, mode='w', encoding='utf-8') as file:
                json.dump(settings, file, indent=2)
                file.flush()
                os.fsync(file.fileno())

            # Then replace original file
            os.replace(tmp_file, FileConfiguration.SETTING_FILE)
            self._logger.info(f'Settings saved to {FileConfiguration.SETTING_FILE}')
        except Exception as e:
            self._logger.error(f'Error saving settings to {FileConfiguration.SETTING_FILE}: {e}')
