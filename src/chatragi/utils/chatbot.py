"""
ChatRagi Chatbot Application

This module manages vector-based document retrieval and response generation
using RetrieverQueryEngine and ChromaDB. It supports contextual memory,
structured responses, and metadata-based citation extraction.

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
from chatragi.utils.persona import PersonaTone, apply_persona_tone

# Suppress noisy library warnings
warnings.filterwarnings("ignore")

# Global query engine object
query_engine = None


def refresh_index():
    """
    Initializes or refreshes the vector index and sets up the query engine.

    Loads an existing index from disk if available; otherwise builds a new one
    from ChromaDB.
    """
    global query_engine

    try:
        logger.info("Refreshing index...")
        time.sleep(2)

        doc_collection = chroma_client.get_or_create_collection("doc_index")
        stored_docs = doc_collection.get()

        storage_context = StorageContext.from_defaults(
            vector_store=ChromaVectorStore(chroma_collection=doc_collection)
        )

        if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
            logger.info("Loading existing index from disk.")
            index = VectorStoreIndex.from_vector_store(
                vector_store=ChromaVectorStore(
                    chroma_collection=doc_collection
                ),
                storage_context=storage_context,
                embed_model=EMBED_MODEL,
            )
        else:
            logger.info("Building new vector index from ChromaDB documents.")
            documents = [
                Document(text=doc_text, metadata=meta)
                for doc_text, meta in zip(
                    stored_docs.get("documents", []),
                    stored_docs.get("metadatas", []),
                )
                if doc_text
            ]
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                embed_model=EMBED_MODEL,
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


def ask_bot(user_input: str, persona: str = "default") -> str:
    """
    Sends a query to the chatbot after applying persona-based tone adjustment.

    Args:
        user_input (str): User's question or statement.
        persona (str): Selected response tone:
            - "default"
            - "professional"
            - "witty"

    Returns:
        str: Response from the chatbot.
    """
    if not query_engine:
        raise RuntimeError(
            "Query engine not initialized. Call refresh_index() first."
        )

    # Parse the persona tone safely
    try:
        tone = PersonaTone(persona.lower())
    except ValueError:
        tone = PersonaTone.DEFAULT

    # Apply persona-specific transformation to the input
    mod_prompt = apply_persona_tone(user_input, tone)

    # Query the LLM engine
    response = query_engine.query(mod_prompt)
    raw_response = getattr(response, "response", str(response)).strip()

    # Store conversation memory (save original user input and raw response)
    store_memory(
        user_query=user_input, response=raw_response, is_important=False
    )

    return raw_response


def ask_chatbot(query: str) -> dict:
    """
    Sends a query to the chatbot and returns both the generated answer and
    source citations.

    Args:
        query (str): The user's question.

    Returns:
        dict: Dictionary containing:
            - 'answer' (str): The chatbot's final answer.
            - 'citations' (List[str]): List of unique source file names used
            in the answer.
    """
    try:
        if not query_engine:
            logger.error("Query engine not initialized.")
            return {
                "answer": "Query engine is not initialized.",
                "citations": [],
            }

        # Directly query the engine
        response = query_engine.query(query)

        # Safely extract the answer
        ai_answer = getattr(response, "response", str(response)).strip()

        # Extract citations (up to MAX_SOURCES unique ones)
        citations = []
        seen = set()
        source_nodes = getattr(response, "source_nodes", [])

        for node in source_nodes:
            metadata = getattr(node.node, "metadata", {})
            source = metadata.get("file_name") or metadata.get("source")
            if source and source not in seen:
                citations.append(source)
                seen.add(source)
            if len(citations) >= MAX_SOURCES:
                break

        # Save memory
        store_memory(query, ai_answer, is_important=False)

        return {
            "answer": ai_answer,
            "citations": citations,
        }

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
