from utils.logger import setup_logger

class Visualizer:
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
