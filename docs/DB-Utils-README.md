# DB-Utils

## Overview

The **db_utils.py** module provides utility functions to manage the database for the ChatRagi chatbot application. It connects to the ChromaDB database and manages tasks such as cleaning up outdated chatbot conversations, listing indexed documents, and deleting specific documents.

---
## Key Functions

1. **delete_non_important_memories**
	This function removes chatbot memories that are older than a specified number of days (defined by the configuration) unless they are marked as important. This ensures that the database does not become overloaded with old or unnecessary data.
2. **log_indexed_documents**
	This function logs the total number of documents currently indexed in the database. It helps keep track of the database size and the growth of stored content.
3. **list_collections**
	This function retrieves and prints the names of all collections currently stored in the database. It is useful for verifying that the system is correctly organizing documents.
4. **list_documents**
	This function gathers the names of all indexed documents and returns a sorted list of unique filenames. This can be used for reporting or verification purposes.
5. **delete_document_by_filename**
	This function deletes a specific document from the database by its filename. This is useful for removing outdated or unwanted documents from the index.

---
## How it Works?

- **Initialization:**
	Upon startup, the module attempts to connect to the ChromaDB database. If the connection is successful, it creates or retrieves collections for chatbot memory and document indexing.
- **Memory Management:**
	The module automatically deletes chatbot memory entries that are older than the configured time limit unless they are flagged as important. This helps in managing the size of the memory storage.
- **Document Management:**
	The module provides functions to list all indexed documents, list all collections, and delete documents based on their filenames. These functions ensure that the database remains organized and that duplicate or unwanted entries can be efficiently managed.
- **Logging:**
	All operations are logged using a centralized logging configuration. This includes successful operations and any errors encountered during database interactions, which aids in troubleshooting and maintenance.

---
## Summary

The **db_utils.py** module is a crucial part of the ChatRagi application, as it handles all interactions with the database. It ensures efficient memory and document management while providing clear logging for monitoring system health. This design helps maintain a clean and well-organized database, which in turn supports the overall performance and reliability of the chatbot application.

