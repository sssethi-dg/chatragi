"""
ChatRagi Chatbot Application

This module initializes the vector index for document retrieval, processes user queries 
using a retriever-based query engine, and stores conversation memory. Designed to support
source citations via metadata.
"""

import os
import time
import warnings

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.vector_stores.chroma import ChromaVectorStore

from chatragi.config import (
    EMBED_MODEL,
    PERSIST_DIR,
    SIMILARITY_CUTOFF,
    SIMILARITY_TOP_K,
)
from chatragi.utils.chat_memory import store_memory
from chatragi.utils.db_utils import chroma_client
from chatragi.utils.logger_config import logger

warnings.filterwarnings("ignore")  # Suppress noisy logs

# Global query engine object
query_engine = None


def refresh_index():
    """
    Initializes or refreshes the vector index and sets up the query engine.

    - If an index exists in PERSIST_DIR, it will be loaded.
    - Otherwise, a new index is built from stored ChromaDB documents.

    Raises:
        Exception: If index creation or loading fails.
    """
    global query_engine

    try:
        logger.info("Refreshing index...")
        time.sleep(2)  # Let any pending file writes settle

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

        # Create query engine with retriever
        query_engine = RetrieverQueryEngine.from_args(
            retriever=index.as_retriever(
                similarity_top_k=SIMILARITY_TOP_K, similarity_cutoff=SIMILARITY_CUTOFF
            ),
            include_source=True,  # Required for citation metadata
        )

        logger.info("Query engine is ready.")

    except Exception as e:
        logger.exception("Failed to refresh or initialize index: %s", e)
        raise


def ask_chatbot(query: str) -> dict:
    """
    Sends a query to the chatbot and returns both the answer and source citations.

    Args:
        query (str): The user's question.

    Returns:
        dict: Contains the answer (str) and a list of citations (List[str]).
    """
    try:
        if not query_engine:
            logger.error("Query engine not initialized.")
            return {"answer": "Query engine is not initialized.", "citations": []}

        # Process the user query
        response = query_engine.query(query)

        # Store the interaction for future memory
        store_memory(query, str(response), is_important=False)

        # Extract citations from source metadata
        citations = []
        for node in response.source_nodes:
            source = node.node.metadata.get("file_name") or node.node.metadata.get(
                "source"
            )
            if source and source not in citations:
                citations.append(source)

        return {"answer": str(response), "citations": citations}

    except Exception as e:
        logger.exception("Failed to handle query '%s': %s", query, e)
        return {"answer": f"Error: {e}", "citations": []}


# Initialize vector index when chatbot loads
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
