"""
ChatRagi Chatbot Application

This module initializes the vector index for document retrieval, processes user queries 
using the query engine, and stores conversation memory. It sets up the chatbot so that 
users can interact via a command-line interface.
"""

import os
import time
import warnings

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

from chatragi.config import (
    EMBED_MODEL,
    MAX_SOURCES,
    PERSIST_DIR,
    SIMILARITY_CUTOFF,
    SIMILARITY_TOP_K,
)
from chatragi.utils.chat_memory import store_memory
from chatragi.utils.db_utils import chroma_client
from chatragi.utils.logger_config import logger  # Centralized logger

# Suppress unnecessary warnings for cleaner logs
warnings.filterwarnings("ignore")

# Global variable to store the initialized query engine
query_engine = None


def refresh_index():
    """
    Refreshes or loads the document index for querying.

    This function retrieves the document collection from ChromaDB, builds a new vector
    index or loads an existing one from disk, and initializes the global query engine
    used to process user queries.

    Raises:
        Exception: If an error occurs during index creation or loading.
    """
    global query_engine

    try:
        logger.info("Refreshing index...")
        time.sleep(2)  # Allow any pending writes to complete

        # Retrieve or create the document collection in ChromaDB
        doc_collection = chroma_client.get_or_create_collection("doc_index")
        stored_docs = doc_collection.get()

        # Check if an index has already been persisted
        if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
            logger.info("Index already exists. Loading existing index.")

            # Create storage context based on the existing collection
            storage_context = StorageContext.from_defaults(
                vector_store=ChromaVectorStore(chroma_collection=doc_collection)
            )
            vector_store = ChromaVectorStore(chroma_collection=doc_collection)

            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context,
                embed_model=EMBED_MODEL,
            )
        else:
            logger.info("Building a new index...")

            # Prepare documents from stored data, filtering out any empty entries
            documents = [
                Document(text=doc_text, metadata=meta)
                for doc_text, meta in zip(
                    stored_docs.get("documents", []), stored_docs.get("metadatas", [])
                )
                if doc_text
            ]
            storage_context = StorageContext.from_defaults(
                vector_store=ChromaVectorStore(chroma_collection=doc_collection)
            )

            # Create a new index and persist it to disk
            index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context, embed_model=EMBED_MODEL
            )
            index.storage_context.persist(persist_dir=PERSIST_DIR)

        # Initialize the query engine with the defined similarity settings
        query_engine = index.as_query_engine(
            similarity_top_k=SIMILARITY_TOP_K, similarity_cutoff=SIMILARITY_CUTOFF
        )
        logger.info("Index is ready.")

    except Exception as e:
        logger.exception("Error refreshing index: %s", e)
        raise  # Propagate the exception after logging


def ask_chatbot(query: str) -> str:
    """
    Processes a user's query through the chatbot and stores the conversation memory.

    This function submits the query to the query engine and, upon receiving a response,
    stores the interaction in memory for future retrieval.

    Args:
        query (str): The user's input query.

    Returns:
        str: The chatbot's response.

    Raises:
        Exception: If the query engine is not initialized.
    """
    try:
        if not query_engine:
            logger.error("Query engine is not initialized.")
            return "Query engine is not initialized."

        # Process the query using the query engine
        response = query_engine.query(query)

        # Store the conversation memory (importance can be adjusted as needed)
        store_memory(query, str(response), is_important=False)

        return str(response)
    except Exception as e:
        logger.exception("Error processing query '%s': %s", query, e)
        return f"Error processing query: {e}"


# Initialize the index at startup
try:
    refresh_index()
except Exception as e:
    logger.error("Failed to initialize the index: %s", e)

# Main command-line interface loop for the chatbot
if __name__ == "__main__":
    logger.info("ChatRagi Chatbot is now running. Type 'exit' to quit.")

    while True:
        try:
            user_query = input("\nYour question (or !command): ")[:1500]
            if user_query.lower() in ["exit", "quit", "bye"]:
                logger.info("Chat session ended by user.")
                print("\nGoodbye! Chat history is saved.")
                break

            if not query_engine:
                print("Query engine is not initialized. Skipping query.")
                continue

            # Get response from the chatbot
            answer = ask_chatbot(user_query)
            print("\nChatRagi Response:", answer)
        except Exception as e:
            logger.exception("Unexpected error in main loop: %s", e)
