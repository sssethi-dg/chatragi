"""
File Watcher Service for ChatRagi

Monitors the data folder for new document files and processes them for
indexing.
Processed files are archived to avoid duplicate indexing.
"""

import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from chatragi.config import DATA_FOLDER
from chatragi.utils.db_utils import chroma_client
from chatragi.utils.document_loader import process_new_documents
from chatragi.utils.logger_config import logger

# Track already-processed files
processed_files = set()


def is_valid_file(file_name: str) -> bool:
    """
    Checks if the file is valid (ignores hidden/system files).

    Args:
        file_name (str): Name of the file.

    Returns:
        bool: True if valid, False otherwise.
    """
    return not file_name.startswith(".")


def is_file_stable(file_path: str, wait_time: int = 2) -> bool:
    """
    Verifies if the file is stable by checking if size remains constant.

    Args:
        file_path (str): Full path to the file.
        wait_time (int): Wait time before re-checking (seconds).

    Returns:
        bool: True if file is stable, False otherwise.
    """
    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(wait_time)
        current_size = os.path.getsize(file_path)
        return initial_size == current_size
    except Exception as e:
        logger.exception(
            "Error checking file stability for '%s': %s",
            file_path,
            e,
        )
        return False


def process_existing_files():
    """
    Processes all existing unprocessed files found in the data folder.
    """
    logger.info("Checking for unprocessed files in data folder...")

    try:
        doc_collection = chroma_client.get_or_create_collection("doc_index")
        existing_docs = set(doc_collection.get().get("documents", []))

        for file_name in os.listdir(DATA_FOLDER):
            file_path = os.path.join(DATA_FOLDER, file_name)

            if not os.path.isfile(file_path) or not is_valid_file(file_name):
                continue

            if file_name in existing_docs:
                logger.info(
                    "File '%s' is already indexed. Skipping.",
                    file_name,
                )
                continue

            if is_file_stable(file_path):
                logger.info("Found unprocessed file: %s", file_path)
                process_new_documents(file_path)
                processed_files.add(file_name)

        indexed_count = len(doc_collection.get().get("documents", []))
        logger.info(
            "ChromaDB now contains %d indexed document chunks.",
            indexed_count,
        )

    except Exception as e:
        logger.exception("Error processing existing files: %s", e)


class NewFileHandler(FileSystemEventHandler):
    """
    Custom handler for new file creation events.
    """

    def on_created(self, event):
        """
        Handles a new file created in the watched folder.

        Args:
            event (FileSystemEvent): New file event details.
        """
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        try:
            if (
                file_name in processed_files
                or not os.path.exists(file_path)
                or not is_valid_file(file_name)
            ):
                return

            logger.info("New file detected: %s", file_path)

            if not is_file_stable(file_path):
                logger.warning(
                    "Skipping file '%s' as it may still be copying.", file_name
                )
                return

            process_new_documents(file_path)
            processed_files.add(file_name)

            doc_collection = chroma_client.get_or_create_collection(
                "doc_index"
            )
            indexed_count = len(doc_collection.get().get("documents", []))
            logger.info(
                "ChromaDB now contains %d indexed document chunks.",
                indexed_count,
            )

        except Exception as e:
            logger.exception(
                "Error processing new file '%s': %s",
                file_name,
                e,
            )


if __name__ == "__main__":
    """
    Main execution block to start file watcher service.
    """
    logger.info("Starting File Watcher Service...")

    observer = None

    try:
        process_existing_files()

        observer = Observer()
        event_handler = NewFileHandler()
        observer.schedule(event_handler, path=DATA_FOLDER, recursive=False)

        logger.info("Watching '%s' for new files...", DATA_FOLDER)
        observer.start()

        while True:
            time.sleep(5)

    except KeyboardInterrupt:
        logger.warning("File watcher stopped by user.")
        if observer:
            observer.stop()

    except Exception as e:
        logger.exception("Unexpected error in file watcher: %s", e)
        if observer:
            observer.stop()

    finally:
        if observer:
            observer.join()
