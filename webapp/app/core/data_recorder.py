"""
Data Recording Module
Handles CSV file creation, writing, and management
"""

import os
import re
import csv
import threading
from config.settings import FileConfiguration
from utils.logger import setup_logger


class DataRecorder:
    """Manages CSV data recording operations"""
    
    def __init__(self):
        self.csv_file_path = None
        self.csv_directory = FileConfiguration.CSV_DIRECTORY
        self.file_pattern = FileConfiguration.CSV_FILE_PATTERN
        self.file_prefix = FileConfiguration.CSV_FILE_PREFIX
        self.columns = FileConfiguration.CSV_COLUMNS
        self.lock = threading.Lock()
        self.logger = setup_logger('DataRecorder')
        
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
    
    def prepare_new_file(self):
        """Prepare a new CSV file for recording"""
        self.csv_file_path = self.get_next_filename()
        
        try:
            # Create file with headers
            with open(self.csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.columns)
            
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
            self.prepare_new_file()
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
    
    def list_csv_files(self):
        """List all CSV files in the recording directory"""
        try:
            files = os.listdir(self.csv_directory)
            csv_files = [f for f in files if f.endswith('.csv')]
            return sorted(csv_files)
        except Exception as e:
            self.logger.error(f"Error listing CSV files: {e}")
            return []
    
    def get_file_path(self, filename):
        """Get full path for a CSV file"""
        return os.path.join(self.csv_directory, filename)
    
    def file_exists(self, filename):
        """Check if a CSV file exists"""
        file_path = self.get_file_path(filename)
        return os.path.exists(file_path)
    

class CSVVisualizer:
    """Handles CSV file visualization operations"""
    
    def __init__(self, data_recorder):
        self.data_recorder = data_recorder
        self.current_visualization_file = None
        self.logger = setup_logger('CSVVisualizer')
    
    def set_visualization_file(self, filename):
        """Set the file to be used for visualization"""
        if not self.data_recorder.file_exists(filename):
            self.logger.error(f"CSV file not found: {filename}")
            raise FileNotFoundError(f"CSV file not found: {filename}")
        
        self.current_visualization_file = self.data_recorder.get_file_path(filename)
        return True
    
    def load_visualization_data(self):
        """Load data from the current visualization file"""
        if not self.current_visualization_file:
            # TODO: Impove this redundant implementation
            raise ValueError("No visualization file set")
        
        try:
            import pandas as pd
            
            df = pd.read_csv(self.current_visualization_file)
            
            # Parse Raw_CSI column if it exists
            if 'Raw_CSI' in df.columns:
                df['Raw_CSI'] = df['Raw_CSI'].apply(eval)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV file for visualization: {e}")
            return None
    
    def get_csi_data_for_processing(self, csi_processor):
        """Extract CSI data and process it for visualization"""
        df = self.load_visualization_data()
        if df is None:
            return []
        
        try:
            csi_processor.clear_queues()
            for _, row in df.iterrows():
                if 'Raw_CSI' in row:
                    csi_processor.process_csi_data(row['Raw_CSI'])
            
            # Return processed signal coordinates
            return csi_processor.filter_amp_phase()
            
        except Exception as e:
            self.logger.error(f"Error processing CSV data for visualization: {e}")
            return []
