"""
ChatRagi Application

This module implements the web backend for the ChatRagi chatbot. It sets up
endpoints to serve the chatbot interface, process user queries, store and retrieve
memories, refresh document index, and list stored documents.
"""

import re
from datetime import datetime
from typing import List

import markdown  # type: ignore[import]
from flask import Flask, jsonify, render_template, request
from markdown.extensions.fenced_code import FencedCodeExtension  # type: ignore[import]

from chatragi.utils.chat_memory import fetch_all_memories, retrieve_memory, store_memory
from chatragi.utils.chatbot import query_engine, refresh_index
from chatragi.utils.db_utils import list_documents
from chatragi.utils.logger_config import logger  # Centralized logger for the app

app = Flask(__name__)


@app.route("/")
def home():
    """
    Renders the main chatbot interface page.

    Returns:
        str: Rendered HTML page for the frontend.
    """
    try:
        return render_template("index.html")
    except Exception as e:
        logger.exception("Error rendering home page: %s", e)
        return "Error rendering home page.", 500


def normalize_markdown_spacing(text: str) -> str:
    """
    Normalizes spacing and formatting in markdown text for consistent rendering.

    This includes:
    - Ensuring a blank line after summary/details/tips headers
    - Fixing spacing between bullets
    - Cleaning up malformed formatting artifacts

    Args:
        text (str): Raw Markdown content.

    Returns:
        str: Cleaned Markdown with improved spacing.
    """
    # Ensure headers like "**Summary:**" or "**Tips:**" are followed by a newline
    text = re.sub(r"(\*\*Summary:\*\*)", r"\1\n", text)
    text = re.sub(r"(\*\*Details:\*\*)", r"\1\n", text)
    text = re.sub(r"(\*\*Tips:\*\*)", r"\1\n", text)

    # Add newline before each bullet if missing
    text = re.sub(r"(?<!\n)- ", r"\n- ", text)

    # Ensure code blocks aren't jammed up (safeguard if needed)
    text = text.replace("```", "\n```\n")

    # Fix odd line-wrapping where tips are concatenated at the end of the prior section
    text = re.sub(r"(\.\s*)(\*\*Tips:\*\*)", r"\1\n\n\2", text)

    return text.strip()


def format_response(response_text: str) -> str:
    """
    Formats chatbot responses using Markdown and fixes common formatting inconsistencies.

    Args:
        response_text (str): Raw LLM-generated response text.

    Returns:
        str: HTML-formatted response with normalized structure.
    """

    def normalize_markdown_spacing(text: str) -> str:
        lines = text.splitlines()
        cleaned: List[str] = []

        for line in lines:
            stripped = line.strip()

            # Remove leading Markdown-style numbers (1., 2., etc.) and normalize to "-"
            if stripped and any(stripped.startswith(f"{i}. ") for i in range(1, 10)):
                stripped = "- " + stripped.split(". ", 1)[1]

            # Remove excessive blank lines within bullets
            if stripped == "" and cleaned and cleaned[-1].strip().startswith("-"):
                continue

            # Reduce over-indented code blocks
            if stripped.startswith("```") or stripped.startswith("    "):
                cleaned.append(stripped)
            else:
                cleaned.append(stripped)

        return "\n".join(cleaned)

    try:
        cleaned_text = normalize_markdown_spacing(response_text)
        return markdown.markdown(
            cleaned_text,
            extensions=[FencedCodeExtension()],
            output_format="html5",
        )
    except Exception as e:
        logger.exception("Error formatting response text: %s", e)
        return response_text


def format_structured_prompt(user_query: str, retrieved_memories: list[str]) -> str:
    """
    Creates a structured prompt using memory snippets and few-shot examples.

    Args:
        user_query (str): User's question.
        retrieved_memories (list[str]): Relevant prior memory entries.

    Returns:
        str: Full prompt string to send to the LLM.
    """
    intro = (
        "You are ChatRagi, a helpful assistant. Format your answers using:\n"
        "- Summary\n- Details\n- Tips (if applicable)\n"
    )

    examples = (
        "Examples:\n"
        "Q: What is vector search?\n"
        "A:\n"
        "- Summary: Vector search finds similar content using numeric representations.\n"
        "- Details: It compares semantic meaning using cosine similarity or distance metrics.\n"
        "- Tips: Use quality embeddings and tune your retrieval threshold.\n\n"
        "Q: What is document chunking?\n"
        "A:\n"
        "- Summary: Chunking splits large documents into smaller parts.\n"
        "- Details: These parts are stored as vectors in a database to allow semantic retrieval.\n"
        "- Tips: Use overlap and consistent chunk size to retain meaning.\n"
    )

    memory_block = ""
    if retrieved_memories:
        memory_block = "\nPrevious Context:\n"
        for i, mem in enumerate(retrieved_memories, 1):
            memory_block += f"\nMemory {i}:\n{mem.strip()}"

    return f"{intro}\n{examples}{memory_block}\n\nNow answer this:\nQ: {user_query}\nA:"


@app.route("/ask", methods=["POST"])
def ask():
    """
    Handles user query, injects retrieved memory context, formats a structured prompt,
    and returns the AI-generated response.

    Request Body (JSON):
        - query (str): The user's input question.

    Returns:
        JSON response with formatted answer, score, and optional metadata.
    """
    try:
        data = request.get_json()
        user_query = data.get("query", "")

        if not user_query:
            logger.error("No query provided in request.")
            return jsonify({"error": "No query provided"}), 400

        # Step 1: Retrieve memory
        relevant_memories = retrieve_memory(user_query)

        # Step 2: Log top N memory snippets with timestamps for debugging
        MAX_LOG_MEMORIES = 3
        if relevant_memories:
            memory_log_lines = []
            for i, mem in enumerate(relevant_memories[:MAX_LOG_MEMORIES], 1):
                timestamp_line = (
                    f"[Memory {i} - Timestamp: {datetime.utcnow().isoformat()}]"
                )
                memory_log_lines.append(f"{timestamp_line}\n{mem.strip()}")
            logger.debug("Retrieved Memory Context:\n%s", "\n\n".join(memory_log_lines))
        else:
            logger.debug("No relevant memory retrieved for query: '%s'", user_query)

        # Step 3: Build memory-aware structured prompt
        full_prompt = format_structured_prompt(user_query, relevant_memories)
        logger.debug("Injected Prompt:\n%s", full_prompt)

        # Step 4: Query the LLM engine
        response = query_engine.query(full_prompt)
        formatted_answer = format_response(response.response)

        # Step 5: Construct response payload
        return jsonify(
            {
                "answer": formatted_answer,
                "score": getattr(response, "score", None),
                "metadata": getattr(response, "metadata", {}),
            }
        )

    except Exception as e:
        logger.exception("Failed to process query '%s': %s", data.get("query"), e)
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500


@app.route("/store-memory", methods=["POST"])
def store_memory_route():
    """
    Saves a user-AI conversation to memory, optionally marking it as important.

    Request JSON:
        - user_query (str): The user's original question.
        - response (str): The AI's response.
        - is_important (bool): Whether the entry is flagged as important.

    Returns:
        JSON: Success or error status.
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
    Refreshes the document index for new or updated content.

    Returns:
        JSON: Success or failure message.
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
    Retrieves all stored document metadata from the database.

    Returns:
        JSON: List of indexed documents.
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
    Retrieves all saved memory entries from the database.

    Returns:
        JSON: List of memory entries with metadata.
    """
    try:
        memories = fetch_all_memories()
        return jsonify({"memories": memories})
    except Exception as e:
        logger.exception("Failed to retrieve memories: %s", e)
        return jsonify({"error": f"Failed to retrieve memories: {str(e)}"}), 500


if __name__ == "__main__":
    try:
        app.run(debug=True)
    except Exception as e:
        logger.exception("Unexpected error starting the Flask app: %s", e)
