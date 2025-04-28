"""
Global Error Handler Module for ChatRagi

This module provides a centralized exception handler for Flask routes.
It logs unhandled exceptions using the configured logger and returns a standardized
JSON error response to the client, including a unique error ID for easier debugging
and basic categorization of known user errors vs internal server errors.
"""

import uuid

from flask import jsonify
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from chatragi.utils.logger_config import logger


def build_error_response(status: str, message: str, error_id: str, code: int):
    """
    Helper function to build standardized JSON error responses.

    Args:
        status (str): Error type, e.g., "client_error" or "server_error".
        message (str): User-facing error message.
        error_id (str): Unique ID for this error.
        code (int): HTTP status code to return.

    Returns:
        tuple: A tuple of (JSON response, HTTP status code)
    """
    payload = {
        "status": status,
        "message": message,
        "error_id": error_id,
    }
    return jsonify(payload), code


def handle_exception(e):
    """
    Handle unexpected exceptions in Flask routes.

    Logs the exception details with a unique error ID and returns
    a user-friendly JSON error response.

    Categorizes errors into:
    - "client_error" for known 4xx issues
    - "server_error" for unexpected 5xx issues
    """
    error_id = str(uuid.uuid4())

    # Client error detection
    if isinstance(e, (BadRequest, NotFound, Forbidden)):
        logger.warning("Client error occurred. Error ID: %s", error_id, exc_info=e)
        message = str(e.description) if hasattr(e, "description") else str(e)
        return build_error_response(
            "client_error", message, error_id, e.code if hasattr(e, "code") else 400
        )

    # Otherwise, treat as server error
    logger.exception(
        "Unhandled server error occurred. Error ID: %s", error_id, exc_info=e
    )
    return build_error_response(
        "server_error",
        "An unexpected error occurred. Please try again later.",
        error_id,
        500,
    )
