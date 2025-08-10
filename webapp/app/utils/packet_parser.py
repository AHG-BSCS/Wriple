"""Utility functions for parsing packet data from hardware devices"""

from utils.logger import setup_logger


class PacketParser:
    """Utility class for parsing received packet data"""

    _logger = setup_logger('PacketParser')
    _rd03d_error = 0
    _ld2420_error = 0
    
    @staticmethod
    def parse_csi_data(raw_data: bytes, is_recording: bool = False) -> list:
        """
        Parse CSI data from received packet
        
        Args:
            raw_data: Raw data from received packet
            
        Returns:
            list: Parsed CSI data components
        """
        try:
            data_str = raw_data.decode('utf-8').strip()
            rd03d_valid = True
            ld2420_valid = True

            # Split using the section delimiter
            sections = [s.strip() for s in data_str.split('|')]
            if len(sections) != 4:
                raise ValueError("Incomplete data packet")

            # Parse Metadata
            rx_timestamp, rssi, channel = map(int, sections[0].split(','))

            # Parse CSI
            raw_csi = [int(x) for x in sections[1].strip().split(' ')]

            # Parse RD03D
            if not sections[2].startswith('!'):
                rd03d_values = list(map(int, sections[2].split(',')))
                rd03d_targets = [rd03d_values[i:i+4] for i in range(0, len(rd03d_values), 4)]
                PacketParser._rd03d_error = 0
            else:
                if PacketParser._rd03d_error > 10:
                    PacketParser._logger.error('RD03D is disconnected')

                PacketParser._rd03d_error += 1
                rd03d_valid = False
                rd03d_targets = [[0, 0, 0, 0]] * 3 # Default to empty targets if no data from sensor

            # Parse LD2420
            if not sections[3].startswith('!'):
                ld2420_values = list(map(int, sections[3].split(',')))
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
                rd03d_valid, ld2420_valid,
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
    def is_rd03d_active() -> bool:
        """Check if RD03D sensor is active"""
        return PacketParser._rd03d_error < 10
    
    @staticmethod
    def is_ld2420_active() -> bool:
        """Check if LD2420 sensor is active"""
        return PacketParser._ld2420_error < 30
