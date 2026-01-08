"""
Logging module for Crypto Morning Pulse Bot.
Handles file and console logging with proper formatting.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from src.config import LOG_DIR, LOG_LEVEL


class BotLogger:
    """Centralized logging manager for the bot."""
    
    _instance: Optional["BotLogger"] = None
    
    def __new__(cls) -> "BotLogger":
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize logger with file and console handlers."""
        if self._initialized:
            return
        
        self.logger = logging.getLogger("crypto_bot")
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Create formatters
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (daily rotation)
        log_filename = os.path.join(
            LOG_DIR,
            f"crypto_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self._initialized = True
    
    def get_logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self.logger
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)


# Global logger instance
logger = BotLogger().get_logger()
