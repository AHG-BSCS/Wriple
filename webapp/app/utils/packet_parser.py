"""Utility functions for parsing packet data from hardware devices"""

from app.utils.logger import setup_logger


class PacketParser:
    """Utility class for parsing received packet data"""

    _logger = setup_logger('PacketParser')
    _ld2420_error = -1
    
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
            ld2420_valid = True

            # Split using the section delimiter
            sections = [s.strip() for s in data_str.split('|')]
            if len(sections) != 3:
                raise ValueError("Incomplete data packet")

            # Parse Metadata
            rx_timestamp, rssi, bandwidth, channel, antenna = map(int, sections[0].split(','))

            # Parse CSI
            raw_csi = [int(x) for x in sections[1].strip().split(' ')]

            # Parse LD2420
            if not sections[2].startswith('!'):
                ld2420_values = list(map(int, sections[2].split(',')))
                ld2420_array = [ld2420_values[i:i+16] for i in range(0, len(ld2420_values), 16)]
                PacketParser._ld2420_error = 0
            else:
                if PacketParser._ld2420_error > 30:
                    PacketParser._logger.error('LD2420 is disconnected')
                
                PacketParser._ld2420_error += 1
                ld2420_valid = False
                ld2420_array = [[0] * 16] * 20 # Default to empty array if no data from sensor

            # Return parsed components
            return [
                ld2420_valid,
                rx_timestamp, rssi, bandwidth, channel, antenna,
                raw_csi,
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
    def is_ld2420_active() -> bool:
        """Check if LD2420 sensor is active"""
        return PacketParser._ld2420_error < 30 or PacketParser._ld2420_error == -1
