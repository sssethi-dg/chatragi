# Web Application Backend

The `app.py` module is the Flask-based backend for ChatRagi.  
It powers the Web UI, handles user queries, manages contextual memory, and orchestrates structured prompt generation — all while interacting with a local vector database and LLM engine.

This file serves as the main entry point for running the chatbot web server.

---

## Core Responsibilities

- Serves the chat interface (`index.html`).
- Routes user queries to the LLM engine with contextual memory.
- Applies persona tone instructions to response generation.
- Stores responses for future memory-aware interactions.
- Exposes API endpoints for document listing, chat memory, and reindexing.
- Handles logging, formatting, and error responses for frontend clients.

---

## API Routes and Endpoints

### `GET /`

Renders the homepage using `templates/index.html` — the main chat interface.

---

### `POST /ask`

Processes a user question and returns a styled LLM-generated response.

**Input (JSON):**
```json
{
  "query": "What is retrieval-augmented generation?",
  "persona": "professional"
}
```

**Output (JSON):**
```json
{
  "answer": "<Markdown formatted HTML>",
  "raw_answer": "...",
  "citations": ["source1.pdf", "notes.md"]
}
```

**Under the hood**:
- Retrieves relevant memory and documents from ChromaDB.
- Builds a structured prompt (includes persona instructions if selected).
- Sends the prompt to the local LLM (e.g., phi4 via Ollama).
- Returns a Markdown-formatted answer and citations.
- Stores the **neutral** version of the response for memory consistency.

---

### GET /list-documents

Returns all indexed documents stored in ChromaDB.

**Example:**
```json
{
  "documents": ["business-report.pdf", "notes.txt"]
}
```

---

### GET /all-memories

Returns all stored chatbot memory entries.

**Example:**
```json
{
  "memories": [
    {
      "user_query": "What is data governance?",
      "conversation": "Data governance is...",
      "timestamp": "...",
      "important": false
    }
  ]
}
```

---

### POST /store-memory

Saves a conversation pair to persistent memory storage.

**Input (JSON):**
```json
{
  "user_query": "What is a vector database?",
  "response": "A vector database is...",
  "is_important": true
}
```

---
### POST /refresh

Triggers a re-ingestion of documents and rebuilds the ChromaDB vector index.

Use this endpoint when you’ve added new documents and want to update the index without restarting the app.

---

### Logging

- Centralized via `logger_config.py`
- Outputs runtime events, query handling, errors, and indexing activity to the `logs/` folder
- Helps with debugging and performance tracing

---

### Error Handling

- Global error handler wraps all endpoints
- Returns structured JSON error messages for frontend display and debugging
- Logs all exceptions with stack traces for visibility

---

### How to Start the Web App

From the project root, run:
```bash
python src/chatragi/app.py
```

---

### Sample Output

```text
INFO - ChatRagi - Refreshing index...
INFO - ChatRagi - Index is ready.
* Running on http://127.0.0.1:5000
```

Then open your browser at: http://127.0.0.1:5000

> 🛑 To stop the service, press Ctrl + C.

---

## Development Notes

- Responses are returned as Markdown and rendered client-side.
- Memory is saved as (user_query, raw_answer) pairs with timestamps and importance flags.
- Index refresh is handled by the llama_index module.
- Persona tone behavior is defined in `persona.py`.

**Customization Points:**

- `chatbot.py`: Query logic and structured prompting.
- `chat_memory.py`: Memory handling and deduplication.
- `persona.py`: Persona tone control and style logic.

---

### Summary

The `app.py` backend ties together ChatRagi’s Web UI, local LLM engine, and vector store.
It’s designed to be:
- **Lightweight** — optimized for local execution.
- **Modular** — easily extensible and debuggable.
- **Private** — no external APIs, no cloud dependencies.

> This is the orchestration layer that transforms your data into personalized, context-rich, Markdown-formatted answers — entirely offline.