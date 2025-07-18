"""
Chat Memory Module for ChatRagi

Handles storing, retrieving, and ranking chatbot memory entries.
Includes deduplication using memory_key, time decay scoring, and importance
flagging.
"""

import re
from datetime import datetime
from hashlib import sha256

from chatragi.utils.db_utils import memory_collection
from chatragi.utils.logger_config import logger


def strip_sources_section(text: str) -> str:
    """
    Removes the 'Sources:' section (and beyond) from the input text.

    Args:
        text (str): The input text.

    Returns:
        str: Cleaned text without the sources section.
    """
    return re.split(r"(?i)Sources?:", text)[0].strip()


def normalize_text(text: str) -> str:
    """
    Normalizes text for comparison by:
    - Removing Markdown symbols
    - Lowercasing
    - Collapsing whitespace

    Args:
        text (str): The input text.

    Returns:
        str: Normalized text.
    """
    text = re.sub(r"[*_`~#>\\-]+", "", text)
    text = text.replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def generate_memory_key(user_query: str, response: str) -> str:
    """
    Generates a SHA256 memory key based on normalized query and response.

    Args:
        user_query (str): Normalized user query.
        response (str): Normalized AI response.

    Returns:
        str: Generated memory key.
    """
    combined = f"{user_query}|||{response}"
    return sha256(combined.encode("utf-8")).hexdigest()


def store_memory(user_query: str, response: str, is_important: bool) -> None:
    """
    Stores a chatbot query-response pair into memory with deduplication.

    - Auto-saves a new memory if no match exists.
    - Updates the "important" flag if an existing match is found.

    Args:
        user_query (str): Raw user input.
        response (str): Raw AI response.
        is_important (bool): Whether to mark the memory as important.
    """
    user_query = strip_sources_section(user_query)
    response = strip_sources_section(response)

    normalized_query = normalize_text(user_query)
    normalized_response = normalize_text(response)

    memory_key = generate_memory_key(normalized_query, normalized_response)
    memory_entry = f"User: {normalized_query}\nAI: {normalized_response}"

    # Debugging information
    # logger.debug("Original query: %s", user_query)
    # logger.debug("Cleaned query: %s", normalized_query)
    # logger.debug("Cleaned response: %s", normalized_response)
    # logger.debug("Generated memory key: %s", memory_key)

    try:
        existing_results = memory_collection.get()
        existing_match_id = None
        existing_metadata = None

        for doc, meta, doc_id in zip(
            existing_results.get("documents", []),
            existing_results.get("metadatas", []),
            existing_results.get("ids", []),
        ):
            meta = meta[0] if isinstance(meta, list) and meta else meta
            if not isinstance(meta, dict):
                continue

            if meta.get("memory_key") == memory_key:
                existing_match_id = doc_id
                existing_metadata = meta
                break

        if existing_match_id:
            logger.debug("Existing match found: %s", existing_match_id)

            if (
                isinstance(existing_metadata, dict)
                and not existing_metadata.get("important", False)
                and is_important
            ):
                try:
                    memory_collection.update(
                        ids=[existing_match_id],
                        metadatas=[
                            {
                                "user_query": normalized_query,
                                "timestamp": existing_metadata.get(
                                    "timestamp"
                                ),
                                "memory_key": memory_key,
                                "important": True,
                            }
                        ],
                    )
                    logger.info(
                        "Updated memory to important: %s", existing_match_id
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to update memory importance: %s", e
                    )
            else:
                logger.info("Duplicate found. No update needed.")
            return

        # No existing match: store new memory
        timestamp = datetime.utcnow().isoformat()
        new_id = f"{hash(memory_entry)}-{timestamp}"

        memory_collection.add(
            documents=[memory_entry],
            metadatas=[
                {
                    "user_query": normalized_query,
                    "memory_key": memory_key,
                    "timestamp": timestamp,
                    "important": is_important,
                }
            ],
            ids=[new_id],
        )
        logger.info("Stored new memory with ID: %s", new_id)

    except Exception as e:
        logger.exception("Failed to store memory: %s", e)


def retrieve_memory(user_query: str) -> list:
    """
    Retrieves relevant chatbot memory entries based on a user query.

    Scoring favors important and recent memories.

    Args:
        user_query (str): The input query.

    Returns:
        list: Top 3 memory entries (as strings).
    """
    try:
        results = memory_collection.query(
            query_texts=[user_query], n_results=5
        )
    except Exception as e:
        logger.exception("Error querying memory_collection: %s", e)
        return []

    scored_results = []

    if results and results.get("documents"):
        for doc, meta in zip(results["documents"], results["metadatas"]):
            meta = meta[0] if isinstance(meta, list) and meta else meta

            if not isinstance(meta, dict):
                logger.warning("Unexpected metadata format: %s", meta)
                continue

            timestamp = meta.get("timestamp")
            if not timestamp:
                logger.warning(
                    "Missing timestamp in memory metadata: %s", meta
                )
                continue

            try:
                stored_time = datetime.fromisoformat(timestamp)
                decay_factor = 1 / (1 + (datetime.utcnow() - stored_time).days)
                doc_str = "\n".join(doc) if isinstance(doc, list) else str(doc)
                importance_score = 2 if meta.get("important", False) else 1
                combined_score = importance_score + decay_factor

                scored_results.append((doc_str.strip(), combined_score))
            except Exception as e:
                logger.exception(
                    "Error processing memory entry %s: %s", meta, e
                )

    scored_results.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored_results[:3]]


def fetch_all_memories() -> list:
    """
    Fetches all stored memory entries from the database.

    Returns:
        list: List of memory records (each with user_query, timestamp,
        importance flag, and conversation text).
    """
    try:
        results = memory_collection.get()
        memories = []

        for doc, meta in zip(
            results.get("documents", []), results.get("metadatas", [])
        ):
            meta = meta[0] if isinstance(meta, list) and meta else meta
            if not isinstance(meta, dict):
                continue

            memories.append(
                {
                    "user_query": meta.get("user_query", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "important": meta.get("important", False),
                    "conversation": (
                        "\n".join(doc) if isinstance(doc, list) else str(doc)
                    ),
                }
            )

        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return memories

    except Exception as e:
        logger.exception("Error fetching all memories: %s", e)
        return []
