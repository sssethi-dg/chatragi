"""
Configuration settings for the ChatRagi chatbot application.

This module defines database storage paths, document processing settings, 
LLM model configuration, and performance optimizations. Logging and exception 
handling are incorporated to assist with troubleshooting and monitoring.
"""

import logging
import os
from pathlib import Path

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

# Set up logging using the project's logger configuration.
# It is assumed that logger_config.py has been added to the project.
logger = logging.getLogger(__name__)

# ------------------- General Configuration -------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = str(os.getenv("DB_PATH", PROJECT_ROOT / "chroma_db"))
DATA_FOLDER = str(os.getenv("DATA_FOLDER", PROJECT_ROOT / "data"))
ARCHIVE_FOLDER = str(os.getenv("ARCHIVE_FOLDER", PROJECT_ROOT / "archive"))
PERSIST_DIR = str(os.getenv("PERSIST_DIR", PROJECT_ROOT / "storage"))
LOG_FOLDER = str(os.getenv("LOG_FOLDER", PROJECT_ROOT / "logs"))

# Ensure required directories exist
for directory in [DATA_FOLDER, ARCHIVE_FOLDER, PERSIST_DIR, LOG_FOLDER]:
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logger.error("Failed to create directory %s: %s", directory, e)

# Define log file path
LOG_FILE_NAME = "chatragi.log"
LOG_FILE = os.path.join(LOG_FOLDER, LOG_FILE_NAME)

# ------------------- LLM Model Configuration -------------------
DEFAULT_MODEL = (
    "phi4:latest"  # Options: "phi4:latest", "gemma3:12b", "llama3.2-vision:latest"
)
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", DEFAULT_MODEL)

try:
    # Load LLM Model with 4-bit quantization (optimizes for better performance)
    LLM_MODEL = Ollama(
        model=LLM_MODEL_NAME,
        request_timeout=360.00,
        options={"num_gpu_layers": 20, "quantization": "4bit"},
    )
    logger.info("LLM model loaded: %s", LLM_MODEL_NAME)
except Exception as e:
    logger.error("Error loading LLM model %s: %s", LLM_MODEL_NAME, e)
    raise

# ------------------- Embedding Model Configuration -------------------
DEFAULT_EMBED_MODEL = "nomic-embed-text"  # Use a dedicated embedding model
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", DEFAULT_EMBED_MODEL)

try:
    # Attempt to use Ollama's embedding model
    EMBED_MODEL = OllamaEmbedding(model_name=EMBED_MODEL_NAME)
    logger.info("Using Ollama embedding model: %s", EMBED_MODEL_NAME)
except Exception as e:
    logger.warning(
        "Ollama embeddings not available; falling back to Hugging Face. Error: %s", e
    )
    EMBED_MODEL = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

# Apply settings globally
Settings.llm = LLM_MODEL
Settings.embed_model = EMBED_MODEL

# ------------------- LLM Query Optimization -------------------
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", 2048))  # Maximum token size for inputs
NUM_OUTPUT_TOKENS = int(
    os.getenv("NUM_OUTPUT_TOKENS", 2000)
)  # Maximum tokens in generated responses

# Fine-tune retrieval parameters
SIMILARITY_TOP_K = int(
    os.getenv("SIMILARITY_TOP_K", 5)
)  # Number of document chunks to retrieve
SIMILARITY_CUTOFF = float(
    os.getenv("SIMILARITY_CUTOFF", 0.8)
)  # Minimum similarity threshold

# ------------------- Memory Management -------------------
TIME_DECAY_DAYS = int(os.getenv("TIME_DECAY_DAYS", 3))
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", 1500))

# ------------------- Adaptive Chunking (Dynamic Splitting) -------------------
DYNAMIC_CHUNKING = {
    "thresholds": [500, 2000, 5000],  # Word count thresholds for different strategies
    "sizes": [
        256,
        512,
        1024,
        1536,
    ],  # Optimized chunk sizes corresponding to thresholds
    "overlap": [0.5, 0.3, 0.2, 0.1],  # Overlap ratios to maintain context
}

# ------------------- Debugging & Performance Logging -------------------
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

if DEBUG_MODE:
    logger.info("Debug Mode: ON")
    logger.info("Using LLM Model: %s", LLM_MODEL_NAME)
    logger.info("Using Embedding Model: %s", EMBED_MODEL_NAME)
    logger.info("Context Window: %d tokens", CONTEXT_WINDOW)
    logger.info("Output Tokens: %d tokens", NUM_OUTPUT_TOKENS)
    logger.info("Similarity Top-K: %d", SIMILARITY_TOP_K)
    logger.info("Similarity Cutoff: %f", SIMILARITY_CUTOFF)

# Disable Tokenizer Parallelism to avoid deadlocks in multi-threaded environments
os.environ["TOKENIZERS_PARALLELISM"] = "false"
