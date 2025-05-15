import csv
import textwrap

import chromadb

from chatragi.config import DB_PATH

WRAP_WIDTH = 100  # Character width for visual chunking


def write_to_csv(filename, rows, headers):
    """
    Writes a list of rows to a CSV file with specified headers.

    Args:
        filename (str): Name of the output CSV file.
        rows (List[List[str]]): List of rows, each row is a list of string values.
        headers (List[str]): List of column headers.
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def format_text(text, width=WRAP_WIDTH):
    """
    Wraps long text into chunks with soft separators for better readability.

    Args:
        text (str): The input text.
        width (int): Maximum number of characters per chunk.

    Returns:
        str: Formatted string with soft separators.
    """
    text = text.strip().replace("\n", " ").replace("\r", "")
    chunks = textwrap.wrap(text, width=width)
    return " | ".join(chunks)


def export_chromadb_contents():
    """
    Connects to ChromaDB, retrieves documents and chatbot memory,
    and exports them to CSV files.
    """
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    collection_names = chroma_client.list_collections()

    # Export documents
    if "doc_index" in collection_names:
        doc_collection = chroma_client.get_collection("doc_index")
        stored_docs = doc_collection.get()

        if stored_docs.get("documents"):
            document_rows = [
                [format_text(doc), meta.get("file_name", "Unknown File")]
                for doc, meta in zip(stored_docs["documents"], stored_docs["metadatas"])
            ]
            write_to_csv(
                "documents.csv",
                document_rows,
                headers=["Document Chunk", "File Name"],
            )

    # Export chat memory
    if "chat_memory" in collection_names:
        memory_collection = chroma_client.get_collection("chat_memory")
        all_memories = memory_collection.get()

        if all_memories.get("documents"):
            memory_rows = [
                [format_text(doc), meta.get("session_id", "N/A")]
                for doc, meta in zip(
                    all_memories["documents"], all_memories["metadatas"]
                )
            ]
            write_to_csv(
                "chat_memory.csv",
                memory_rows,
                headers=["Chat Message", "Session ID"],
            )


if __name__ == "__main__":
    """
    Main function to export ChromaDB contents to CSV files.
    """
    export_chromadb_contents()
