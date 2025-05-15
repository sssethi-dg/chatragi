# Configuration Overview

The `config.py` module defines global system settings for ChatRagi — including paths, model names, and feature flags.  
It acts as the central control hub that powers the document pipeline, memory system, and local model behavior.

---

## Core Responsibilities

- Define key folder paths (documents, memory storage, logs, vector DB).
- Specify default model names for embeddings and LLM responses.
- Configure optional runtime toggles (e.g., debug UI, markdown formatting).
- Allow flexible overrides via environment variables.

---

## Configuration Variables

| Variable | Purpose | Default Value |
|:---------|:--------|:--------------|
| `PROJECT_ROOT` | Root directory of the project | auto-detected |
| `DB_PATH` | Path to ChromaDB vector store | `chroma_db/` |
| `DATA_FOLDER` | Incoming files for ingestion | `data/` |
| `ARCHIVE_FOLDER` | Archive of processed documents | `archive/` |
| `PERSIST_DIR` | Folder for saved chatbot outputs | `storage/` |
| `LOG_FOLDER` | Folder for logs and diagnostics | `logs/` |
| `EMBED_MODEL` | Embedding model via Ollama | `nomic-embed-text` |
| `LLM_MODEL` | Chat model via Ollama | `phi4` |
| `DEBUG_MODE_UI` | Show debug info in Web UI | `False` |
| `STRICT_MARKDOWN_MODE` | Enforce stricter output formatting | `False` |

> 🔧 `DEBUG_MODE_UI`: Adds dev info overlays in the chat interface.  
> 📐 `STRICT_MARKDOWN_MODE`: Strips extra LLM flair for clean Markdown output.

---

## Folder Structure Impact

These directories are **auto-created** at runtime:

| Folder       | Purpose                                       |
|--------------|-----------------------------------------------|
| `data/`      | New files waiting for ingestion               |
| `archive/`   | Processed files, moved after ingestion        |
| `chroma_db/` | Vector store for embeddings and memory        |
| `logs/`      | Application and ingestion logs                |
| `storage/`   | Memory entries and response outputs           |

---

## Modules That Use `config.py`

- `file_watcher.py` — file monitoring and document ingestion.
- `chatbot.py` — embedding/query model selection.
- `chat_memory.py` — path to memory persistence store.
- `logger_config.py` — logs folder.
- `app.py` — integrates all configuration into the backend service.

---

## Why It Matters

Centralizing configuration in one file:
- Simplifies debugging and tuning
- Makes the app portable and environment-agnostic
- Enables quick switching of models or paths
- Improves local development and deployment workflows

---

## How to Override Settings

You can override any configuration using environment variables (no need to modify the file).

**Example (bash):**
```bash
export EMBED_MODEL="custom-embedding-model"
export DEBUG_MODE_UI=true
```

> 💡 **Tip:** Use a `.env` file with [python-dotenv](https://pypi.org/project/python-dotenv/) to auto-load environment variables at runtime.

---

## Summary

The `config.py` file is ChatRagi’s **central control system** — defining how the app loads data, stores vectors, logs behavior, and interacts with models.  
Mastering this module gives you full control over how ChatRagi behaves and scales across different environments.
