"""
File Watcher Service for ChatRagi

This module monitors the designated data folder for new document files and processes
them for indexing. Processed files are archived to avoid duplicate indexing.
"""

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from chatragi.config import DATA_FOLDER
from chatragi.utils.document_loader import process_new_documents
from chatragi.utils.db_utils import chroma_client
from chatragi.utils.logger_config import logger  # Import centralized logger

# Set to track processed files and avoid redundant processing
processed_files = set()

def is_valid_file(file_name: str) -> bool:
    """
    Determines if a file should be processed by ignoring hidden or system files.

    Args:
        file_name (str): The name of the file.

    Returns:
        bool: True if the file is valid for processing, False otherwise.
    """
    # Ignore hidden files (e.g., .DS_Store)
    return not file_name.startswith(".")


def is_file_stable(file_path: str, wait_time: int = 2) -> bool:
    """
    Checks if a file is stable (i.e., not being modified) by comparing its size
    over a brief period.

    Args:
        file_path (str): The full path to the file.
        wait_time (int, optional): Time in seconds to wait before rechecking the file size. Defaults to 2.

    Returns:
        bool: True if the file size remains unchanged, False otherwise.
    """
    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(wait_time)
        current_size = os.path.getsize(file_path)
        return initial_size == current_size
    except Exception as e:
        logger.exception("Error checking file stability for '%s': %s", file_path, e)
        return False


def process_existing_files():
    """
    Processes all existing unprocessed files in the data folder.

    This function scans the data folder for files that have not yet been indexed.
    It checks that each file is stable and not already indexed before processing.
    """
    logger.info("Checking for unprocessed files in data folder...")

    try:
        # Retrieve existing document references from ChromaDB for quick lookup
        doc_collection = chroma_client.get_or_create_collection("doc_index")
        existing_docs = set(doc_collection.get().get("documents", []))

        for file_name in os.listdir(DATA_FOLDER):
            file_path = os.path.join(DATA_FOLDER, file_name)

            # Skip non-files and hidden files
            if not os.path.isfile(file_path) or not is_valid_file(file_name):
                continue

            # Skip processing if file is already indexed in ChromaDB
            if file_name in existing_docs:
                logger.info("File '%s' is already indexed. Skipping.", file_name)
                continue

            # Process the file only if it is stable (fully written)
            if is_file_stable(file_path):
                logger.info("Found unprocessed file: %s", file_path)
                process_new_documents(file_path)
                processed_files.add(file_name)

        # Log the current count of indexed document chunks
        indexed_count = len(doc_collection.get().get("documents", []))
        logger.info("ChromaDB now contains %d indexed document chunks.", indexed_count)

    except Exception as e:
        logger.exception("Error processing existing files: %s", e)


class NewFileHandler(FileSystemEventHandler):
    """
    Custom event handler for new file events.

    This class processes new files created in the data folder, ensuring that each
    file is stable and has not already been processed before sending it for indexing.
    """

    def on_created(self, event):
        """
        Handles the file creation event.

        Args:
            event (FileSystemEvent): Event data containing file details.
        """
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        try:
            # Ignore files that have already been processed or are invalid
            if file_name in processed_files or not os.path.exists(file_path) or not is_valid_file(file_name):
                return

            logger.info("New file detected: %s", file_path)

            # Process the file only if it is stable (i.e., not still being copied)
            if not is_file_stable(file_path):
                logger.warning("Skipping file '%s' as it may still be copying.", file_name)
                return

            # Process the new document and mark it as processed
            process_new_documents(file_path)
            processed_files.add(file_name)

            # Log the updated count of indexed document chunks
            doc_collection = chroma_client.get_or_create_collection("doc_index")
            indexed_count = len(doc_collection.get().get("documents", []))
            logger.info("ChromaDB now contains %d indexed document chunks.", indexed_count)

        except Exception as e:
            logger.exception("Error processing new file '%s': %s", file_name, e)


if __name__ == "__main__":
    """
    Main execution block for the file watcher service.

    Processes existing files in the data folder and starts the real-time file monitoring service.
    """
    logger.info("Starting File Watcher Service...")

    try:
        # Process any existing unprocessed files at startup
        process_existing_files()

        # Set up the file system observer for real-time monitoring
        observer = Observer()
        event_handler = NewFileHandler()
        observer.schedule(event_handler, path=DATA_FOLDER, recursive=False)

        logger.info("Watching '%s' for new files...", DATA_FOLDER)
        observer.start()
        
        # Main loop: keep the script running in the background
        while True:
            time.sleep(5)  # Keep the observer running in the background

    except KeyboardInterrupt:
        logger.warning("File watcher stopped by user.")
        observer.stop()
        observer.join()  # Wait for the observer to fully stop before exiting

    except Exception as e:
        logger.exception(f"Unexpected error in file watcher: {e}")
        observer.stop()
        observer.join()

    finally:
        # Optional: join thread if no exceptions occur
        observer.join()