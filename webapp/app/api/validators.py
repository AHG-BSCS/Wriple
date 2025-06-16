"""
Input Validation Module
Validates incoming API requests and data
"""

from utils.logger import setup_logger

logger = setup_logger('Validators')

def validate_recording_parameters(params) -> bool:
    """
    Validate recording data parameters
    
    Args:
        data (dict): Input data to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required fields exist
        required_fields = ['class_label', 'target_count', 'line_of_sight', 'angle', 'distance_t1']
        
        for field in required_fields:
            if field not in params:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate data types and ranges
        presence = params.get('class_label')
        if not isinstance(presence, (int, str)) or int(presence) not in [0, 1]:
            logger.error(f"Invalid class_label: {presence}")
            return False
        
        target = params.get('target_count')
        if not isinstance(target, (int, str)) or not str(target).isdigit():
            logger.error(f"Invalid target_count: {target}")
            return False
        
        # Validate numeric fields
        numeric_fields = ['line_of_sight', 'angle', 'distance_t1']
        for field in numeric_fields:
            value = params.get(field)
            if not isinstance(value, (int, float, str)):
                logger.error(f"Invalid type for {field}: {value}")
                return False
            
            try:
                float(value)
            except (ValueError, TypeError):
                logger.error(f"Invalid value for {field}: {value}")
                return False
        
        # Additional range validation
        angle = float(params.get('angle', 0))
        if not -180 <= angle <= 180:
            logger.error(f"Angle out of range: {angle}")
            return False
        
        distance = float(params.get('distance_t1', 0))
        if distance < 0:
            logger.error(f"Distance_t1 cannot be negative: {distance}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating recording parameters: {e}")
        return False

def validate_target_count(params) -> dict:
    """Validate target count based on class label
    
    Args:
        params (dict): Recording parameters
    
    Returns:
        dict: Updated parameters with target count
    """
    try:
        class_label = int(params['class_label'])
        if class_label == 0:
            params['target_count'] = 0
        else:
            params['target_count'] = int(params.get('target_count', -1))
        return params
    except Exception as e:
        logger.error(f"Error validating target count: {e}")
        return params

def validate_filename(filename) -> bool:
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
