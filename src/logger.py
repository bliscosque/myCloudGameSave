"""
Logging module
Handles application logging with file and console output
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """Application logger with file and console output"""
    
    def __init__(self, log_dir: Path, log_level: str = "info", verbose: bool = False):
        """Initialize logger
        
        Args:
            log_dir: Directory for log files
            log_level: Log level (debug, info, warning, error)
            verbose: Enable verbose console output
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "gamesync.log"
        self.log_level = self._parse_level(log_level)
        self.verbose = verbose
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger("gamesync")
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        self.logger.handlers.clear()  # Clear any existing handlers
        
        # File handler with rotation (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = logging.DEBUG if verbose else self.log_level
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _parse_level(self, level: str) -> int:
        """Parse log level string to logging constant
        
        Args:
            level: Log level string
            
        Returns:
            Logging level constant
        """
        levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR
        }
        return levels.get(level.lower(), logging.INFO)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def exception(self, message: str):
        """Log exception with traceback"""
        self.logger.exception(message)


# Global logger instance
_logger: Optional[Logger] = None


def init_logger(log_dir: Path, log_level: str = "info", verbose: bool = False) -> Logger:
    """Initialize global logger
    
    Args:
        log_dir: Directory for log files
        log_level: Log level (debug, info, warning, error)
        verbose: Enable verbose console output
        
    Returns:
        Logger instance
    """
    global _logger
    _logger = Logger(log_dir, log_level, verbose)
    return _logger


def get_logger() -> Logger:
    """Get global logger instance
    
    Returns:
        Logger instance
        
    Raises:
        RuntimeError: If logger not initialized
    """
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call init_logger() first.")
    return _logger
