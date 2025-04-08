# Document-Loader

#### Overview
The **document_loader.py** module is a key component of the ChatRagi project. Its primary purpose is to ingest documents of various types (such as PDF, CSV, JSON, and TXT), split their content into smaller, manageable chunks, and enrich these chunks with metadata. The module also checks for duplicate documents by computing a unique hash for each file and its content. Processed files are moved to an archive folder to prevent repeated processing.

---
#### Key Benefits
- **Automation:** Automatically ingests and processes new documents.
- **Efficiency:** Splits large documents into manageable chunks for improved indexing performance.
- **Duplicate Detection:** Uses file and chunk hashes to prevent redundant processing.
- **Robustness:** Comprehensive logging and exception handling ensure reliable operation.

---
#### How it Works?
1. **Document Ingestion:**
	The module supports several file formats. When a new document is provided, the corresponding loader function extracts the text content from the file.
2. **Text Chunking:**
	The extracted text is split into smaller segments, or chunks, based on estimated token counts and natural sentence boundaries. Overlap is added between chunks to ensure contextual continuity.
3. **Metadata Enrichment:**
	Each chunk is enriched with metadata, including the source file name, file type, and a computed hash. The hash is used to detect duplicates, ensuring that identical documents are not reprocessed.
4. **Indexing and Storage:**
	Once processed, the text chunks are converted into Document objects and stored in a vector database (ChromaDB) for later retrieval by the chatbot. This enables fast and accurate response generation.
5. **Archiving:**
	After successful processing, the original document is moved to an archive folder. This prevents the same file from being processed multiple times.
6. **Logging and Exception Handling:**\
	The module includes comprehensive logging and error handling to record important events and issues. This aids in monitoring the document ingestion process and troubleshooting any problems.  