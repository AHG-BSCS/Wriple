"""
Input Validation Module
Validates incoming API requests and data
"""

from app.utils.logger import setup_logger

_logger = setup_logger('Validators')

def validate_recording_parameters(params) -> bool:
    """
    Validate recording data parameters

    Args:
        params (dict): Input data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required fields exist
        required_fields = [
            'class',
            'target_count',
            'state',
            'activity',
            'angle',
            'distance',
            'obstructed',
            'obstruction',
            'setup_spacing'
        ]

        for field in required_fields:
            if field not in params:
                _logger.error(f'Missing required field: {field}')
                return False
        
        # Typecast all to integer for validation
        class_label = int(params.get('class'))
        target_count = int(params.get('target_count'))
        state = int(params.get('state'))
        activity = int(params.get('activity'))
        angle = int(params.get('angle'))
        distance = int(params.get('distance'))
        obstructed = int(params.get('obstructed'))
        obstruction = int(params.get('obstruction'))
        setup_spacing = int(params.get('setup_spacing'))

        if not _validate_rec_param_ranges(class_label, target_count, state, angle, distance,
                                        obstructed, obstruction, setup_spacing):
            return False

        if not _validate_target_params(class_label, target_count, angle, distance):
            return False
        
        if not _validate_activity_params(class_label, state, activity):
            return False
        
        if not _validate_obstruction_params(obstructed, obstruction):
            return False

        return True
    except Exception as e:
        _logger.error(f'Error validating recording parameters: {e}')
        return False


def _validate_rec_param_ranges(class_label, target_count, state, angle, distance,
                              obstructed, obstruction, setup_spacing) -> bool:
    """
    Validate recording parameter ranges
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Class must be 0 or 1 (Absence, Presence)
    if class_label not in [0, 1]:
        _logger.error(f'Invalid class value: {class_label}')
        return False
    
    # Target count must 0-3 (0=None, 1=1 target, 2=2 target, 3=3 target)
    if target_count not in [0, 1, 2, 3]:
        _logger.error(f'Invalid target_count value: {target_count}')
        return False
    
    # State must be 0-2 (0=N/A, 1=Motionless, 2=Moving)
    if state not in [0, 1, 2]:
        _logger.error(f'Invalid state value: {state}')
        return False
    
    # Angle must be 0-5 (0=None, 1=0deg, 2=30deg, 3=60deg, 4=90deg, 5=120deg)
    if angle not in [0, 1, 2, 3, 4, 5]:
        _logger.error(f'Invalid angle value: {angle}')
        return False
    
    # Distance must be 0-15 (0=None, 1=1m, ..., 15=15m)
    if distance < 0 or distance > 15:
        _logger.error(f'Invalid distance value: {distance}')
        return False
    
    # Obstructed must be 0 or 1 (0=No, 1=Yes)
    if obstructed not in [0, 1]:
        _logger.error(f'Invalid obstructed value: {obstructed}')
        return False
    
    # Obstruction must be 0-3 (0=None, 1=Concrete, 2=Wood, 3=Metal)
    if obstruction not in [0, 1, 2, 3]:
        _logger.error(f'Invalid obstruction value: {obstruction}')
        return False
    
    # Setup spacing must be 4-20 (4m to 20m)
    if setup_spacing < 4 or setup_spacing > 20:
        _logger.error(f'Invalid setup_spacing value: {setup_spacing}')
        return False
    
    return True

def _validate_target_params(class_label, target_count, angle, distance) -> bool:
    """
    Validate target parameters based on class
    
    Returns:
        bool: True if valid, False otherwise
    """
    if class_label == 0:
        if target_count == 0 and angle == 0 and distance == 0:
            return True
        else:
            _logger.error(f'Invalid target parameter for absence class.')
            return False
    elif class_label == 1:
        if target_count in [1, 2, 3] and angle in [1, 2, 3, 4, 5] and distance >= 1 and distance <= 15:
            return True
        else:
            _logger.error(f'Invalid target parameter for presence class.')
            return False

def _validate_activity_params(class_label, state, activity) -> bool:
    """
    Validate activity type based on state
    
    Returns:
        bool: True if valid, False otherwise
    """
    if class_label == 0:
        if state == 0 and activity == 0:
            return True
        else:
            _logger.error(f'Invalid activity parameter for absence class.')
            return False
    elif class_label == 1:
        if state == 1:
            if activity in [1, 2]:
                return True
            else:
                _logger.error(f'Invalid activity parameter for presence class.')
                return False
        elif state == 2:
            if activity in [1, 2, 3, 4]:
                return True
            else:
                _logger.error(f'Invalid activity parameter for presence class.')
                return False
        return True
    
def _validate_obstruction_params(obstructed, obstruction) -> bool:
    """
    Validate obstruction type based on obstructed state
    
    Returns:
        bool: True if valid, False otherwise
    """
    if obstructed == 0:
        if obstruction == 0:
            return True
        else:
            _logger.error(f'Invalid obstruction type when not obstructed.')
            return False
    elif obstructed == 1:
        if obstruction in [1, 2, 3]:
            return True
        else:
            _logger.error(f'Invalid obstruction type when obstructed.')
            return False

def validate_filename(filename) -> bool:
    """
    Validate CSV filename
    
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
