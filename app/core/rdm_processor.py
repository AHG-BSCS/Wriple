"""Range-Doppler Map Processor Module"""

import json

import numpy as np

from app.config.settings import RecordConfig, RdmConfig


class RDMProcessor:
    """Handles RDM data processing and distance estimation"""

    def __init__(self):
        self._rdm_queue = []
        self._queue_max_packets = RecordConfig.RDM_QUEUE_LIMIT
        self._gates_threshold  = np.array(RdmConfig.GATES_DISTANCE_THRESHOLDS)
        self._rdm_thresholds = None
        self._heatmap_max_scaler = RdmConfig.HEATMAP_MAX_SCALER

        self._gate_distance = RdmConfig.GATE_DISTANCE
        self._absence_tolerance = RdmConfig.ABSENCE_TOLERANCE
        self._alpha = RdmConfig.SMOOTHING_ALPHA

        self._last_distance = None
        self._target_distance = 0.0
        self._absence_counter = 0
        self._prev_distance = []

        self._load_threshold()
    
    def _load_threshold(self):
        """Load RDM thresholds from JSON file"""
        try:
            with open(RdmConfig.RDM_THRESHOLDS_PATH, 'r') as file:
                    self._rdm_thresholds = json.load(file)
        except Exception as e:
            print(f'Error loading RDM thresholds: {e}')

    def _find_contiguous_clusters(self, indices):
        """
        Find contiguous clusters in a list of indices.

        Args:
            indices: List of integer indices (sorted in ascending order).

        Returns:
            List of tuples representing start and end of each contiguous cluster.
        """
        if len(indices) == 0:
            return []
        clusters = []
        start = indices[0]
        end = indices[0]
        for idx in indices[1:]:
            if idx == end + 1:
                end = idx
            else:
                clusters.append((start, end))
                start = idx
                end = idx
        clusters.append((start, end))
        return clusters

    def estimate_distance(self):
        """
        Estimate distance based on range gate energies.

        Args:
            gate_energies: List or array of gate energy values.
        
        Returns:
            float: Smoothed distance estimate in meters.
        """
        energies = np.array(self._rdm_queue[-1][9])
        if len(energies) == 0:
            return 0.0

        # Select gates that exceed human presence threshold
        active_gates = np.where(energies >= self._gates_threshold)[0]

        if active_gates.size > 0:
            clusters = self._find_contiguous_clusters(list(active_gates))

            # Choose the largest cluster
            best_cluster = None
            best_width = -1
            best_energy_sum = -1.0
            for (a, b) in clusters:
                width = b - a + 1
                if width < 1:
                    continue
                energy_sum = float(np.sum(energies[a:b+1]))
                if width > best_width or (width == best_width and energy_sum > best_energy_sum):
                    best_width = width
                    best_energy_sum = energy_sum
                    best_cluster = (a, b)

            a, b = best_cluster
            # Compute center-of-cluster using gate-center convention (k + 0.5)
            center_index = ((a + b) / 2.0) + 0.5
            raw_distance_m = center_index * self._gate_distance

            # Average current raw_distance with last non-zero distance
            if (self._last_distance is None) or (self._last_distance == 0.0):
                self._target_distance = float(raw_distance_m)
            else:
                self._target_distance = float(self._alpha * raw_distance_m + (1.0 - self._alpha) * self._last_distance)

            self._last_distance = float(raw_distance_m)
            self._absence_counter = 0
        else:
            self._absence_counter += 1
            if (self._last_distance is not None) and (self._absence_counter <= self._absence_tolerance):
                # Hold last_nonzero_distance if within tolerance
                self._target_distance = float(self._last_distance)
            else:
                self._last_distance = None
                self._target_distance = 0.0

        self._prev_distance.append(self._target_distance)
        if len(self._prev_distance) > self._queue_max_packets:
            self._prev_distance.pop(0)
        
        # print(f'ACTIVE GATES: {active_gates}')
        return round(self._target_distance, 1)

    def get_filtered_data(self):
        """
        Apply filtering to the RDM data queue to remove noise.

        Returns:
            list: Filtered RDM data suitable for visualization.
        """
        if len(self._rdm_queue) == 0:
            return None

        raw = self._rdm_queue[-1]
        filtered_data = []
        
        # Apply Thresholds
        for doppler_idx, row in enumerate(raw):
            for gate_idx, value in enumerate(row):
                threshold = self._rdm_thresholds[doppler_idx][gate_idx]
                if value <= threshold:
                    value = 0.0
                else:
                    value = value / self._heatmap_max_scaler
                filtered_data.append([doppler_idx, gate_idx, value])

        return filtered_data

    def queue_rdm(self, rdm_data):
        """
        Queue new RDM data packet.

        Args:
            rdm_data: New RDM data packet shaped (20, 16).
        """
        self._rdm_queue.append(rdm_data)

        # Remove oldest RDM data if it exceeds the limits
        while len(self._rdm_queue) > self._queue_max_packets:
            self._rdm_queue.pop(0)
