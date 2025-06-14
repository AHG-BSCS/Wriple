"""
CSI Data Processing Module
Handles CSI data computation, filtering, and feature extraction
"""

import math
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from config.settings import VisualizerConfiguration


class CSIProcessor:
    """Handles CSI data processing operations"""
    
    def __init__(self):
        self.amplitude_queue = []
        self.phase_queue = []
        self.std_threshold = VisualizerConfiguration.D3_STD_THRESHOLD
        self.mm_scaler = MinMaxScaler(VisualizerConfiguration.D3_VISUALIZER_SCALE)
        self.max_packets = VisualizerConfiguration.MAX_PACKET
    
    def compute_csi_amplitude_phase(self, csi_data):
        """
        Compute amplitude and phase from CSI I/Q data
        
        Args:
            csi_data: List of I/Q values
            
        Returns:
            tuple: (amplitudes, phases)
        """
        if len(csi_data) % 2 != 0:
            raise ValueError('CSI data length must be even (I/Q pairs).')
        
        amplitudes = []
        phases = []
        
        for i in range(0, len(csi_data), 2):
            I = csi_data[i]
            Q = csi_data[i + 1]
            amplitudes.append(math.sqrt(I**2 + Q**2))
            phases.append(math.atan2(Q, I))
        
        return amplitudes, phases
    
    def add_to_queue(self, amplitudes, phases):
        """Add amplitude and phase data to processing queues"""
        # Remove old signals if queue exceeds limit
        while len(self.amplitude_queue) >= self.max_packets:
            self.amplitude_queue.pop(0)
            self.phase_queue.pop(0)
        
        self.amplitude_queue.append(amplitudes)
        self.phase_queue.append(phases)
    
    def get_subcarrier_threshold(self, data_transposed):
        """Calculate threshold values for each subcarrier"""
        lower_threshold, upper_threshold = [], []
        
        for column in data_transposed:
            mean = np.mean(column)
            std_dev = np.std(column)
            
            lower_threshold.append(mean - self.std_threshold * std_dev)
            upper_threshold.append(mean + self.std_threshold * std_dev)
        
        return lower_threshold, upper_threshold
    
    def clean_and_filter_data(self, amplitudes, phases, amp_lower, amp_upper, 
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
    
    def filter_amp_phase(self):
        """Filter and process amplitude/phase data for visualization"""
        if not self.amplitude_queue:
            return []
        
        signal_coordinates = []
        
        # Convert to pandas-like structure for processing
        amps_transposed = list(map(list, zip(*self.amplitude_queue)))
        phases_transposed = list(map(list, zip(*self.phase_queue)))
        
        # Scale data for visualization
        scaled_amplitudes = self.mm_scaler.fit_transform(amps_transposed).T
        scaled_phases = self.mm_scaler.fit_transform(phases_transposed).T
        
        # Get thresholds
        amp_lower, amp_upper = self.get_subcarrier_threshold(scaled_amplitudes.T)
        phase_lower, phase_upper = self.get_subcarrier_threshold(scaled_phases.T)
        
        # Process each packet
        for amp, phase in zip(scaled_amplitudes, scaled_phases):
            amp = np.array(amp)
            phase = np.array(phase)
            
            # Filter data
            amp, phase = self.clean_and_filter_data(
                amp, phase, amp_lower, amp_upper, phase_lower, phase_upper
            )
            
            # Create coordinates for visualization
            x = np.arange(-10, 10, 20/len(amp))
            
            for i in range(len(x)):
                if phase[i] != 0:
                    signal_coordinates.append((float(x[i]), float(amp[i]), float(phase[i])))
        
        return signal_coordinates
    
    def get_latest_amplitude_subset(self, start_idx=127, end_idx=148):
        """Get subset of latest amplitude data"""
        if not self.amplitude_queue:
            return []
        
        latest_amplitudes = self.amplitude_queue[-1][start_idx:end_idx]
        return [[x, 0, float(latest_amplitudes[x])] for x in range(len(latest_amplitudes))]
    
    def get_latest_phase_subset(self, start_idx=6, end_idx=27):
        """Get subset of latest phase data"""
        if not self.phase_queue:
            return []
        
        latest_phases = self.phase_queue[-1][start_idx:end_idx]
        return [[x, 0, float(latest_phases[x])] for x in range(len(latest_phases))]
    
    def clear_queues(self):
        """Clear amplitude and phase queues"""
        self.amplitude_queue.clear()
        self.phase_queue.clear()
    
    def set_max_packets(self, max_packets):
        """Set maximum number of packets to keep in queues"""
        self.max_packets = max_packets
    
    def get_queue_size(self):
        """Get current queue size"""
        return len(self.amplitude_queue)
