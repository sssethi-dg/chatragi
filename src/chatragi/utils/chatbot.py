"""
ChatRagi Chatbot Application

This module manages vector-based document retrieval and response generation using
RetrieverQueryEngine and ChromaDB. It supports contextual memory, structured responses,
and metadata-based citation extraction.

Main Features:
- Vector index refresh/load logic
- Memory-aware response via `store_memory()`
- Source citations for each answer
- Optional CLI interface
"""

import os
import time
import warnings

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
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
from chatragi.utils.logger_config import logger

warnings.filterwarnings("ignore")

# Global query engine object
query_engine = None


def refresh_index():
    """
    Initializes or refreshes the vector index and sets up the query engine.

    Loads an existing index from disk if available; otherwise builds a new one from ChromaDB.
    """
    global query_engine

    try:
        logger.info("Refreshing index...")
        time.sleep(2)

        doc_collection = chroma_client.get_or_create_collection("doc_index")
        stored_docs = doc_collection.get()

        if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
            logger.info("Loading existing index from disk.")
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
            logger.info("Building new vector index from ChromaDB documents.")
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
            index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context, embed_model=EMBED_MODEL
            )
            index.storage_context.persist(persist_dir=PERSIST_DIR)

        # Configure the retriever-based query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=index.as_retriever(
                similarity_top_k=SIMILARITY_TOP_K,
                similarity_cutoff=SIMILARITY_CUTOFF,
            ),
            include_source=True,
        )

    except Exception as e:
        logger.exception("Failed to refresh index: %s", e)
        raise


def ask_bot(user_input: str) -> str:
    """
    Sends a query to the chatbot and stores the memory entry.

    Args:
        user_input (str): User's question or statement.
        chat_id (str): Unique identifier for the session.

    Returns:
        str: Response from the chatbot.
    """
    if not query_engine:
        raise RuntimeError("Query engine not initialized. Call refresh_index() first.")

    response = query_engine.query(user_input)
    store_memory(user_query=user_input, response=str(response), is_important=False)
    return str(response)


def ask_chatbot(query: str) -> dict:
    """
    Sends a query to the chatbot and returns both the generated answer and source citations.

    Filters duplicate sources but ignores similarity score due to unreliability in current setup.

    Args:
        query (str): The user's question.

    Returns:
        dict: Dictionary with:
            - 'answer' (str): The chatbot's response.
            - 'citations' (List[str]): List of unique source file names.
    """
    try:
        if not query_engine:
            logger.error("Query engine not initialized.")
            return {"answer": "Query engine is not initialized.", "citations": []}

        response = query_engine.query(query)
        store_memory(query, str(response), is_important=False)

        citations = []
        seen = set()

        for node in response.source_nodes:
            source = node.node.metadata.get("file_name") or node.node.metadata.get(
                "source"
            )
            if source and source not in seen:
                citations.append(source)
                seen.add(source)
            if len(citations) >= MAX_SOURCES:
                break

        return {"answer": str(response), "citations": citations}

    except Exception as e:
        logger.exception("Failed to handle query '%s': %s", query, e)
        return {"answer": f"Error: {e}", "citations": []}


# Auto-refresh the index when module is loaded
try:
    refresh_index()
except Exception as e:
    logger.error("Initialization failed: %s", e)


if __name__ == "__main__":
    logger.info("ChatRagi CLI is active. Type 'exit' to quit.")

    while True:
        try:
            user_query = input("\nYour question: ")[:1500]
            if user_query.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            result = ask_chatbot(user_query)
            print("\nChatRagi:\n", result["answer"])
            if result["citations"]:
                print("\nSources:")
                for i, src in enumerate(result["citations"], 1):
                    print(f"{i}. {src}")

        except Exception as e:
            logger.exception("Unexpected CLI error: %s", e)
