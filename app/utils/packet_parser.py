"""Utility functions for parsing packet data from hardware devices"""

@staticmethod
def parse_csi_data(raw_data: bytes, ld2420_miss_count) -> list:
    """
    Parse CSI data from received packet
    
    Args:
        raw_data: Raw data from received packet
        
    Returns:
        list: Parsed CSI data components
    """
    try:
        data_str = raw_data.decode('utf-8').strip()
    except Exception as e:
        print(f'PACKET PARSER: Error decoding data - {e}')
        return None

    # Split using the section delimiter
    sections = [s.strip() for s in data_str.split('|')]
    if len(sections) != 3:
        print('PACKET PARSER: Incomplete data packet')
        return None

    # Parse Metadata
    rx_timestamp, rssi, bandwidth, channel, antenna = map(int, sections[0].split(','))

    # Parse CSI
    raw_csi = [int(x) for x in sections[1].strip().split(' ')]
    raw_csi_length = len(raw_csi)
    # Ensure that the received raw data is from 802.11a/g and has LLTF, HT-LTF
    if raw_csi_length not in [256, 384]:
        print(f'PACKET PARSER: Invalid CSI length: {raw_csi_length}')
        raw_csi = None

    # Parse LD2420
    if not sections[2].startswith('!'):
        ld2420_values = list(map(int, sections[2].split(',')))
        ld2420_array = [ld2420_values[i:i+16] for i in range(0, len(ld2420_values), 16)]
        ld2420_miss_count = 0
    else:
        if ld2420_miss_count > 30:
            print('PACKET PARSER: LD2420 sensor disconnected')
        
        ld2420_miss_count += 1

        return [
            False, ld2420_miss_count,
            rx_timestamp, rssi, bandwidth, channel, antenna,
            raw_csi
        ]

    return [
        True, ld2420_miss_count,
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
