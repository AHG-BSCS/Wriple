"""File Manager Module"""

import csv
import json
import os
import re
import threading

from config.settings import FileConfiguration
from config.settings import NetworkConfig
from utils.logger import setup_logger


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
    
    def select_csv_file(self, filename: str) -> bool:
        """
        Set the file to be used for visualization

        Args:
            filename: Name of the CSV file to select

        Returns:
            bool: True if file exists and is selected, False otherwise
        """
        self._selected_csv_file = os.path.join(FileConfiguration.CSV_DIRECTORY, filename)
        
        if os.path.exists(self._selected_csv_file):
            self._logger.info(f'{filename} is selected for visualization')
            return True
        else:
            self._selected_csv_file = None
            self._logger.error(f'{filename} is not found')
            return False
    
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
