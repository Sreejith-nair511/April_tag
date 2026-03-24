import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str, log_file: str = "precision_landing.log", level=logging.INFO) -> logging.Logger:
    """Sets up a thread-safe logger."""
    
    # Ensure logs directory exists if running from elsewhere
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(threadName)s] - %(levelname)s - %(message)s'
        )

        # File Handler
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
