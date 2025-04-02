"""
Logger Configuration Module

This module sets up the logging configuration for the ChatRagi chatbot application.
It configures logging to output messages both to a file and the console.
"""

import logging

from chatragi.config import LOG_FILE


def setup_logger() -> logging.Logger:
    """
    Configures and returns a logger instance for the ChatRagi application.

    The logger is set up to log messages at the INFO level by default. It uses a
    specific format that includes the timestamp, log level, logger name, and the
    message. Logs are written both to a file and to the console.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Configure the logging settings
    logging.basicConfig(
        level=logging.INFO,  # Change to logging.DEBUG for more detailed logs
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="a"),  # Log messages to a file
            logging.StreamHandler(),  # Log messages to the console
        ],
    )

    # Create and return a logger instance with the name "ChatRagi"
    return logging.getLogger("ChatRagi")


# Instantiate the logger for use in the application
logger = setup_logger()
