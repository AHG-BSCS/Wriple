"""File Manager Module"""

import csv
import datetime
import json
import os
import re
import threading

from app.config.settings import FileConfig, NetworkConfig
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
            # os.makedirs(FileConfig.CSV_DIRECTORY, exist_ok=True)
    
    def list_csv_files(self) -> list:
        """
        Retrieve all CSV files in the recording directory

        Returns:
            list: Sorted list of CSV filenames
        """
        try:
            files = os.listdir(FileConfig.CSV_DIRECTORY)
            csv_files = [f for f in files if f.endswith('.csv')]
            return sorted(csv_files)
        except Exception as e:
            self._logger.error(f'Error listing CSV files: {e}')
            return []
    
    def read_csv_file_meta(self, filename: str) -> dict:
        self._selected_csv_file = os.path.join(FileConfig.CSV_DIRECTORY, filename)
        
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
                metadata = self._metadata_to_category(metadata)

                # Count the number of samples
                row_count = sum(1 for _ in reader) + 1 if first_row else 0
                metadata['packet_count'] = row_count
                
                # Calculate the sampling rate based on transmit timestamps
                file.seek(0)
                next(reader)  # Skip header
                timestamps = [float(row['Transmit_Timestamp']) for row in reader]
                metadata['sampling_rate'] = self._compute_sampling_rate(timestamps)
                
                # Convert the transmit timestamp to a readable date
                record_date = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
                metadata['recording_date'] = record_date
                return metadata
        else:
            return None

    def _compute_sampling_rate(self, timestamps):
        if len(timestamps) >= 2:
            time_diffs = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            sampling_rate = 1 / avg_time_diff
            return round(sampling_rate, 2)
        else:
            return 'Missing'
    
    def _metadata_to_category(self, metadata: dict) -> dict:
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
    
    def _get_next_filename(self) -> str:
        """
        Generate the next available CSV filename
        
        Returns:
            str: Full path to the next CSV file
        """
        try:
            files = os.listdir(FileConfig.CSV_DIRECTORY)
            pattern = re.compile(FileConfig.CSV_FILE_PATTERN)
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
            
            filename = f'{FileConfig.CSV_FILE_PREFIX}{next_number:03d}.csv'
            self._logger.info(f'Writing on {filename}.')
            return os.path.join(FileConfig.CSV_DIRECTORY, filename)
            
        except Exception as e:
            self._logger.error(f'Error generating new csv filename: {e}')
            # Fallback filename
            return os.path.join(FileConfig.CSV_DIRECTORY, f'{FileConfig.CSV_FILE_PREFIX}ERROR.csv')
    
    def _init_new_csv(self) -> bool:
        """
        Prepare a new CSV file for recording
        
        Returns:
            bool: True if file was created successfully, False otherwise
        """
        self._csv_file_path = self._get_next_filename()
        
        try:
            # Create file with column names as headers
            with open(self._csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(FileConfig.CSV_COLUMNS)
            
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
                    self._flush_buffer()
            return True
        except Exception as e:
            self._logger.error(f'Error writing to CSV file: {e}')
            return False

    def _flush_buffer(self):
        """Flush buffered data to the CSV file"""
        if not self._csv_buffer:
            return
        
        try:
            self._init_new_csv()
            with open(self._csv_file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(self._csv_buffer)
            self._csv_buffer.clear()
        except Exception as e:
            self._logger.error(f'Error flushing buffer to CSV file: {e}')

    def close(self):
        """Flush any remaining data and close the file manager"""
        with self._lock:
            self._flush_buffer()

    def load_settings(self):
        """Load settings from JSON file and apply relevant values."""
        try:
            with open(FileConfig.SETTING_FILE, mode='r', encoding='utf-8') as file:
                data: dict = json.load(file)
                NetworkConfig.update(NetworkConfig, data['NetworkConfiguration'])
        except Exception as e:
            # os.makedirs(os.path.dirname(FileConfig.SETTING_FILE), exist_ok=True)
            self._logger.error(f'Error loading settings from {FileConfig.SETTING_FILE}: {e}')

    def save_settings(self):
        """Save current settings to JSON file."""
        settings = {
            'NetworkConfiguration': NetworkConfig.to_dict(NetworkConfig)
        }

        tmp_file = FileConfig.SETTING_FILE + '.tmp'
        try:
            # Create temporary file first
            os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
            with open(tmp_file, mode='w', encoding='utf-8') as file:
                json.dump(settings, file, indent=2)
                file.flush()
                os.fsync(file.fileno())

            # Then replace original file
            os.replace(tmp_file, FileConfig.SETTING_FILE)
            self._logger.info(f'Settings saved to {FileConfig.SETTING_FILE}')
        except Exception as e:
            self._logger.error(f'Error saving settings to {FileConfig.SETTING_FILE}: {e}')
