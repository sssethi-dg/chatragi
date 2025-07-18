"""
Document Loader for ChatRagi

Handles ingestion of PDF, CSV, JSON, TXT documents into ChromaDB.
Splits files into chunks, attaches metadata, and checks for duplication.
"""

import hashlib
import json
import os
import re
import shutil
from typing import List

import pandas as pd
import pdfplumber
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

from chatragi.config import (
    ARCHIVE_FOLDER,
    CONTEXT_WINDOW,
    DATA_FOLDER,
    EMBED_MODEL,
    PERSIST_DIR,
)
from chatragi.utils.db_utils import chroma_client
from chatragi.utils.logger_config import logger

# Optional tokenizer for token estimation
try:
    import tiktoken

    tokenizer = tiktoken.get_encoding("cl100k_base")
except ImportError:
    tokenizer = None


def move_to_archive(filename: str):
    """
    Moves a processed file to the archive folder to avoid reprocessing.

    Args:
        filename (str): Name of the file.
    """
    src_path = os.path.join(DATA_FOLDER, filename)
    dest_path = os.path.join(ARCHIVE_FOLDER, filename)

    if not os.path.exists(src_path):
        logger.warning(
            "File '%s' not found in '%s'. Skipping.", filename, DATA_FOLDER
        )
        return

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(
            os.path.join(ARCHIVE_FOLDER, f"{base}_{counter}{ext}")
        ):
            counter += 1
        dest_path = os.path.join(ARCHIVE_FOLDER, f"{base}_{counter}{ext}")

    shutil.move(src_path, dest_path)
    logger.info("Moved file '%s' to archive.", filename)


def compute_file_hash(file_path: str) -> str:
    """
    Computes a SHA-256 hash of file contents.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: File hash or empty string if error.
    """
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.exception("Error computing hash for '%s': %s", file_path, e)
        return ""


def estimate_tokens(text: str) -> int:
    """
    Estimates number of tokens in the given text.

    Args:
        text (str): Input text.

    Returns:
        int: Approximate token count.
    """
    return len(text.split())


def split_text_into_chunks(
    text: str, max_tokens: int = CONTEXT_WINDOW, overlap_ratio: float = 0.2
) -> List[str]:
    """
    Splits text into overlapping chunks based on sentences.

    Args:
        text (str): Full document text.
        max_tokens (int): Maximum tokens per chunk.
        overlap_ratio (float): Overlap fraction between chunks.

    Returns:
        List[str]: List of text chunks.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current_chunk: List[str] = []
    overlap = int(max_tokens * overlap_ratio)

    for sentence in sentences:
        tokens_in_sentence = estimate_tokens(sentence)
        tokens_in_chunk = sum(estimate_tokens(s) for s in current_chunk)

        if tokens_in_chunk + tokens_in_sentence <= max_tokens:
            current_chunk.append(sentence)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:] + [sentence]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def chunk_text(text: str, file_name: str, source: str) -> List[dict]:
    """
    Prepares structured chunks with metadata for a document.

    Args:
        text (str): Full document text.
        file_name (str): Source filename.
        source (str): File source type (e.g., 'pdf', 'csv').

    Returns:
        List[dict]: Chunk metadata.
    """
    chunks = split_text_into_chunks(text)
    return [
        {
            "text": chunk,
            "metadata": {
                "file_name": file_name,
                "source": source,
                "hash": hashlib.md5(chunk.encode()).hexdigest(),
            },
        }
        for chunk in chunks
        if chunk
    ]


def load_pdf(file_path: str) -> List[dict]:
    """
    Loads text from a PDF file.

    Args:
        file_path (str): Path to PDF file.

    Returns:
        List[dict]: Chunked document.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n\n".join(
                page.extract_text()
                for page in pdf.pages
                if page.extract_text()
            )

        if not text.strip():
            logger.warning(
                "Skipping empty or unreadable PDF: %s",
                os.path.basename(file_path),
            )
            return []

        return chunk_text(text, os.path.basename(file_path), "pdf")
    except Exception as e:
        logger.exception(
            "Error processing PDF '%s': %s", os.path.basename(file_path), e
        )
        return []


def load_csv(file_path: str) -> List[dict]:
    """
    Loads text from a CSV file.

    Args:
        file_path (str): Path to CSV file.

    Returns:
        List[dict]: Chunked document.
    """
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(
                "Skipping empty CSV: %s", os.path.basename(file_path)
            )
            return []

        text = df.to_string(index=False)
        return chunk_text(text, os.path.basename(file_path), "csv")
    except Exception as e:
        logger.exception(
            "Error processing CSV '%s': %s", os.path.basename(file_path), e
        )
        return []


def load_json(file_path: str) -> List[dict]:
    """
    Loads text from a JSON or JSONL file.

    Args:
        file_path (str): Path to JSON file.

    Returns:
        List[dict]: Chunked document.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]

        if not data:
            logger.warning(
                "Skipping empty JSON: %s", os.path.basename(file_path)
            )
            return []

        source = "jsonl" if isinstance(data, list) else "json"
        text = json.dumps(data, indent=2)
        return chunk_text(text, os.path.basename(file_path), source)
    except Exception as e:
        logger.exception(
            "Error processing JSON '%s': %s", os.path.basename(file_path), e
        )
        return []


def load_txt(file_path: str) -> List[dict]:
    """
    Loads text from a TXT or Markdown file.

    Args:
        file_path (str): Path to TXT/MD file.

    Returns:
        List[dict]: Chunked document.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        if not text:
            logger.warning(
                "Skipping empty TXT: %s", os.path.basename(file_path)
            )
            return []

        return chunk_text(text, os.path.basename(file_path), "text")
    except Exception as e:
        logger.exception(
            "Error processing TXT '%s': %s", os.path.basename(file_path), e
        )
        return []


def load_document(file_path: str) -> List[dict]:
    """
    Loads document based on its file extension.

    Args:
        file_path (str): File path.

    Returns:
        List[dict]: Chunked document.
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
        logger.warning("Unsupported file format: %s", file_path)
        return []

    return loaders[ext](file_path)


def process_new_documents(file_path: str):
    """
    Processes a new file: splits, checks for duplicates, and indexes
    into ChromaDB.

    Args:
        file_path (str): Full path to the new document.
    """
    logger.info("Processing file: %s", os.path.basename(file_path))

    file_hash = compute_file_hash(file_path)
    if not file_hash:
        logger.warning(
            "Hash computation failed for '%s'. Skipping.", file_path
        )
        return

    chunks = load_document(file_path)
    if not chunks:
        logger.warning("No valid content found in '%s'. Skipping.", file_path)
        return

    doc_collection = chroma_client.get_or_create_collection("doc_index")
    stored_docs = doc_collection.get()
    existing_hashes = {
        meta.get("hash", "") for meta in stored_docs.get("metadatas", [])
    }

    if any(chunk["metadata"]["hash"] in existing_hashes for chunk in chunks):
        logger.warning(
            "Duplicate document detected: %s. Skipping indexing.",
            os.path.basename(file_path),
        )
        move_to_archive(os.path.basename(file_path))
        return

    try:
        documents = [
            Document(text=chunk["text"], metadata=chunk["metadata"])
            for chunk in chunks
        ]

        storage_context = StorageContext.from_defaults(
            vector_store=ChromaVectorStore(chroma_collection=doc_collection)
        )
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, embed_model=EMBED_MODEL
        )
        index.storage_context.persist(persist_dir=PERSIST_DIR)

        logger.info(
            "Successfully indexed %d chunks from '%s'.",
            len(chunks),
            os.path.basename(file_path),
        )
        move_to_archive(os.path.basename(file_path))
    except Exception as e:
        logger.exception(
            "Error indexing document '%s': %s", os.path.basename(file_path), e
        )
