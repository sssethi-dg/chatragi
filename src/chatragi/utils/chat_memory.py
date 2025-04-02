"""
Chat Memory Module for ChatRagi

This module handles storing, retrieving, and fetching previous chatbot interactions
(memory). It is used to provide context to the chatbot by recalling relevant past
conversations based on the user's current query.
"""

from datetime import datetime

from chatragi.utils.db_utils import memory_collection
from chatragi.utils.logger_config import logger  # Centralized logger for the project


def retrieve_memory(user_query: str) -> list:
    """
    Retrieves past relevant chatbot interactions from memory.

    This function queries stored chatbot conversations related to the user's query.
    It scores retrieved memories based on their importance and recency, ensuring that
    the most relevant responses are returned.

    Args:
        user_query (str): The input query for which relevant past responses are retrieved.

    Returns:
        list: A list of up to three relevant chatbot responses.
    """
    try:
        results = memory_collection.query(query_texts=[user_query], n_results=5)
    except Exception as e:
        logger.exception("Error querying memory_collection: %s", e)
        return []

    scored_results = []
    if results and results.get("documents"):
        for doc, meta in zip(results["documents"], results["metadatas"]):
            # Normalize metadata if wrapped in a list
            if isinstance(meta, list) and meta:
                meta = meta[0]

            if not isinstance(meta, dict):
                logger.warning("Unexpected metadata format, skipping entry: %s", meta)
                continue

            timestamp = meta.get("timestamp")
            if not timestamp:
                logger.warning(
                    "Missing timestamp in metadata, skipping entry: %s", meta
                )
                continue

            try:
                stored_time = datetime.fromisoformat(timestamp)
                # Compute decay factor: more recent memories get higher score
                decay_factor = 1 / (1 + (datetime.utcnow() - stored_time).days)
                # Ensure document is represented as a string
                doc_str = "\n".join(doc) if isinstance(doc, list) else str(doc)
                # Assign higher weight if memory is marked as important
                importance_score = 2 if meta.get("important", False) else 1
                combined_score = importance_score + decay_factor
                scored_results.append((doc_str, combined_score))
            except Exception as e:
                logger.exception("Error processing memory entry %s: %s", meta, e)

    # Sort memories by combined score in descending order
    scored_results.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored_results[:3]]


def fetch_all_memories() -> list:
    """
    Fetches all stored chatbot memories from the database.

    Returns:
        list: A list of dictionaries representing all memory entries along with metadata.
    """
    try:
        results = memory_collection.get()
        memories = []
        for doc, meta in zip(
            results.get("documents", []), results.get("metadatas", [])
        ):
            # Normalize metadata if it is wrapped in a list
            if isinstance(meta, list) and meta:
                meta = meta[0]
            if not isinstance(meta, dict):
                continue
            memories.append(
                {
                    "user_query": meta.get("user_query", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "important": meta.get("important", False),
                    "conversation": doc,
                }
            )
        # Sort memories by timestamp in descending order
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return memories
    except Exception as e:
        logger.exception("Error fetching all memories: %s", e)
        return []


def store_memory(user_query: str, response: str, is_important: bool) -> None:
    """
    Stores chatbot interactions in memory, avoiding duplicate entries.

    If an identical interaction exists, the function updates its importance flag.
    Otherwise, it adds a new memory entry to the database.

    Args:
        user_query (str): The user's query.
        response (str): The chatbot's response.
        is_important (bool): Flag indicating whether the memory should be marked as important.

    Returns:
        None
    """
    memory_entry = f"User: {user_query}\nAI: {response}"

    try:
        existing_results = memory_collection.query(
            query_texts=[user_query], n_results=10
        )
    except Exception as e:
        logger.exception(
            "Error querying existing memory for user_query '%s': %s", user_query, e
        )
        return

    for doc, meta, doc_id in zip(
        existing_results.get("documents", []),
        existing_results.get("metadatas", []),
        existing_results.get("ids", []),
    ):
        if isinstance(meta, list) and meta:
            meta = meta[0]
        if not isinstance(meta, dict) or "user_query" not in meta:
            continue

        # If an identical query-response pair exists, update its importance if needed
        if meta["user_query"] == user_query and doc == memory_entry:
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
                    logger.info("Memory exists. Updated importance for ID: %s", doc_id)
                except Exception as e:
                    logger.exception("Error updating memory for ID '%s': %s", doc_id, e)
            else:
                logger.info(
                    "Memory already exists for user_query '%s'. No update needed.",
                    user_query,
                )
            return  # Prevent duplicate storage

    # If no duplicate was found, store the new memory entry
    timestamp = datetime.utcnow().isoformat()
    new_id = f"{hash(memory_entry)}-{timestamp}"  # Create a unique identifier
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
        logger.info("Memory stored successfully with ID: %s", new_id)
    except Exception as e:
        logger.exception("Error storing new memory: %s", e)
