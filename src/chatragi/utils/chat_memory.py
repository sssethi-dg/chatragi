"""
Chat Memory Module for ChatRagi

Handles storing, retrieving, and ranking chatbot memory entries. 
Supports deduplication, time decay, and importance scoring for context-aware responses.
"""

from datetime import datetime

from chatragi.utils.db_utils import memory_collection
from chatragi.utils.logger_config import logger


def retrieve_memory(user_query: str) -> list:
    """
    Retrieves relevant chatbot memory entries related to the current query.

    Uses a combination of recency and importance to score and return the top responses.

    Args:
        user_query (str): The user's input query.

    Returns:
        list: Top 3 scored memory entries (as strings).
    """
    try:
        results = memory_collection.query(query_texts=[user_query], n_results=5)
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
                logger.warning("Missing timestamp in memory metadata: %s", meta)
                continue

            try:
                stored_time = datetime.fromisoformat(timestamp)
                decay_factor = 1 / (1 + (datetime.utcnow() - stored_time).days)
                doc_str = "\n".join(doc) if isinstance(doc, list) else str(doc)
                importance_score = 2 if meta.get("important", False) else 1
                combined_score = importance_score + decay_factor

                scored_results.append((doc_str, combined_score))
            except Exception as e:
                logger.exception("Error processing memory entry %s: %s", meta, e)

    # Return top 3 highest scoring entries
    scored_results.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored_results[:3]]


def fetch_all_memories() -> list:
    """
    Fetches all stored memory entries from the database.

    Returns:
        list: List of memory objects with user query, timestamp, and content.
    """
    try:
        results = memory_collection.get()
        memories = []

        for doc, meta in zip(
            results.get("documents", []), results.get("metadatas", [])
        ):
            meta = meta[0] if isinstance(meta, list) and meta else meta

            if isinstance(meta, dict):
                memories.append(
                    {
                        "user_query": meta.get("user_query", ""),
                        "timestamp": meta.get("timestamp", ""),
                        "important": meta.get("important", False),
                        "conversation": doc,
                    }
                )

        # Most recent first
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return memories
    except Exception as e:
        logger.exception("Error fetching all memories: %s", e)
        return []


def store_memory(user_query: str, response: str, is_important: bool) -> None:
    """
    Stores a chatbot query-response pair into memory.

    Avoids duplication by checking for existing matches. Updates importance if needed.

    Args:
        user_query (str): The user's input.
        response (str): The chatbot's reply.
        is_important (bool): Whether the memory is flagged as important.
    """
    memory_entry = f"User: {user_query}\nAI: {response}"

    try:
        existing_results = memory_collection.query(
            query_texts=[user_query], n_results=10
        )
    except Exception as e:
        logger.exception("Error checking for duplicates: %s", e)
        return

    for doc, meta, doc_id in zip(
        existing_results.get("documents", []),
        existing_results.get("metadatas", []),
        existing_results.get("ids", []),
    ):
        meta = meta[0] if isinstance(meta, list) and meta else meta

        if not isinstance(meta, dict) or "user_query" not in meta:
            continue

        if meta["user_query"] == user_query and doc == memory_entry:
            # If importance has changed, update metadata
            if not meta.get("important", False) and is_important:
                try:
                    memory_collection.update(
                        ids=[doc_id],
                        metadatas=[
                            {
                                "user_query": user_query,
                                "timestamp": meta["timestamp"],
                                "important": True,
                            }
                        ],
                    )
                    logger.info("Updated importance flag for memory ID: %s", doc_id)
                except Exception as e:
                    logger.exception("Failed to update memory ID '%s': %s", doc_id, e)
            else:
                logger.info("Duplicate memory found. No update needed.")
            return  # Avoid inserting duplicate

    # Create new memory entry
    timestamp = datetime.utcnow().isoformat()
    new_id = f"{hash(memory_entry)}-{timestamp}"

    try:
        memory_collection.add(
            documents=[memory_entry],
            metadatas=[
                {
                    "user_query": user_query,
                    "timestamp": timestamp,
                    "important": is_important,
                }
            ],
            ids=[new_id],
        )
        logger.info("Stored new memory with ID: %s", new_id)
    except Exception as e:
        logger.exception("Error storing new memory: %s", e)
