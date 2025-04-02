"""
Document Loader for ChatRagi

This module handles the ingestion of various document types (PDF, CSV, JSON, TXT),
splits their text into manageable chunks with metadata, and checks for duplicates 
before adding the processed chunks into the vector store (ChromaDB) for later retrieval.
"""

import os
import shutil
import json
import re
import pandas as pd
import pdfplumber
import hashlib
from chatragi.config import DATA_FOLDER, ARCHIVE_FOLDER, PERSIST_DIR, EMBED_MODEL, CONTEXT_WINDOW
from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.vector_stores.chroma import ChromaVectorStore
from chatragi.utils.db_utils import chroma_client
from chatragi.utils.logger_config import logger  # Centralized logging configuration


# Optional dependency for advanced token counting; falls back to word count if unavailable.
try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
except ImportError:
    tokenizer = None

def move_to_archive(filename: str):
    """
    Moves a processed file to the archive folder to prevent reprocessing.

    Args:
        filename (str): Name of the file to be archived.
    """
    src_path = os.path.join(DATA_FOLDER, filename)
    dest_path = os.path.join(ARCHIVE_FOLDER, filename)

    if not os.path.exists(src_path):
        logger.warning("File '%s' not found in '%s'. Skipping.", filename, DATA_FOLDER)
        return

    # Prevent overwriting by appending a counter if the file already exists in the archive.
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(ARCHIVE_FOLDER, f"{base}_{counter}{ext}")):
            counter += 1
        dest_path = os.path.join(ARCHIVE_FOLDER, f"{base}_{counter}{ext}")

    shutil.move(src_path, dest_path)
    logger.info("Moved file '%s' to archive successfully.", filename)

def compute_file_hash(file_path: str) -> str:
    """
    Computes a SHA-256 hash for a file's contents for duplicate detection.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: SHA-256 hash of the file content, or None if an error occurs.
    """
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read file in small chunks to conserve memory.
            while chunk := f.read(8192):
                hasher.update(chunk)
    except Exception as e:
        logger.exception("Error computing hash for '%s': %s", file_path, e)
        return None
    return hasher.hexdigest()

def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a text string based on word count.

    Args:
        text (str): Input text.

    Returns:
        int: Estimated token count.
    """
    return len(text.split())

def split_text_into_chunks(text: str, max_tokens: int = CONTEXT_WINDOW, overlap_ratio: float = 0.2) -> list:
    """
    Splits text into overlapping chunks based on estimated token count and sentence boundaries.

    Args:
        text (str): The full text to be chunked.
        max_tokens (int): Maximum tokens allowed per chunk.
        overlap_ratio (float): Fraction of tokens to overlap between consecutive chunks.

    Returns:
        list: List of text chunks.
    """
    # Split text at sentence-ending punctuation followed by whitespace.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    # Determine the number of words to retain from the previous chunk as overlap.
    overlap = int(max_tokens * overlap_ratio)

    for sentence in sentences:
        tokens_in_sentence = estimate_tokens(sentence)
        tokens_in_chunk = sum(estimate_tokens(s) for s in current_chunk)

        # If adding the sentence does not exceed max_tokens, add it to the current chunk.
        if tokens_in_chunk + tokens_in_sentence <= max_tokens:
            current_chunk.append(sentence)
        else:
            # Append the current chunk and start a new chunk with overlapping words.
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:] + [sentence]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def chunk_text(text: str, file_name: str, source: str) -> list:
    """
    Splits document text into structured chunks and enriches each with metadata.

    Args:
        text (str): Full text extracted from the document.
        file_name (str): Name of the source file.
        source (str): Identifier for the type of file (e.g., 'pdf', 'csv').

    Returns:
        list: List of dictionaries, each containing a text chunk and its metadata.
    """
    chunks = split_text_into_chunks(text)
    # Add an MD5 hash for each chunk to help detect duplicates at the chunk level.
    return [
        {
            "text": chunk,
            "metadata": {
                "file_name": file_name,
                "source": source,
                "hash": hashlib.md5(chunk.encode()).hexdigest()
            }
        }
        for chunk in chunks if chunk
    ]

def load_pdf(file_path: str) -> list:
    """
    Loads text from a PDF file, splits it into chunks, and attaches metadata.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: List of text chunks with metadata.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        
        if not text.strip():
            logger.warning("Skipping empty or unreadable PDF: %s", os.path.basename(file_path))
            return []
        
        return chunk_text(text, os.path.basename(file_path), "pdf")
    except Exception as e:
        logger.exception("Error processing PDF '%s': %s", os.path.basename(file_path), e)
        return []

def load_csv(file_path: str) -> list:
    """
    Loads text from a CSV file, converts it to a string, and splits it into chunks.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        list: List of text chunks with metadata.
    """
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning("Skipping empty CSV: %s", os.path.basename(file_path))
            return []
        
        text = df.to_string(index=False)
        return chunk_text(text, os.path.basename(file_path), "csv")
    except Exception as e:
        logger.exception("Error processing CSV '%s': %s", os.path.basename(file_path), e)
        return []

def load_json(file_path: str) -> list:
    """
    Loads text from a JSON file, converts it to a formatted string, and splits it into chunks.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        list: List of text chunks with metadata.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data:
            logger.warning("Skipping empty JSON: %s", os.path.basename(file_path))
            return []
        
        text = json.dumps(data, indent=2)
        return chunk_text(text, os.path.basename(file_path), "json")
    except Exception as e:
        logger.exception("Error processing JSON '%s': %s", os.path.basename(file_path), e)
        return []

def load_txt(file_path: str) -> list:
    """
    Loads text from a TXT or Markdown file and splits it into chunks.

    Args:
        file_path (str): Path to the TXT or Markdown file.

    Returns:
        list: List of text chunks with metadata.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        
        if not text:
            logger.warning("Skipping empty TXT file: %s", os.path.basename(file_path))
            return []
        
        return chunk_text(text, os.path.basename(file_path), "text")
    except Exception as e:
        logger.exception("Error processing TXT '%s': %s", os.path.basename(file_path), e)
        return []

def load_document(file_path: str) -> list:
    """
    Dispatches the loading process to the appropriate loader function based on file extension.

    Args:
        file_path (str): Path to the document file.

    Returns:
        list: List of text chunks with metadata.
    """
    loaders = {
        ".pdf": load_pdf,
        ".csv": load_csv,
        ".json": load_json,
        ".txt": load_txt,
        ".md": load_txt,
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in loaders:
        logger.warning("Unsupported file format: %s. Skipping.", file_path)
        return []
    
    return loaders[ext](file_path)

def process_new_documents(file_path: str):
    """
    Processes a new document by loading its content, splitting it into chunks,
    checking for duplicates, and updating the ChromaDB index.

    Args:
        file_path (str): Path to the document being processed.
    """
    logger.info("Processing file: %s", os.path.basename(file_path))
    
    # Compute a hash of the entire file for duplicate detection.
    file_hash = compute_file_hash(file_path)
    if not file_hash:
        logger.warning("Hash computation failed for %s. Skipping.", file_path)
        return
    
    # Load document and split into text chunks.
    chunks = load_document(file_path)
    if not chunks:
        logger.warning("No valid content found in %s. Skipping.", file_path)
        return
    
    # Retrieve the existing documents from ChromaDB.
    doc_collection = chroma_client.get_or_create_collection("doc_index")
    stored_docs = doc_collection.get()
    
    # Build a set of existing chunk hashes for duplicate detection.
    existing_hashes = {meta.get("hash", "") for meta in stored_docs.get("metadatas", [])}
    
    # If any chunk's hash is already present, treat the file as duplicate.
    if any(chunk["metadata"]["hash"] in existing_hashes for chunk in chunks):
        logger.warning("Duplicate document detected: %s. Skipping indexing.", os.path.basename(file_path))
        move_to_archive(os.path.basename(file_path))
        return

    try:
        # Convert each chunk into a Document object for indexing.
        document_objects = [Document(text=chunk["text"], metadata=chunk["metadata"]) for chunk in chunks]
        
        # Build the vector store index and persist it.
        storage_context = StorageContext.from_defaults(vector_store=ChromaVectorStore(chroma_collection=doc_collection))
        index = VectorStoreIndex.from_documents(document_objects, storage_context=storage_context, embed_model=EMBED_MODEL)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        
        logger.info("Successfully indexed %d chunks from '%s'", len(chunks), os.path.basename(file_path))
        move_to_archive(os.path.basename(file_path))
    except Exception as e:
        logger.exception("Error indexing document '%s': %s", os.path.basename(file_path), e)