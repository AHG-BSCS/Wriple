"""
Input Validation Module
Validates incoming API requests and data
"""


def validate_recording_parameters(data):
    """
    Validate recording data parameters
    
    Args:
        data (dict): Input data to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    try:
        # Check required fields exist
        required_fields = ['class_label', 'target_count', 'line_of_sight', 'angle', 'distance_t1']
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate data types and ranges
        presence = data.get('class_label')
        if not isinstance(presence, (int, str)) or int(presence) not in [0, 1]:
            return False
        
        target = data.get('target_count')
        if not isinstance(target, (int, str)) or not str(target).isdigit():
            return False
        
        # Validate numeric fields
        numeric_fields = ['line_of_sight', 'angle', 'distance_t1']
        for field in numeric_fields:
            value = data.get(field)
            if not isinstance(value, (int, float, str)):
                return False
            
            try:
                float(value)
            except (ValueError, TypeError):
                return False
        
        # Additional range validation
        angle = float(data.get('angle', 0))
        if not -180 <= angle <= 180:
            return False
        
        distance = float(data.get('distance_t1', 0))
        if distance < 0:
            return False
        
        return True
        
    except Exception as e:
        print(f"Validation error: {e}")
        return False


def validate_filename(filename):
    """
    Validate CSV filename
    
    Args:
        filename (str): Filename to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(filename, str):
        return False
    
    # Check file extension
    if not filename.endswith('.csv'):
        return False
    
    # Check for potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in dangerous_chars):
        return False
    
    # Check filename length
    if len(filename) > 255:
        return False
    
    return True
