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
        params (dict): Input data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required fields exist
        required_fields = [
            'class_label',
            'target_count',
            'state',
            'activity',
            'angle',
            'distance_t1',
            'obstructed',
            'obstruction',
            'spacing'
        ]

        for field in required_fields:
            if field not in params:
                logger.error(f'Missing required field: {field}')
                return False

        # Validate class_label: must be 0 or 1 (Absence/Presence)
        presence = params.get('class_label')
        try:
            presence_int = int(presence)
        except (ValueError, TypeError):
            logger.error(f'Invalid class_label type: {presence}')
            return False
        if presence_int not in [0, 1]:
            logger.error(f'Invalid class_label value: {presence}')
            return False

        # Validate target_count: must be integer 0-3
        target = params.get('target_count')
        try:
            target_int = int(target)
        except (ValueError, TypeError):
            logger.error(f'Invalid target_count type: {target}')
            return False
        if target_int < 0 or target_int > 3:
            logger.error(f'Invalid target_count value: {target}')
            return False
        
        # Validate state : must be integer 0-2 (No State, Motionless, Moving)
        state = params.get('state')
        try:
            state_int = int(state)
        except (ValueError, TypeError):
            logger.error(f'Invalid state type: {state}')
            return False
        if state_int < 0 or state_int > 2:
            logger.error(f'Invalid state value: {state}')
            return False
        
        # Validate activity: must be integer 0-4 (No Activity, Stand, Sit, Walking, Running)
        activity = params.get('activity')
        try:
            activity_int = int(activity)
        except (ValueError, TypeError):
            logger.error(f'Invalid activity type: {activity}')
            return False
        if activity_int < 0 or activity_int > 4:
            logger.error(f'Invalid activity value: {activity}')
            return False

        # Validate angle: must be one of 0-5
        angle = params.get('angle')
        try:
            angle_val = int(angle)
        except (ValueError, TypeError):
            logger.error(f'Invalid angle type: {angle}')
            return False
        if angle_val not in [0, 1, 2, 3, 4, 5]:
            logger.error(f'Invalid angle value: {angle}')
            return False

        # Validate distance_t1: must be integer 0-10
        distance = params.get('distance_t1')
        try:
            distance_val = int(distance)
        except (ValueError, TypeError):
            logger.error(f'Invalid distance_t1 type: {distance}')
            return False
        if distance_val < -1 or distance_val > 10:
            logger.error(f'Invalid distance_t1 value: {distance}')
            return False

        # Validate obstructed: must be 0 or 1 (No/Yes)
        obstructed = params.get('obstructed')
        try:
            obstructed_int = int(obstructed)
        except (ValueError, TypeError):
            logger.error(f'Invalid obstructed type: {obstructed}')
            return False
        if obstructed_int not in [0, 1]:
            logger.error(f'Invalid obstructed value: {obstructed}')
            return False

        # Validate obstruction: must be integer 0-3 (None, Wood, Concrete, Metal)
        obstruction = params.get('obstruction')
        try:
            obstruction_int = int(obstruction)
        except (ValueError, TypeError):
            logger.error(f'Invalid obstruction type: {obstruction}')
            return False
        if obstruction_int < 0 or obstruction_int > 3:
            logger.error(f'Invalid obstruction value: {obstruction}')
            return False

        # Validate spacing: must be integer 3-15
        spacing = params.get('spacing')
        try:
            spacing_val = int(spacing)
        except (ValueError, TypeError):
            logger.error(f'Invalid spacing type: {spacing}')
            return False
        if spacing_val < 3 or spacing_val > 15:
            logger.error(f'Invalid spacing value: {spacing}')
            return False

        return True

    except Exception as e:
        logger.error(f'Error validating recording parameters: {e}')
        return False

def validate_class(params) -> bool:
    """
    Validate target count based on class label
    
    Args:
        params (dict): Recording parameters
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        class_label = int(params.get('class_label'))
        target_count = int(params.get('target_count'))
        angle = int(params.get('angle'))
        distance_t1 = int(params.get('distance_t1'))
        
        if class_label == 0:
            if target_count == 0 and angle == 0 and distance_t1 == -1:
                return True
            else:
                logger.error(f'Invalid recording parameter/s for absence class.')
                return False
        elif class_label == 1:
            if target_count in [1, 2, 3] and angle in [1, 2, 3, 4, 5] and distance_t1 >= 0:
                return True
            else:
                logger.error(f'Invalid recording parameter/s for presence class.')
                return False
        else:
            logger.error(f'Invalid class_label: {class_label}')
            return False
    except Exception as e:
        logger.error(f'Error validating target count: {e}')
        return False

def validate_obstruction(params) -> bool:
    """
    Validate obstruction type based on obstructed state
    
    Args:
        params (dict): Recording parameters
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        obstructed = int(params.get('obstructed'))
        obstruction = int(params.get('obstruction'))

        if obstructed == 0:
            # If not obstructed, obstruction should be 1
            if obstruction == 0:
                return True
            else:
                logger.error(f'Invalid obstruction type when not obstructed.')
                return False
        # If obstructed, obstruction should not be 1
        elif obstructed == 1:
            if obstruction in [1, 2, 3]:
                return True
            else:
                logger.error(f'Invalid obstruction type when obstructed.')
                return False
    except (ValueError, TypeError) as e:
        logger.error(f'Error validating obstruction type: {e}')
        return False
    
def validate_activity(params) -> bool:
    """
    Validate activity type based on state
    
    Args:
        params (dict): Recording parameters
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        state = int(params.get('state'))
        activity = int(params.get('activity'))

        if state == 0:
            # No state means no activity
            if activity == 0:
                return True
            else:
                logger.error(f'Invalid activity type when state is No State.')
                return False
        elif state == 1:
            # Motionless state allows only Stand or Sit
            if activity in [1, 2]:
                return True
            else:
                logger.error(f'Invalid activity type when state is Motionless.')
                return False
        elif state == 2:
            # Moving state allows Stand, Sit, Walking or Running
            if activity in [1, 2, 3, 4]:
                return True
            else:
                logger.error(f'Invalid activity type when state is Moving.')
                return False
    except (ValueError, TypeError) as e:
        logger.error(f'Error validating activity type: {e}')
        return False

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
