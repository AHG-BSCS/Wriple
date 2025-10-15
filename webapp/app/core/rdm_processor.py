import numpy as np
from app.config.settings import RecordingConfiguration, VisualizerConfiguration

class RDMProcessor:
    """Handles RDM data processing and distance estimation"""

    def __init__(self):
        self._rdm_queue = []
        self._queue_max_packets = RecordingConfiguration.RDM_QUEUE_LIMIT
        self._gates_threshold  = np.array(VisualizerConfiguration.RDM_GATES_THRESHOLD)

        self._gate_distance = VisualizerConfiguration.RDM_GATE_DISTANCE
        self._absence_tolerance = VisualizerConfiguration.RDM_ABSENCE_TOLERANCE
        self._alpha = VisualizerConfiguration.RDM_SMOOTHING_ALPHA

        self._last_distance = None
        self._target_distance = 0.0
        self._absence_counter = 0
        self._prev_distance = []

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

    def estimate_distance(self, gate_energies):
        """
        Estimate distance based on range gate energies.

        Args:
            gate_energies: List or array of gate energy values.
        
        Returns:
            float: Smoothed distance estimate in meters.
        """
        energies = np.array(gate_energies)
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
