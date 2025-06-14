"""Utility functions for parsing packet data from hardware devices"""

class PacketParser:
    """Utility class for parsing received packet data"""
    
    @staticmethod
    def parse_csi_data(data_str):
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
            raw_csi = list(filter(None, raw_csi))  # Remove empty strings
            raw_csi = [int(x) for x in raw_csi]
            
            # Return parsed components
            return parts[:-1] + [raw_csi]
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing CSI data: {e}")
            return []
    
    @staticmethod
    def extract_radar_data(parsed_data):
        """
        Extract radar coordinates and metrics from parsed data
        
        Args:
            parsed_data: Parsed CSI data list
            
        Returns:
            list: Radar data components
        """
        try:
            return [
                parsed_data[0],
                [parsed_data[5], parsed_data[9], parsed_data[13]],
                [parsed_data[6], parsed_data[10], parsed_data[14]],
                [parsed_data[7], parsed_data[11], parsed_data[15]],
                [parsed_data[8], parsed_data[12], parsed_data[16]],
            ]
        except (IndexError, TypeError) as e:
            print(f"Error extracting radar data: {e}")
            return []
