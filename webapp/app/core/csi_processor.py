"""
CSI Data Processing Module
Handles CSI data computation, filtering, and feature extraction
"""

import math
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from config.settings import VisualizerConfiguration, PredictionConfiguration, RecordingConfiguration
from utils.logger import setup_logger


class CSIProcessor:
    """Handles CSI data processing operations"""
    
    def __init__(self):
        self._amplitude_queue = []
        self._phase_queue = []
        self._signal_window = PredictionConfiguration.SIGNAL_WINDOW
        self._std_threshold = VisualizerConfiguration.D3_STD_THRESHOLD
        # Use a scaler model based from dataset to avoid fit_transform()
        self._mm_scaler = MinMaxScaler(VisualizerConfiguration.D3_VISUALIZER_SCALE)
        self._max_packets = 0
        self._logger = setup_logger('CSIProcessor')
    
    def compute_amplitude_phase(self, csi_data: list) -> tuple:
        """
        Compute amplitude and phase from CSI I/Q data
        
        Args:
            csi_data: List of I/Q values
            
        Returns:
            tuple: (amplitudes, phases)
        """
        amplitudes = []
        phases = []

        if len(csi_data) % 2 != 0:
            self._logger.error('CSI data length must be even (I/Q pairs).')
            return amplitudes, phases
        
        for i in range(0, len(csi_data), 2):
            I = csi_data[i]
            Q = csi_data[i + 1]
            amplitudes.append(math.sqrt(I**2 + Q**2))
            phases.append(math.atan2(Q, I))
        
        return amplitudes, phases
    
    def buffer_amplitude_phase(self, parsed_data: list):
        """Add amplitude and phase data to processing queues"""

        amplitudes, phases = self.compute_amplitude_phase(parsed_data)
        
        # Remove old signals if queue exceeds limit
        while len(self._amplitude_queue) >= self._max_packets:
            self._amplitude_queue.pop(0)
            self._phase_queue.pop(0)
        
        self._amplitude_queue.append(amplitudes)
        self._phase_queue.append(phases)
    
    def get_subcarrier_threshold(self, data_transposed: list) -> tuple:
        """Calculate threshold values for each subcarrier"""
        lower_threshold, upper_threshold = [], []
        
        for column in data_transposed:
            mean = np.mean(column)
            std_dev = np.std(column)
            
            lower_threshold.append(mean - self._std_threshold * std_dev)
            upper_threshold.append(mean + self._std_threshold * std_dev)

        self._logger.debug(f'Lower thresholds: {lower_threshold}')
        self._logger.debug(f'Upper thresholds: {upper_threshold}')
        
        return lower_threshold, upper_threshold
    
    def threshold_filter(self, amplitudes, phases, amp_lower, amp_upper, 
                            phase_lower, phase_upper):
        """Filter data based on amplitude and phase thresholds"""
        cleaned_amplitudes = []
        cleaned_phases = []
        
        for i, (amp, phase) in enumerate(zip(amplitudes, phases)):
            if ((amp < amp_lower[i]) or (amp > amp_upper[i]) and 
                (phase < phase_lower[i]) or (phase > phase_upper[i])):
                cleaned_amplitudes.append(amp)
                cleaned_phases.append(phase)
            else:
                cleaned_amplitudes.append(0)
                cleaned_phases.append(0)
        
        return cleaned_amplitudes, cleaned_phases
    
    def get_amp_phase_3d_coords(self):
        """Filter and process amplitude/phase data for visualization"""
        if not self._amplitude_queue:
            self._logger.warning('Amplitude queue is empty.')
            return []
        
        signal_coordinates = []
        
        # Convert to pandas-like structure for processing
        amps_transposed = list(map(list, zip(*self._amplitude_queue)))
        phases_transposed = list(map(list, zip(*self._phase_queue)))
        
        # Scale data for visualization
        scaled_amplitudes = self._mm_scaler.fit_transform(amps_transposed).T
        scaled_phases = self._mm_scaler.fit_transform(phases_transposed).T
        
        # Get thresholds
        amp_lower, amp_upper = self.get_subcarrier_threshold(scaled_amplitudes.T)
        phase_lower, phase_upper = self.get_subcarrier_threshold(scaled_phases.T)
        
        # Process each packet
        for amp, phase in zip(scaled_amplitudes, scaled_phases):
            amp = np.array(amp)
            phase = np.array(phase)
            
            # Filter data
            amp, phase = self.threshold_filter(
                amp, phase, amp_lower, amp_upper, phase_lower, phase_upper
            )
            
            # Create coordinates for visualization
            x = np.arange(-10, 10, 20/len(amp))
            
            for i in range(len(x)):
                if phase[i] != 0:
                    signal_coordinates.append((float(x[i]), float(amp[i]), float(phase[i])))
        
        return signal_coordinates
    
    def get_latest_amplitude(self, start_subcarrier: int, end_subcarrier: int) -> list:
        """
        Get subset of latest amplitude data

        Args:
            start_idx (int): Starting subcarrier for amplitude data
            end_idx (int): Ending subcarrier for amplitude data

        Returns:
            list: Amplitudes containing specific subcarriers. The 0 is the permanent y axis in heatmap
        """
        if not self._amplitude_queue:
            self._logger.warning('Amplitude queue is empty.')
            return []
        
        latest_amplitudes = self._amplitude_queue[-1][start_subcarrier:end_subcarrier]
        return latest_amplitudes
    
    def get_latest_phase(self, start_subcarrier:int, end_subcarrier: int) -> list:
        """
        Get subset of latest phase data

        Args:
            start_idx (int): Starting subcarrier for phase data
            end_idx (int): Ending subcarrier for phase data

        Returns:
            list: Phases containing specific subcarriers. The 0 is the permanent y axis in heatmap.
        """
        if not self._phase_queue:
            self._logger.warning('Phase queue is empty.')
            return []
        
        latest_phases = self._phase_queue[-1][start_subcarrier:end_subcarrier]
        return latest_phases
    
    def get_amplitude_window(self) -> list:
        """Get a window of amplitude data for visualization"""
        if (len(self._amplitude_queue) >= self._signal_window * 2):
            return self._amplitude_queue[:self._signal_window]
        else:
            return None
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self._amplitude_queue)
    
    def clear_queues(self):
        """Clear amplitude and phase queues"""
        self._amplitude_queue.clear()
        self._phase_queue.clear()
        self._logger.info('Cleared amplitude and phase queues.')
    
    def set_max_packets(self, value: int):
        """
        Set maximum number of packets to keep in queues

        Args:
            value (int): 1 for recording mode, 0 for monitoring mode
        """
        if value == 1:
            self._max_packets = RecordingConfiguration.RECORD_PACKET_LIMIT
        elif value == 0:
            self._max_packets = RecordingConfiguration.MONITOR_QUEUE_LIMIT
        else:
            self._logger.error('Invalid max packets value. Must be 0 or 1.')

    @property
    def max_packets(self) -> int:
        """Get maximum number of packets to keep in queues"""
        return self._max_packets
