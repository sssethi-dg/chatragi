"""
ChatRagi Web Application

This Flask backend powers the ChatRagi chatbot interface. It includes
endpoints for:
- Homepage rendering
- Processing user queries
- Memory storage and retrieval
- Document listing
- Index refresh

The application integrates contextual memory retrieval, few-shot prompting,
and markdown formatting.
"""

import re

import markdown  # type: ignore[import]
from flask import Flask, jsonify, render_template, request
from markdown.extensions.fenced_code import FencedCodeExtension  # type: ignore

# fmt: off
from chatragi.utils.chat_memory import (
    fetch_all_memories,
    retrieve_memory,
    store_memory,
)

# fmt: on
from chatragi.utils.chatbot import query_engine, refresh_index
from chatragi.utils.db_utils import list_documents
from chatragi.utils.error_handler import handle_exception
from chatragi.utils.logger_config import logger
from chatragi.utils.persona import PersonaTone, apply_persona_tone

# Maximum number of citations to return
MAX_SOURCES = 3

app = Flask(__name__)

# Register global error handler
app.register_error_handler(Exception, handle_exception)


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
    Formats chatbot responses using Markdown and fixes common formatting
    inconsistencies.

    Args:
        response_text (str): Raw LLM-generated response text.

    Returns:
        str: HTML-formatted response with normalized structure.
    """

    def normalize_markdown_spacing(text: str) -> str:
        """
        Cleans up LLM output into better Markdown:
        - Converts numbered lists like "1. Item" into "- Item"
        - Avoids extra blank lines inside lists
        - Removes redundant blank lines
        """
        lines = text.splitlines()
        cleaned = []

        inside_section = False

        for line in lines:
            stripped = line.strip()

            # Convert numbered lists to dash
            if re.match(r"^\d+\.\s", stripped):
                stripped = "- " + stripped.split(". ", 1)[1]

            # Detect section headers like - **Details**:
            if re.match(r"-\s\*\*.*\*\*:", stripped):
                inside_section = True
                cleaned.append(stripped)
                continue

            # If inside a section and line starts with "-", indent it
            if inside_section and stripped.startswith("- "):
                cleaned.append("  " + stripped)
            else:
                inside_section = False
                cleaned.append(stripped)

        # ==== NEW CLEANUP: remove consecutive blank lines ====
        final_lines = []
        skip_next_blank = False
        for line in cleaned:
            if skip_next_blank and line == "":
                skip_next_blank = False
                continue

            final_lines.append(line)

            # If this is a section header like "- **Details**:"
            if re.match(r"-\s\*\*.*\*\*:", line.strip()):
                skip_next_blank = True

        return "\n".join(final_lines)

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


def format_structured_prompt(
    user_query: str,
    retrieved_memories: list[str],
) -> str:
    """
    Builds a structured prompt using a few-shot style pattern for professional
    tone, including relevant memory context.

    Args:
        user_query (str): The latest user question.
        retrieved_memories (list[str]): A list of memory snippets to include
        in the prompt.

    Returns:
        str: A complete prompt ready to be submitted to the LLM.
    """
    # Persona introduction (always professional)
    persona_instruction = (
        "You are ChatRagi, a highly professional and formal assistant. "
        "Answer in a polished, precise, and formal tone suitable for"
        "professional communication."
    )

    # Markdown formatting guide
    formatting_guide = (
        "Format your answers using Markdown with:\n"
        "- **Summary**: Provide a one or two sentence overview.\n"
        "- **Details**: Use bullet points for explanations or steps. "
        "Use indented lists inside Details sections where appropriate.\n"
        "- **Tips**: Offer best practices or optimization tips "
        "as bullet points.\n"
        "Ensure your answers are cleanly structured and easy to read."
    )

    examples = (
        "Examples:\n"
        "Q: What is vector search?\n"
        "A:\n"
        "- **Summary**: Vector search finds similar content using numeric "
        "representations.\n"
        "- **Details**: It compares semantic meaning using cosine similarity "
        "or distance metrics.\n"
        "- **Tips**: Use high-quality embeddings and consistent chunk "
        "sizes.\n\n"
        "Q: What is document chunking?\n"
        "A:\n"
        "- **Summary**: Chunking splits large documents into smaller parts.\n"
        "- **Details**: Chunks are embedded into a vector database to enable "
        "retrieval.\n"
        "- **Tips**: Use chunk overlap and balance size for best results.\n"
    )

    memory_block = ""
    if retrieved_memories:
        memory_block += "\nPrevious Context:\n"
        for i, mem in enumerate(retrieved_memories, 1):
            memory_block += f"\nMemory {i}:\n{mem.strip()}"

    return (
        f"{persona_instruction}\n\n"
        f"{formatting_guide}\n\n"
        f"{examples}"
        f"{memory_block}\n\n"
        f"Now answer this:\nQ: {user_query}\nA:"
    )


@app.route("/ask", methods=["POST"])
def ask():
    """
    Handles incoming user queries, enriches them with memory context,
    submits to the LLM engine, formats the response, and returns it.

    Request JSON:
        {
            "query": "Your question here"
        }

    Response JSON:
        {
            "answer": "<Markdown formatted HTML>",
            "raw_answer": "<plain model text>",
            "citations": ["source1", "source2", "source3"]
        }
    """
    try:
        data = request.get_json()
        user_query = data.get("query", "").strip()
        persona = data.get("persona", "default").strip().lower()

        if not user_query:
            logger.error("No query provided in request.")
            return jsonify({"error": "No query provided"}), 400

        # Validate persona
        try:
            tone = PersonaTone(persona)
        except ValueError:
            tone = PersonaTone.DEFAULT

        # === Decide prompt building based on persona ===
        if tone == PersonaTone.PROFESSIONAL:
            # Use structured Markdown prompt for professional tone
            relevant_memories = retrieve_memory(user_query)
            mod_prompt = format_structured_prompt(
                user_query,
                relevant_memories,
            )
        else:
            # Use natural freeform persona prompts
            mod_prompt = apply_persona_tone(user_query, tone)

        # Query LLM
        response = query_engine.query(mod_prompt)
        raw_answer = getattr(response, "response", str(response)).strip()

        # Handle citations (same)
        citations = []
        source_nodes = getattr(response, "source_nodes", [])
        seen = set()
        for node in source_nodes:
            metadata = getattr(node.node, "metadata", {})
            source = metadata.get("file_name") or metadata.get("source")
            if source and source not in seen:
                citations.append(source)
                seen.add(source)
            if len(citations) >= MAX_SOURCES:
                break

        # Format output for frontend
        formatted_answer = format_response(raw_answer)

        # Store memory
        store_memory(
            user_query=user_query,
            response=raw_answer,
            is_important=False,
        )

        return jsonify(
            {
                "answer": formatted_answer,
                "raw_answer": raw_answer,
                "citations": citations,
            }
        )

    except Exception as e:
        logger.exception("Failed to process query: %s", e)
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500


@app.route("/store-memory", methods=["POST"])
def store_memory_route():
    """
    Stores chatbot interaction (user + response) in memory. Optionally marks
    it as important.

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
                jsonify(
                    {"error": "Both 'user_query' and 'response' are required"}
                ),
                400,
            )

        store_memory(user_query, response, is_important)
        return jsonify(
            {"status": "success", "message": "Memory stored successfully."}
        )
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
        JSON: List of memory entries including timestamp, content,
        and importance.
    """
    try:
        memories = fetch_all_memories()
        return jsonify({"memories": memories})
    except Exception as e:
        logger.exception("Failed to retrieve memories: %s", e)
        return (
            jsonify({"error": f"Failed to retrieve memories: {str(e)}"}),
            500,
        )


if __name__ == "__main__":
    try:
        app.run(debug=True)
    except Exception as e:
        logger.exception("Unexpected error starting the Flask app: %s", e)
