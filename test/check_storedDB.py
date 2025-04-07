import csv

import chromadb

from chatragi.config import DB_PATH


def write_to_csv(filename, rows, headers):
    """
    Writes a list of rows to a CSV file with specified headers.

    Args:
        filename (str): Name of the output CSV file.
        rows (List[List[str]]): List of rows, each row is a list of string values.
        headers (List[str]): List of column headers.

    Returns:
        None
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def export_chromadb_contents():
    """
    Connects to ChromaDB, retrieves documents and chatbot memory, and exports them to CSV files.

    This function performs the following:
    - Lists available collections in ChromaDB
    - Retrieves all documents from 'doc_index' collection (if available)
    - Retrieves all chat memories from 'chat_memory' collection (if available)
    - Saves both outputs to CSV files
    """
    # ✅ Connect to ChromaDB persistent client
    chroma_client = chromadb.PersistentClient(path=DB_PATH)

    # ✅ Retrieve all collection names
    collection_names = chroma_client.list_collections()
    print("\n📌 Stored Collections:")
    for name in collection_names:
        print(f"- {name}")

    # ✅ Handle 'doc_index' collection
    if "doc_index" in collection_names:
        doc_collection = chroma_client.get_collection("doc_index")
        stored_docs = doc_collection.get()

        print("\n📂 Stored Documents in ChromaDB:")
        if stored_docs.get("documents"):
            # Create a list of rows for CSV
            document_rows = []
            for doc, meta in zip(stored_docs["documents"], stored_docs["metadatas"]):
                document_rows.append([doc, meta.get("file_name", "Unknown File")])
                print(f"📌 Document: {doc} → {meta}\n\n---")

            # Write documents to CSV
            write_to_csv(
                "./results/documents.csv",
                document_rows,
                headers=["Document Chunk", "File Name"],
            )
            print("✅ Document data written to documents.csv")
        else:
            print("⚠️ No documents found in ChromaDB.")
    else:
        print("⚠️ 'doc_index' collection not found in ChromaDB.")

    # ✅ Handle 'chat_memory' collection
    if "chat_memory" in collection_names:
        memory_collection = chroma_client.get_collection("chat_memory")
        all_memories = memory_collection.get()

        print("\n📝 Stored Chatbot Conversations:")
        if all_memories.get("documents"):
            # Create a list of rows for CSV
            memory_rows = []
            for doc, meta in zip(all_memories["documents"], all_memories["metadatas"]):
                memory_rows.append([doc, meta.get("session_id", "N/A")])
                print(f"📌 {doc} → {meta}")

            # Write chat memory to CSV
            write_to_csv(
                "./results/chat_memory.csv",
                memory_rows,
                headers=["Chat Message", "Session ID"],
            )
            print("✅ Chat memory data written to chat_memory.csv")
        else:
            print("⚠️ No chatbot memory found.")
    else:
        print("⚠️ 'chat_memory' collection not found in ChromaDB.")


if __name__ == "__main__":
    export_chromadb_contents()
