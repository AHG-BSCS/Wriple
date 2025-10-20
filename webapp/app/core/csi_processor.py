"""CSI Data Processing Module"""

import math

import numpy as np

from scipy.signal import butter, filtfilt

from app.config.settings import VisualizerConfiguration, PredictionConfiguration, RecordingConfiguration
from app.utils.logger import setup_logger


class CSIProcessor:
    """Handles CSI data computation, filtering, and feature extraction"""
    
    def __init__(self):
        self._amplitude_queue = []
        self._phase_queue = []
        self._amps_variance = 0
        self._prev_amps_sum = None

        parts = [np.arange(sl[0], sl[1]) for sl in VisualizerConfiguration.HEAT_SUBCARRIER_SLICES]
        self._heat_subcarrier_slices = np.concatenate(parts)
        self._amps_subcarriers = [i for s, e in VisualizerConfiguration.AMPS_SUBCARRIER for i in range(s, e)]
        self._heat_subcarrier_count = sum(sl[1] - sl[0] for sl in VisualizerConfiguration.HEAT_SUBCARRIER_SLICES)
        self._heat_signal_window = VisualizerConfiguration.HEAT_SIGNAL_WINDOW
        self._heat_penalty_factor = VisualizerConfiguration.HEAT_PENALTY_FACTOR
        self._heat_diff_threshold = VisualizerConfiguration.HEAT_DIFF_THRESHOLD

        self._cutoff = VisualizerConfiguration.CUTOFF
        self._fs = VisualizerConfiguration.FS
        self._order = VisualizerConfiguration.ORDER
        
        self._pred_signal_window = PredictionConfiguration.PRED_SIGNAL_WINDOW
        self._queue_max_packets = RecordingConfiguration.CSI_QUEUE_LIMIT
        self._logger = setup_logger('CSIProcessor')
    
    def queue_csi(self, raw_csi_data: list):
        """
        Add amplitude and phase data to processing queues
        
        Args:
            raw_csi_data: Separated and validated Wi-Fi CSI data from ESP32
        """
        amplitudes = self._compute_csi(raw_csi_data)
        amplitudes = np.array(amplitudes)[self._amps_subcarriers]

        while len(self._amplitude_queue) > self._queue_max_packets:
            self._amplitude_queue.pop(0)
        
        self._amplitude_queue.append(amplitudes)
    
    def _compute_csi(self, csi_data: list) -> tuple[list, list]:
        """
        Compute amplitude and phase from raw CSI I/Q data
        
        Args:
            csi_data: List of I/Q values
            
        Returns:
            tuple: (Amplitudes, Phases)
        """
        amplitudes = []
        # phases = []

        if len(csi_data) % 2 != 0:
            self._logger.error('CSI data length must be even (I/Q pairs).')
            return amplitudes
        
        for i in range(0, len(csi_data), 2):
            I = csi_data[i]
            Q = csi_data[i + 1]
            amplitudes.append(math.sqrt(I**2 + Q**2))
            # phases.append(math.atan2(Q, I))
        
        return amplitudes
    
    def _apply_lowpass_filter(self, data) -> np.ndarray:
        """
        Remove the high frequency noise using a low-pass Butterworth filter

        Args:
            data: Input signal data to be filtered

        Returns:
            Filtered signal data
        """
        nyquist = 0.5 * self._fs
        normal_cutoff = self._cutoff / nyquist
        b, a = butter(self._order, normal_cutoff, btype='low', analog=False)
        y = filtfilt(b, a, data, axis=0)
        return y

    def get_amps_heatmap_data(self) -> list:
        """
        Get the latest amplitude data, preprocessed by subtracting the mean for each subcarrier,
        and apply a penalty to values far from the mean to improve heatmap contrast.
    
        Returns:
            list: Highlighted amplitudes
        """
        if len(self._amplitude_queue) < self._heat_signal_window:
            last = np.asarray(self._amplitude_queue[-1])
            return last[self._heat_subcarrier_slices].tolist()
        
        latest_window = np.asarray(self._amplitude_queue[-self._heat_signal_window:])
        # latest_window = self._apply_lowpass_filter(latest_window)
        diff = self._compute_latest_diff(latest_window)
        filtered_data = self._apply_diff_threshold(diff)
        return filtered_data
    
    def _compute_latest_diff(self, latest_window: np.ndarray) -> np.ndarray:
        """
        Compute difference between the latest packet and the latest window mean
        over the configured subcarrier slice.
        """
        mean_per_subcarrier = np.mean(latest_window[:, self._heat_subcarrier_slices], axis=0)
        diff = latest_window[-1, self._heat_subcarrier_slices] - mean_per_subcarrier
        # Store highest absolute diff
        self._amps_variance = diff.var()
        return diff

    def _apply_diff_threshold(self, diff: np.ndarray) -> list:
        """
        Suppress small differences and amplify large ones according to thresholds
        and penalty factor. Returns a python list ready for JSON/consumption.
        """
        mask = np.abs(diff) >= self._heat_diff_threshold
        highlighted = np.where(
            mask,
            (np.abs(diff) ** self._heat_penalty_factor),
            0.0
        ).tolist()
        return highlighted
    
    def preprocess_amplitudes(self, amplitudes):
        amp_data = [self._apply_lowpass_filter(amp) for amp in amplitudes]
        mean_per_sub = np.mean(amp_data, axis=0)

        # Euclidean distance of each packet to the mean vector
        distances = np.linalg.norm(amp_data - mean_per_sub, axis=1)

        threshold = 8.0     # Threshold for keeping original value
        min_shrink = 0.1    # Minimum shrink factor for very far samples
        decay = 1.0         # Exponential decay rate

        shrink_factors = np.where(
            distances <= threshold,
            1.0,
            min_shrink + (1.0 - min_shrink) * np.exp(-decay * (distances - threshold))
        )

        amp_arr = mean_per_sub + shrink_factors[:, None] * (amp_data - mean_per_sub)

        amplitudes_mean = np.mean(amp_arr, axis=0)
        amplitudes_sum = np.sum(amplitudes_mean[:52])

        if self._prev_amps_sum is None:
            self._prev_amps_sum = amplitudes_sum
        amplitudes_diff = np.abs(amplitudes_sum - self._prev_amps_sum)
        # amplitudes_diff = np.abs(np.diff(amplitudes_sum, prepend=self._prev_amps_sum))
        self._prev_amps_sum = amplitudes_sum
        return amplitudes_mean.tolist() + [float(amplitudes_diff)]
    
    def get_amplitude_window(self) -> list:
        """
        Get a window of amplitude data for visualization

        Returns:
            list: Amplitude data for the current signal window, or None if not enough data
        """
        return self.preprocess_amplitudes(self._amplitude_queue[-self._pred_signal_window:])
    
    @property
    def amplitude_variance(self) -> float:
        """
        Get the variance of the amplitude data in the queue

        Returns:
            float: Variance of the amplitude data, or 0.0 if not enough data
        """
        if len(self._amplitude_queue) < self._heat_signal_window:
            return 0.0
        
        latest_window = np.asarray(self._amplitude_queue[-self._heat_signal_window:])
        # latest_window = self._apply_lowpass_filter(latest_window)
        self._compute_latest_diff(latest_window)
        return round(self._amps_variance, 1)
    
    def clear_queues(self):
        """Clear amplitude and phase queues"""
        self._amplitude_queue.clear()
        self._phase_queue.clear()
        self._logger.info('Cleared amplitude and phase queues.')
    
    @property
    def max_packets(self) -> int:
        """
        Get maximum number of packets to keep in queues
        
        Returns:
            int: Maximum packets limit
        """
        return self._queue_max_packets
