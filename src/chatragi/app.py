"""
ChatRagi Web Application

This Flask backend powers the ChatRagi chatbot interface. It includes endpoints for:
- Homepage rendering
- Processing user queries
- Memory storage and retrieval
- Document listing
- Index refresh

The application integrates contextual memory retrieval, few-shot prompting, and markdown formatting.
"""

import markdown  # type: ignore[import]
from flask import Flask, jsonify, render_template, request
from markdown.extensions.fenced_code import FencedCodeExtension  # type: ignore[import]

from chatragi.utils.chat_memory import fetch_all_memories, retrieve_memory, store_memory
from chatragi.utils.chatbot import ask_chatbot, refresh_index
from chatragi.utils.db_utils import list_documents
from chatragi.utils.logger_config import logger  # Centralized logger

app = Flask(__name__)


@app.route("/")
def home():
    """
    Renders the home page for the chatbot interface.

    Returns:
        str: Rendered HTML template.
    """
    try:
        return render_template("index.html")
    except Exception as e:
        logger.exception("Error rendering home page: %s", e)
        return "Error rendering home page.", 500


def format_response(response_text: str) -> str:
    """
    Formats chatbot responses using Markdown and fixes common formatting inconsistencies.

    This function:
    - Converts numbered lists to markdown-style bullets
    - Collapses redundant blank lines inside list blocks
    - Maintains consistent formatting for code blocks

    Args:
        response_text (str): Raw LLM-generated response text.

    Returns:
        str: HTML-formatted response with normalized structure.
    """

    # Normalize markdown formatting and spacing
    def normalize_markdown_spacing(text: str) -> str:
        lines = text.splitlines()
        cleaned: list[str] = []

        for line in lines:
            stripped = line.strip()

            # Convert numbered list items to dash format (e.g., "1. Item" → "- Item")
            if stripped and any(stripped.startswith(f"{i}. ") for i in range(1, 10)):
                stripped = "- " + stripped.split(". ", 1)[1]

            # Avoid extra blank lines after bullet items
            if stripped == "" and cleaned and cleaned[-1].strip().startswith("-"):
                continue

            # Preserve code blocks and normal lines
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
    Builds a structured prompt using a few-shot style pattern, including relevant memory context.

    Args:
        user_query (str): The latest user question.
        retrieved_memories (list[str]): A list of memory snippets to include in the prompt.

    Returns:
        str: A complete prompt ready to be submitted to the LLM.
    """
    intro = (
        "You are ChatRagi, a helpful assistant. Format your answers clearly using Markdown with:\n"
        "- **Summary**\n- **Details**\n- **Tips** (if applicable)\n"
    )

    examples = (
        "Examples:\n"
        "Q: What is vector search?\n"
        "A:\n"
        "- **Summary**: Vector search finds similar content using numeric representations.\n"
        "- **Details**: It compares semantic meaning using cosine similarity or distance metrics.\n"
        "- **Tips**: Use high-quality embeddings and consistent chunk sizes.\n\n"
        "Q: What is document chunking?\n"
        "A:\n"
        "- **Summary**: Chunking splits large documents into smaller parts.\n"
        "- **Details**: Chunks are embedded into a vector database to enable retrieval.\n"
        "- **Tips**: Use chunk overlap and balance size for best results.\n"
    )

    memory_block = ""
    if retrieved_memories:
        memory_block += "\nPrevious Context:\n"
        for i, mem in enumerate(retrieved_memories, 1):
            memory_block += f"\nMemory {i}:\n{mem.strip()}"

    return f"{intro}\n{examples}{memory_block}\n\nNow answer this:\nQ: {user_query}\nA:"


@app.route("/ask", methods=["POST"])
def ask():
    """
    Handles incoming user queries, enriches them with memory context,
    submits to the LLM engine via ask_chatbot(), formats the response, and returns it.

    Request JSON:
        {
            "query": "Your question here"
        }

    Returns:
        JSON response:
        {
            "answer": "<formatted markdown HTML>",
            "citations": [<source names>]
        }
    """
    try:
        data = request.get_json()
        user_query = data.get("query", "").strip()

        if not user_query:
            logger.error("No query provided in request.")
            return jsonify({"error": "No query provided"}), 400

        # Step 1: Retrieve memory context
        relevant_memories = retrieve_memory(user_query)

        # Step 2: Build structured prompt with memory context
        full_prompt = format_structured_prompt(user_query, relevant_memories)

        # Step 3: Ask chatbot and get answer + citations
        result = ask_chatbot(full_prompt)

        # Step 4: Format the markdown output to HTML
        formatted_answer = format_response(result["answer"])
        citations = result.get("citations", [])

        # Optional debug logging
        if app.debug:
            if relevant_memories:
                for i, mem in enumerate(relevant_memories[:3], 1):
                    logger.debug("Retrieved Memory %d:\n%s", i, mem)
            if citations:
                logger.debug("Retrieved Citations: %s", citations)

        return jsonify({"answer": formatted_answer, "citations": citations})

    except Exception as e:
        logger.exception("Failed to process query '%s': %s", data.get("query", ""), e)
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500


@app.route("/store-memory", methods=["POST"])
def store_memory_route():
    """
    Stores chatbot interaction (user + response) in memory. Optionally marks it as important.

    Request JSON:
        {
            "user_query": "What is a vector store?",
            "response": "A vector store is...",
            "is_important": true
        }

    Returns:
        JSON: Success/failure status.
    """
    try:
        data = request.get_json()
        user_query = data.get("user_query")
        response = data.get("response")
        is_important = data.get("is_important", False)

        if not user_query or not response:
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
    Refreshes the vector index by re-ingesting source documents.

    Returns:
        JSON: Confirmation message.
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
    Lists all ingested documents tracked by the system.

    Returns:
        JSON: List of document filenames and metadata.
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
    Fetches all stored chatbot memories for user review.

    Returns:
        JSON: List of memory entries including timestamp, content, and importance.
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
