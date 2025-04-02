"""
Database Utilities for ChatRagi

This module provides functions for interacting with ChromaDB, including managing
chatbot memory and document indexing. It supports operations such as deleting outdated
memories, logging the number of indexed documents, listing available collections, and
removing specific documents by filename.
"""

import chromadb
from datetime import datetime, timedelta
from chatragi.config import DB_PATH, TIME_DECAY_DAYS
from chatragi.utils.logger_config import logger  # Import the centralized logger

# Initialize ChromaDB with persistent storage
try:
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    memory_collection = chroma_client.get_or_create_collection("chat_memory")
    doc_collection = chroma_client.get_or_create_collection("doc_index")
    logger.info("Successfully connected to ChromaDB!")
except Exception as e:
    logger.exception("Error initializing ChromaDB: %s", e)


def delete_non_important_memories() -> None:
    """
    Deletes chatbot memory that is older than TIME_DECAY_DAYS unless marked as important.

    This function helps maintain efficient memory storage by removing outdated,
    non-essential records.

    Returns:
        None
    """
    cutoff_date = datetime.utcnow() - timedelta(days=TIME_DECAY_DAYS)
    try:
        results = memory_collection.get()  # Retrieve all stored memories
        ids_to_delete = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            if not isinstance(meta, dict):
                continue  # Skip invalid metadata entries
            timestamp = meta.get("timestamp")
            if not timestamp:
                logger.warning("Skipping entry without timestamp: %s", meta)
                continue
            stored_time = datetime.fromisoformat(timestamp)
            # If the record is older than the cutoff and not marked as important, mark it for deletion
            if stored_time < cutoff_date and not meta.get("important", False):
                if "id" in meta:
                    ids_to_delete.append(meta["id"])
                else:
                    logger.warning("Missing 'id' in metadata: %s", meta)
        if ids_to_delete:
            memory_collection.delete(ids=ids_to_delete)
            logger.info("Deleted %d non-important memories older than %d days.", len(ids_to_delete), TIME_DECAY_DAYS)
        else:
            logger.info("No old, non-important memories to delete.")
    except Exception as e:
        logger.exception("Error during memory cleanup: %s", e)


# Run memory cleanup at startup
delete_non_important_memories()


def log_indexed_documents() -> None:
    """
    Logs the total number of indexed documents in ChromaDB.

    This function tracks the growth of stored documents over time.

    Returns:
        None
    """
    try:
        num_stored_docs = len(doc_collection.get().get("documents", []))
        logger.info("ChromaDB contains %d indexed documents.", num_stored_docs)
    except Exception as e:
        logger.exception("Unable to count stored documents: %s", e)


# Log document count at startup
log_indexed_documents()


def list_collections() -> None:
    """
    Lists all available collections in ChromaDB.

    This function prints the names of all collections currently stored in ChromaDB.

    Returns:
        None
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


def list_documents() -> list:
    """
    Lists all indexed documents in the 'doc_index' collection.

    This function queries the stored documents and their metadata, displaying filenames
    for easy reference.

    Returns:
        list: A sorted list of unique filenames of the indexed documents.
    """
    try:
        stored_docs = doc_collection.get()
        documents = stored_docs.get("documents", [])
        metadatas = stored_docs.get("metadatas", [])
        if not documents:
            logger.warning("No documents found in ChromaDB.")
            return []
        unique_file_names = set()
        for meta_info in metadatas:
            if isinstance(meta_info, dict):
                file_name = meta_info.get("file_name")
                if file_name:
                    unique_file_names.add(file_name)
        logger.info("Stored Documents in ChromaDB:")
        for i, file_name in enumerate(sorted(unique_file_names), start=1):
            logger.info("Source Document %d: %s", i, file_name)
        return sorted(unique_file_names)
    except Exception as e:
        logger.exception("Error listing documents: %s", e)
        return []


def delete_document_by_filename(file_name: str) -> None:
    """
    Deletes a specific document from ChromaDB based on its filename.

    Args:
        file_name (str): The name of the file to delete from the database.

    Returns:
        None
    """
    try:
        logger.info("Deleting document: %s from ChromaDB...", file_name)
        doc_collection.delete(where={"file_name": file_name})
        logger.info("Successfully removed '%s' from the index.", file_name)
    except Exception as e:
        logger.exception("Error deleting document '%s': %s", file_name, e)