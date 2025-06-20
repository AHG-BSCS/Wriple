"""Utility functions for parsing packet data from hardware devices"""

from utils.logger import setup_logger


class PacketParser:
    """Utility class for parsing received packet data"""

    _logger = setup_logger('PacketParser')
    
    @staticmethod
    def parse_csi_data(data_str: str) -> list:
        """
        Parse CSI data from received packet
        
        Args:
            data_str: Raw data string from packet
            
        Returns:
            list: Parsed CSI data components
        """
        try:
            parts = data_str.split(',')
            csi_data_start = data_str.find('[')
            csi_data_end = data_str.find(']')
            
            # Extract CSI data as integers
            raw_csi = data_str[csi_data_start + 1:csi_data_end].strip().split(' ')
            raw_csi = list(filter(None, raw_csi))
            raw_csi = [int(x) for x in raw_csi]
            
            # Return parsed components
            return parts[:-1] + [raw_csi]
            
        except (ValueError, IndexError) as e:
            PacketParser._logger.error(f'Error parsing CSI data: {e}')
            return []
    
    @staticmethod
    def extract_radar_data(parsed_data: list) -> list:
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
            return [
                # RSSI
                parsed_data[0],
                # Target 1 X     Target 2 X      Target 3 X
                [parsed_data[5], parsed_data[9], parsed_data[13]],
                # Target 1 Y     Target 2 Y       Target 3 Y
                [parsed_data[6], parsed_data[10], parsed_data[14]],
                # Target 1 Speed Target 2 Speed   Target 3 Speed
                [parsed_data[7], parsed_data[11], parsed_data[15]],
                # Target 1 Res   Target 2 Res     Target 3 Res
                [parsed_data[8], parsed_data[12], parsed_data[16]],
            ]
        except (IndexError, TypeError) as e:
            PacketParser._logger.error(f'Error extracting radar data: {e}')
            return []
