"""
Database Utilities for ChatRagi

This module provides functions for interacting with ChromaDB, including:
- Managing chat memory collections
- Deleting stale or unimportant data
- Listing and removing indexed documents
"""

from datetime import datetime, timedelta

import chromadb

from chatragi.config import DB_PATH, TIME_DECAY_DAYS
from chatragi.utils.logger_config import logger

# Initialize ChromaDB client and key collections
try:
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    memory_collection = chroma_client.get_or_create_collection("chat_memory")
    doc_collection = chroma_client.get_or_create_collection("doc_index")
    logger.info("Successfully connected to ChromaDB!")
except Exception as e:
    logger.exception("Error initializing ChromaDB: %s", e)


def delete_non_important_memories() -> None:
    """
    Deletes chatbot memory older than TIME_DECAY_DAYS unless marked as important.

    Helps maintain efficient memory usage by pruning outdated entries.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=TIME_DECAY_DAYS)

    try:
        results = memory_collection.get()
        ids_to_delete = []

        for doc, meta in zip(
            results.get("documents", []), results.get("metadatas", [])
        ):
            if not isinstance(meta, dict):
                continue  # Skip entries without valid metadata

            timestamp = meta.get("timestamp")
            if not timestamp:
                logger.warning("Skipping entry without timestamp: %s", meta)
                continue

            stored_time = datetime.fromisoformat(timestamp)

            # Mark for deletion if not important and older than cutoff
            if stored_time < cutoff_date and not meta.get("important", False):
                doc_id = meta.get("id")
                if doc_id:
                    ids_to_delete.append(doc_id)
                else:
                    logger.warning("Missing 'id' in metadata: %s", meta)

        if ids_to_delete:
            memory_collection.delete(ids=ids_to_delete)
            logger.info(
                "Deleted %d non-important memories older than %d days.",
                len(ids_to_delete),
                TIME_DECAY_DAYS,
            )
        else:
            logger.info("No old, non-important memories to delete.")
    except Exception as e:
        logger.exception("Error during memory cleanup: %s", e)


# Run cleanup during module load
delete_non_important_memories()


def log_indexed_documents() -> None:
    """
    Logs the total number of indexed documents in ChromaDB.
    """
    try:
        num_stored_docs = len(doc_collection.get().get("documents", []))
        logger.info("ChromaDB contains %d indexed documents.", num_stored_docs)
    except Exception as e:
        logger.exception("Unable to count stored documents: %s", e)


# Log document count during module load
log_indexed_documents()


def list_collections() -> None:
    """
    Lists all available collections in ChromaDB.
    """
    try:
        collections = chroma_client.list_collections()
        if not collections:
            logger.warning("No collections found in ChromaDB.")
        else:
            logger.info("Stored Collections:")
            for collection in collections:
                logger.info("- %s", collection.name)
    except Exception as e:
        logger.exception("Error listing collections: %s", e)


def list_documents() -> list[dict]:
    """
    Lists all indexed documents with metadata from the 'doc_index' collection.

    Returns:
        list[dict]: List of documents with file_name, source, and chunk count.
    """
    try:
        stored_docs = doc_collection.get()
        metadatas = stored_docs.get("metadatas", [])

        if not metadatas:
            logger.warning("No documents found in ChromaDB.")
            return []

        file_stats = {}

        for meta in metadatas:
            if not isinstance(meta, dict):
                continue

            file_name = meta.get("file_name")
            source = meta.get("source", "unknown")

            if file_name:
                if file_name not in file_stats:
                    file_stats[file_name] = {
                        "file_name": file_name,
                        "source": source,
                        "chunks": 1,
                    }
                else:
                    file_stats[file_name]["chunks"] += 1

        results = sorted(file_stats.values(), key=lambda x: x["file_name"].lower())

        logger.info("Stored Documents in ChromaDB:")
        for i, doc in enumerate(results, start=1):
            logger.info(
                "Source Document %d: %s (%s, %d chunks)",
                i,
                doc["file_name"],
                doc["source"],
                doc["chunks"],
            )

        return results

    except Exception as e:
        logger.exception("Error listing documents: %s", e)
        return []


def delete_document_by_filename(file_name: str) -> None:
    """
    Deletes a specific document from ChromaDB by filename.

    Args:
        file_name (str): The name of the file to remove from storage.
    """
    try:
        logger.info("Deleting document: %s from ChromaDB...", file_name)
        doc_collection.delete(where={"file_name": file_name})
        logger.info("Successfully removed '%s' from the index.", file_name)
    except Exception as e:
        logger.exception("Error deleting document '%s': %s", file_name, e)
