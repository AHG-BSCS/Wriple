"""Utility functions for parsing packet data from hardware devices"""

from utils.logger import setup_logger


class PacketParser:
    """Utility class for parsing received packet data"""

    _logger = setup_logger('PacketParser')
    
    @staticmethod
    def parse_csi_data(raw_data: bytes) -> list:
        """
        Parse CSI data from received packet
        
        Args:
            raw_data: Raw data from received packet
            
        Returns:
            list: Parsed CSI data components
        """
        try:
            data_str = raw_data.decode('utf-8').strip()

            # Split using the section delimiter
            sections = [s.strip() for s in data_str.split('|')]
            if len(sections) != 4:
                raise ValueError("Incomplete data packet")

            # Parse Metadata
            meta_str = sections[0].strip('()')
            rx_timestamp, rssi, channel = map(int, meta_str.split(','))

            # Parse CSI
            csi_str = sections[1].strip('[]')
            raw_csi = [int(x) for x in csi_str.strip().split(' ')]

            # Parse RD03D
            if len(sections[2]) > 3: # If RD03D sensor doesn't provide data
                rd03d_str = sections[2].strip('()')
                rd03d_values = list(map(int, rd03d_str.split(',')))
                rd03d_targets = [rd03d_values[i:i+4] for i in range(0, len(rd03d_values), 4)]

            # Parse LD2420
            if len(sections[3]) > 3: # If LD2420 sensor doesn't provide data
                ld2420_str = sections[3].strip('[]')
                ld2420_values = list(map(int, ld2420_str.split(',')))
                ld2420_array = [ld2420_values[i:i+16] for i in range(0, len(ld2420_values), 16)]
            else:
                ld2420_array = [[0] * 16] * 20  # Default to empty array if no data

            # Return parsed components
            return [
                rx_timestamp, rssi, channel,
                raw_csi,
                rd03d_targets[0], rd03d_targets[1], rd03d_targets[2],
                ld2420_array[0], ld2420_array[1], ld2420_array[2],
                ld2420_array[3], ld2420_array[4], ld2420_array[5],
                ld2420_array[6], ld2420_array[7], ld2420_array[8],
                ld2420_array[9], ld2420_array[10], ld2420_array[11],
                ld2420_array[12], ld2420_array[13], ld2420_array[14],
                ld2420_array[15], ld2420_array[16], ld2420_array[17],
                ld2420_array[18], ld2420_array[19]
            ]
            
        except (ValueError, IndexError) as e:
            PacketParser._logger.error(f'Error parsing CSI data: {e}')
            return []
    
    @staticmethod
    def extract_radar_data(rssi: int, target_1: list, target_2: list, target_3: list) -> list:
        """
        Extract radar coordinates and metrics from parsed data
        
        Args:
            parsed_data: Parsed CSI data list
            
        Returns:
            list: Radar data components including:
            - RSSI: RSSI value of AP
            - X: X coordinates of targets
            - Y: Y coordinates of targets
            - Speed: Speed of targets
            - Resolution: Resolution of X and Y coordinates
        """
        try:
            return [rssi, target_1, target_2, target_3]
        except (IndexError, TypeError) as e:
            PacketParser._logger.error(f'Error extracting radar data: {e}')
            return []
