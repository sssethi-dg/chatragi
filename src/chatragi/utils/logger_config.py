"""
Logging configuration for the ChatRagi application.

Includes both file-based and colored console logging using a custom formatter.
Supports log rotation and minimizes noise from third-party libraries.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from chatragi.config import LOG_FILE


class ColorFormatter(logging.Formatter):
    """
    Custom formatter for applying ANSI colors to console logs
    based on log level (INFO, DEBUG, etc).
    """

    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with color codes.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: Formatted log message string with optional ANSI color.
        """
        log_fmt = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        if record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            log_fmt = f"{color}{log_fmt}{self.RESET}"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger() -> logging.Logger:
    """
    Configures and returns a logger instance for the ChatRagi application.

    Returns:
        logging.Logger: Fully configured logger instance.
    """
    logger = logging.getLogger("ChatRagi")
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    # Prevent duplicate handlers if setup_logger is called more than once
    if not logger.handlers:
        # Rotating log file (max 5MB per file, keep 3 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 5MB
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Console logging with color formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter())

        # Attach both handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Suppress noisy logs from third-party modules
        logging.getLogger("pdfminer").setLevel(logging.ERROR)

    return logger


# Instantiate the configured logger
logger = setup_logger()
