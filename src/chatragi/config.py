"""
Configuration settings for the ChatRagi chatbot application.

This module centralizes all configuration parameters used across the system.
It includes file paths, model selections, query settings, embedding choices, 
and performance optimizations. All values can be overridden using environment variables.
"""

import logging
import os
from pathlib import Path

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

# Set up logging (assumes logger_config.py is used across the project)
logger = logging.getLogger(__name__)

# ------------------- General Configuration -------------------

# Resolve the absolute project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Define key folder paths with environment overrides
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

# Common LLM options: "llama3.2:3b", "phi4:14b", "phi4:14b-q8_0" etc.
DEFAULT_MODEL = "phi4:14b"
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", DEFAULT_MODEL)

try:
    # Load LLM model with performance-optimized options (e.g. quantization)
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

DEFAULT_EMBED_MODEL = "nomic-embed-text"
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", DEFAULT_EMBED_MODEL)

try:
    # Attempt to load Ollama embedding model (preferred for local usage)
    EMBED_MODEL = OllamaEmbedding(model_name=EMBED_MODEL_NAME)
    logger.info("Using Ollama embedding model: %s", EMBED_MODEL_NAME)
except Exception as e:
    logger.warning(
        "Ollama embeddings not available; falling back to Hugging Face. Error: %s", e
    )
    EMBED_MODEL = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

# Apply model settings globally for use in LlamaIndex
Settings.llm = LLM_MODEL
Settings.embed_model = EMBED_MODEL

# ------------------- LLM Query Optimization -------------------

# Max input token size (affects how much context can be sent to the LLM)
# phi4 supports up to 16K tokens — use 8192 as a balanced default.
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", 8192))

# Max number of tokens for model output — capped to stay within context window
NUM_OUTPUT_TOKENS = min(2000, CONTEXT_WINDOW // 2)

# Retrieval parameters for similarity-based document search
SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", 5))  # Top-K matching chunks
SIMILARITY_CUTOFF = float(
    os.getenv("SIMILARITY_CUTOFF", 0.8)
)  # Minimum similarity threshold

# Max number of sources to include in the response
MAX_SOURCES = 3

# ------------------- Memory Management -------------------

# Time decay (in days) for memory retention logic
TIME_DECAY_DAYS = int(os.getenv("TIME_DECAY_DAYS", 3))

# Max length of user input stored in memory
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", 1500))

# ------------------- Adaptive Chunking -------------------

DYNAMIC_CHUNKING = {
    "thresholds": [500, 2000, 5000],  # Word count thresholds for strategies
    "sizes": [256, 512, 1024, 1536],  # Corresponding chunk sizes
    "overlap": [0.5, 0.3, 0.2, 0.1],  # Context overlap ratios
}

# ------------------- Debugging & Performance Logging -------------------

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
    logger.info("Debug Mode: ON")
    logger.info("Using LLM Model: %s", LLM_MODEL_NAME)
    logger.info("Using Embedding Model: %s", EMBED_MODEL_NAME)
    logger.info("Context Window: %d tokens", CONTEXT_WINDOW)
    logger.info("Output Tokens: %d tokens", NUM_OUTPUT_TOKENS)
    logger.info("Similarity Top-K: %d", SIMILARITY_TOP_K)
    logger.info("Similarity Cutoff: %f", SIMILARITY_CUTOFF)

# Prevent tokenizer-related deadlocks in parallel environments
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Ensure root and 'ChatRagi' loggers capture debug output if DEBUG_MODE is enabled
if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)  # root logger
    logging.getLogger("ChatRagi").setLevel(logging.DEBUG)  # project logger
