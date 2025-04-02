"""
Global Error Handler Module for ChatRagi

This module provides a centralized exception handler for Flask routes.
It logs unhandled exceptions using the configured logger and returns a standardized
JSON error response to the client.
"""

from flask import jsonify

from chatragi.utils.logger_config import logger


def handle_exception(e):
    """
    Handle unexpected exceptions in Flask routes.

    This function logs detailed information about the exception using the
    centralized logger and returns a JSON response with a generic error message.
    The HTTP status code 500 indicates an internal server error.

    Args:
        e (Exception): The exception that was raised.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code (500).
    """
    # Log the exception details along with the traceback for debugging purposes.
    logger.exception("Unhandled exception occurred", exc_info=e)

    # Return a generic error message to the client without exposing internal details.
    return jsonify({"error": "An unexpected error occurred. Please try again."}), 500
