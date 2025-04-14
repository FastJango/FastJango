"""
Logging configuration for FastJango
"""

import logging
import sys
from pathlib import Path
from rich.logging import RichHandler


def setup_logging(level=logging.INFO, log_file=None):
    """
    Set up logging configuration for FastJango.
    
    Args:
        level: The logging level (default: INFO)
        log_file: Optional path to a log file
    """
    # Create logger
    logger = logging.getLogger("fastjango")
    logger.setLevel(level)
    logger.propagate = False
    
    # Clear existing handlers
    logger.handlers = []
    
    # Configure console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        try:
            log_path = Path(log_file)
            
            # Ensure log directory exists
            if not log_path.parent.exists():
                log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to configure file logging: {str(e)}")
    
    # Configure other loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set up exception hooks
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Let the system handle keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    return logger


class Logger:
    """
    Logger utility class for FastJango applications.
    
    Example:
        logger = Logger(__name__)
        logger.info("This is an info message")
        logger.error("This is an error", exc_info=True)
    """
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def debug(self, message, **kwargs):
        self.logger.debug(message, **kwargs)
    
    def info(self, message, **kwargs):
        self.logger.info(message, **kwargs)
    
    def warning(self, message, **kwargs):
        self.logger.warning(message, **kwargs)
    
    def error(self, message, **kwargs):
        self.logger.error(message, **kwargs)
    
    def critical(self, message, **kwargs):
        self.logger.critical(message, **kwargs)
    
    def exception(self, message, **kwargs):
        self.logger.exception(message, **kwargs) 