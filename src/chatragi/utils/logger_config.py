import logging
import sys
from logging.handlers import RotatingFileHandler

from chatragi.config import LOG_FILE


class ColorFormatter(logging.Formatter):
    """
    Custom formatter for adding ANSI colors to console logs
    in development mode.
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
        Format a log record with ANSI colors based on log level.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message string.
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
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("ChatRagi")
    logger.setLevel(logging.INFO)  # Set default log level

    if not logger.handlers:
        # Rotating File Handler (5 MB max, keep 3 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 5MB
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Console Handler with color output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter())

        # Attach handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Reduce log noise from other libraries
        logging.getLogger("pdfminer").setLevel(logging.ERROR)

    return logger


# Instantiate the logger for use in the application
logger = setup_logger()
