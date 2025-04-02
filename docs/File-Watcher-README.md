
#### File-Watcher - Automating Document Processing for ChatRagi

> [!INFO] Overview
> The **file_watcher.py** script is a service that monitors a specific folder (the “data” folder) for new document files. When a new file is detected, the script checks that the file is fully written and stable. If the file is valid and has not been processed before, it is sent to the document processing system for indexing. Processed files are then moved to an archive folder to prevent duplicate processing.

---
> [!attention] Key Benefits
>  - **Automation**: Automatically processes new documents as they are added to the data folder.
>  - **Reliability**: Ensures that only complete, stable, and unique files are processed.
> - **Efficiency**: Prevents duplicate processing by archiving files after indexing.
> - **Transparency**: Logs all operations and errors, making it easier to monitor and troubleshoot the system.
> 

---
> [!question] How it Works?
> 1. **Monitoring the Folder**
> 	The script uses a file system observer to continuously monitor the data folder. When a new file is created, an event is triggered.
> 2. **File Validation and Stability Check**
> 	Each file is checked to ensure it is not a hidden or system file and is fully written before processing. This prevents incomplete files from being processed.
> 3. **Processing and Archiving**
> 	Valid and stable files are processed to extract and index their content. Once processed, files are moved to an archive folder to ensure they are not re-indexed.
> 4. **Logging and Exception Handling**
> 	The script uses a centralized logging system to record actions and errors. This helps in diagnosing issues and maintaining the reliability of the system.

---
> [!summary]
    > The purpose of the **file_watcher.py** script is to automate the document indexing process for the ChatRagi chatbot application. This ensures that the system’s knowledge base is continuously updated with new documents without manual intervention!
