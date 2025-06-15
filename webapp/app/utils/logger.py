import logging

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and logging level.
    
    Args:
        name (str): The name of the logger.
        level (int): The logging level (default is logging.INFO).
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler with formatter
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s: %(levelname)s - %(message)s')
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate = False
    
    return logger
