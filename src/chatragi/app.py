"""
ChatRagi Application

This module implements the web backend for the ChatRagi chatbot. It sets up several
HTTP endpoints to serve the chatbot's home page, process user queries, store conversation
memories, refresh the document index, and list stored documents and memories.
"""

# import os
import markdown  # type: ignore[import]
from flask import Flask, jsonify, render_template, request

# from markdown.extensions.codehilite import CodeHiliteExtension # type: ignore[import]
from markdown.extensions.fenced_code import FencedCodeExtension  # type: ignore[import]

from chatragi.utils.chat_memory import fetch_all_memories, store_memory
from chatragi.utils.chatbot import query_engine, refresh_index
from chatragi.utils.db_utils import list_documents
from chatragi.utils.logger_config import (  # Centralized logger for the application
    logger,
)

app = Flask(__name__)


@app.route("/")
def home():
    """
    Renders the home page for the chatbot interface.

    Returns:
        str: Rendered HTML page.
    """
    try:
        return render_template("index.html")
    except Exception as e:
        logger.exception("Error rendering home page: %s", e)
        return "Error rendering home page.", 500


def format_response(response_text: str) -> str:
    """
    Formats chatbot responses using Markdown with fenced code blocks.

    Args:
        response_text (str): Raw LLM output.

    Returns:
        str: HTML with proper <pre><code>...</code></pre> wrapping.
    """
    try:
        return markdown.markdown(
            response_text, extensions=[FencedCodeExtension()], output_format="html5"
        )
    except Exception as e:
        logger.exception("Error formatting response text: %s", e)
        return response_text


@app.route("/ask", methods=["POST"])
def ask():
    """
    Processes user queries and returns AI-generated responses.

    Request Body (JSON):
        - query (str): The user's input question.

    Returns:
        Response: JSON object containing the formatted AI response, score, and metadata.
    """
    try:
        data = request.get_json()
        user_query = data.get("query", "")

        if not user_query:
            logger.error("No query provided in request.")
            return jsonify({"error": "No query provided"}), 400

        # Query the AI engine
        response = query_engine.query(user_query)

        # Format the response text using Markdown
        formatted_answer = format_response(response.response)

        formatted_response = {
            "answer": formatted_answer,
            "score": getattr(response, "score", None),
            "metadata": getattr(response, "metadata", {}),
        }

        return jsonify(formatted_response)
    except Exception as e:
        logger.exception("Failed to process query '%s': %s", data.get("query"), e)
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500


@app.route("/store-memory", methods=["POST"])
def store_memory_route():
    """
    Stores chatbot conversations in memory with an option to mark them as important.

    Request Body (JSON):
        - user_query (str): The user's original query.
        - response (str): The chatbot's response.
        - is_important (bool, optional): Indicates if the memory should be marked as important.

    Returns:
        Response: JSON object indicating success or failure of the operation.
    """
    try:
        data = request.get_json()
        user_query = data.get("user_query")
        response = data.get("response")
        is_important = data.get("is_important", False)

        if not user_query or not response:
            logger.error("Missing user_query or response in memory store request.")
            return (
                jsonify({"error": "Both 'user_query' and 'response' are required"}),
                400,
            )

        store_memory(user_query, response, is_important)
        return jsonify({"status": "success", "message": "Memory stored successfully."})
    except Exception as e:
        logger.exception("Failed to store memory: %s", e)
        return jsonify({"error": f"Failed to store memory: {str(e)}"}), 500


@app.route("/refresh", methods=["POST"])
def refresh():
    """
    Refreshes the document index to incorporate any new data.

    Returns:
        Response: JSON object confirming the refresh operation.
    """
    try:
        refresh_index()
        return jsonify({"response": "Index refreshed successfully."})
    except Exception as e:
        logger.exception("Failed to refresh index: %s", e)
        return jsonify({"error": f"Failed to refresh index: {str(e)}"}), 500


@app.route("/list-documents", methods=["GET"])
def list_all_documents():
    """
    Retrieves a list of documents stored in the database.

    Returns:
        Response: JSON object containing the list of documents.
    """
    try:
        documents = list_documents()
        return jsonify({"documents": documents})
    except Exception as e:
        logger.exception("Failed to list documents: %s", e)
        return jsonify({"error": f"Failed to list documents: {str(e)}"}), 500


@app.route("/all-memories", methods=["GET"])
def all_memories():
    """
    Retrieves all stored chatbot memories.

    Returns:
        Response: JSON object containing a list of all stored memories.
    """
    try:
        memories = fetch_all_memories()
        return jsonify({"memories": memories})
    except Exception as e:
        logger.exception("Failed to retrieve memories: %s", e)
        return jsonify({"error": f"Failed to retrieve memories: {str(e)}"}), 500


if __name__ == "__main__":
    # Run the Flask app in debug mode
    try:
        app.run(debug=True)
    except Exception as e:
        logger.exception("Unexpected error starting the Flask app: %s", e)
