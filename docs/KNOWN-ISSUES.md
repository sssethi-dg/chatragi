# Known Issues

This document lists known issues and current limitations in **ChatRagi v1.1.0**. These items are being tracked for resolution in future releases.

---

## 1. Real-Time Queuing Delay During File Ingestion
- **Issue**: New files added to the /data/ folder are not always immediately searchable, even after being processed by the File Watcher.
- **Cause**: The query engine doesn’t automatically refresh its in-memory index when new vectors are added.
- **Workaround**: Use the **Refresh Index** button in the Web UI or restart the app.
- **Planned Fix**: Add event-driven refresh logic (scheduled for v1.2).

---

## 2. Inconsistent Source Ranking from ChromaDB
- **Issue**: The “Top 3 Sources” in the Web UI may not reflect the most relevant matches.
- **Cause**: ChromaDB does not currently support strict source-level ranking in multi-node retrieval.
- **Impact**: Responses may cite documents with weaker relevance.
- **Planned Fix**: Explore hybrid re-ranking or alternate vector stores (e.g., Qdrant, FAISS).

---

## 3. Semaphore Warning on App Shutdown
- **Message**:
```bash
resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown
```

- **Cause**: Python multiprocessing cleanup on macOS when Ctrl + C is used.
- **Impact**: Harmless. No functional or data loss concerns.
- **Planned Fix**: Suppress or gracefully handle cleanup in v1.2.

---

## 4. No Native GPU Acceleration in Docker (Apple Silicon)
- **Issue**: Ollama models run slower in Docker on macOS M1/M2.
- **Cause**: Docker containers can’t access Apple’s Metal framework for GPU acceleration.
- **Workaround**: Run ChatRagi natively outside of Docker for optimal speed.
- **Status**: Documented limitation — no fix planned.

---

## 5. Occasional Markdown Formatting Drift
- **Issue**: Some answers may show inconsistent list spacing or markdown formatting.
- **Cause**: LLM may deviate slightly from structured prompt expectations.
- **Planned Fix**: Optional STRICT_MARKDOWN_MODE toggle under consideration for v1.2.


