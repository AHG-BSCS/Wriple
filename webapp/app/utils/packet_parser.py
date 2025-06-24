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
            data_set = -1 # 0 = CSI, 1 = RD03D, 2 = LD2420
            data_str = raw_data.decode('utf-8').strip()

            # Split using the section delimiter
            sections = [s.strip() for s in data_str.split('|')]
            if len(sections) != 3:
                raise ValueError("Incomplete data packet")

            # Check for data set based from request
            if sections[0].startswith('CSI'):
                data_set = 0
                # Parse Metadata
                rx_timestamp, rssi, channel = map(int, sections[1].split(','))
                # Parse CSI
                raw_csi = [int(x) for x in sections[2].strip().split(',')]

            elif sections[0].startswith('RD03D'):
                data_set = 1
                # Parse Metadata
                rx_timestamp, rssi, channel = map(int, sections[1].split(','))

                # Parse RD03D
                if sections[2].startswith('!'): # If RD03D sensor doesn't provide data
                    rd03d_targets = [[0, 0, 0, 0]] * 3
                else:
                    rd03d_values = list(map(int, sections[2].split(',')))
                    rd03d_targets = [rd03d_values[i:i+4] for i in range(0, len(rd03d_values), 4)]

            elif sections[0].startswith('LD2420'):
                data_set = 2
                # Parse RD03D
                if sections[1].startswith('!'): # If RD03D sensor doesn't provide data
                    rd03d_targets = [[0, 0, 0, 0]] * 3
                    PacketParser._logger.error('LD2420 has no data')
                else:
                    rd03d_values = list(map(int, sections[1].split(',')))
                    rd03d_targets = [rd03d_values[i:i+4] for i in range(0, len(rd03d_values), 4)]

                # Parse LD2420
                if sections[2].startswith('!'): # If LD2420 sensor doesn't provide data
                    ld2420_array = [[0] * 16] * 20
                else:
                    ld2420_values = list(map(int, sections[2].split(',')))
                    ld2420_array = [ld2420_values[i:i+16] for i in range(0, len(ld2420_values), 16)]

            # Return parsed components
            if data_set == 0:
                return [data_set, rx_timestamp, rssi, channel, raw_csi]
            elif data_set == 1:
                return [
                    data_set, rx_timestamp, rssi, channel,
                    rd03d_targets[0], rd03d_targets[1], rd03d_targets[2]
                ]
            elif data_set == 2:
                return [
                    data_set,
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
