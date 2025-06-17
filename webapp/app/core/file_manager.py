"""File Manager Module"""

import csv
import os
import re
import threading

from config.settings import FileConfiguration
from utils.logger import setup_logger

class FileManager:
    """Handles CSV file CRUD operations and management"""

    def __init__(self):
            self.csv_file_path = None
            self.selected_csv_file = None
            self.csv_columns = FileConfiguration.CSV_COLUMNS
            self.csv_directory = FileConfiguration.CSV_DIRECTORY
            self.file_pattern = FileConfiguration.CSV_FILE_PATTERN
            self.file_prefix = FileConfiguration.CSV_FILE_PREFIX
            self.lock = threading.Lock()
            self.logger = setup_logger('FileManager')
            
            # Ensure directory exists
            os.makedirs(self.csv_directory, exist_ok=True)
    
    def get_next_filename(self):
        """Generate the next available CSV filename"""
        try:
            files = os.listdir(self.csv_directory)
            pattern = re.compile(self.file_pattern)
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
            
            filename = f'{self.file_prefix}{next_number:03d}.csv'
            self.logger.info(f'Writing on {filename}.')
            return os.path.join(self.csv_directory, filename)
            
        except Exception as e:
            self.logger.error(f"Error generating new csv filename: {e}")
            # Fallback filename
            return os.path.join(self.csv_directory, f'{self.file_prefix}ERROR.csv')
    
    def list_csv_files(self):
        """List all CSV files in the recording directory"""
        try:
            files = os.listdir(self.csv_directory)
            csv_files = [f for f in files if f.endswith('.csv')]
            return sorted(csv_files)
        except Exception as e:
            self.logger.error(f"Error listing CSV files: {e}")
            return []
    
    def select_csv_file(self, filename):
        """Set the file to be used for visualization"""
        self.selected_csv_file = os.path.join(self.csv_directory, filename)
        file_path = self.get_file_path(filename)
        
        if os.path.exists(file_path):
            self.logger.info(f"{filename} is selected for visualization")
            return True
        else:
            self.selected_csv_file = None
            self.logger.error(f"{filename} is not found")
            return False
    
    def init_new_csv(self):
        """Prepare a new CSV file for recording"""
        self.csv_file_path = self.get_next_filename()
        
        try:
            # Create file with headers
            with open(self.csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.csv_columns)
            
            return True
        except Exception as e:
            self.logger.error(f"Error creating CSV file: {e}")
            self.csv_file_path = None
            return False
    
    def write_data(self, data_row):
        """
        Write a data row to the CSV file
        
        Args:
            data_row: List of data values to write
        """
        if not self.csv_file_path:
            self.logger.warning("CSV file path is not set. Preparing new file.")
            self.init_new_csv()
            return False
        
        try:
            with self.lock:
                with open(self.csv_file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(data_row)
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing to CSV file: {e}")
            return False
