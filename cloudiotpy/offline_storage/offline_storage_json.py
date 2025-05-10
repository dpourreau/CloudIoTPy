"""
Thread-safe JSON-based offline storage for CloudIoTPy.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List

from cloudiotpy.common.exceptions import handle_exceptions
from cloudiotpy.offline_storage.offline_storage import OfflineStorage

logger = logging.getLogger(__name__)


class JSONOfflineStorage(OfflineStorage):
    """
    A thread-safe JSON-based offline store.

    This class:
    1. Loads the current JSON array of messages from disk.
    2. Appends or removes messages.
    3. Saves the updated array back to disk.

    All read/write operations are protected by a lock to avoid concurrent file
    access collisions.

    Examples
    --------
    .. code-block:: python

        storage = JSONOfflineStorage(Path("./offline_messages.json"))
        storage.add_messages([{ "telemetry": "data" }])
        messages = storage.load_messages(limit=10)
        removed_count = storage.remove_messages(messages)
    """

    def __init__(self, path: Path) -> None:
        """
        Initialize the JSONOfflineStorage.

        Parameters
        ----------
        path : Path
            The filesystem path to the JSON file for storing messages.
        """
        self.path = path
        self._lock = threading.Lock()

    @handle_exceptions(default_return_value=None)
    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Append new messages to the existing JSON list.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            The new messages to store.
        """
        if not messages:
            return

        with self._lock:
            current = self._load_entire_list()
            current.extend(messages)
            self._save_entire_list(current)

    @handle_exceptions(default_return_value=[])
    def load_messages(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Return up to ``limit`` oldest messages from the JSON file.

        Parameters
        ----------
        limit : int, optional
            The maximum number of messages to return. If 0 or negative, return
            all.

        Returns
        -------
        List[Dict[str, Any]]
            A list of messages in ascending order of insertion (oldest first).
        """
        with self._lock:
            current = self._load_entire_list()
            if limit <= 0:
                return current
            return current[:limit]

    @handle_exceptions(default_return_value=0)
    def remove_messages(self, messages: List[Dict[str, Any]]) -> int:
        """
        Remove occurrences of each message from the store.

        For each message in ``messages``, remove one matching dict if found.
        Passing duplicates attempts to remove each instance.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            The messages to remove.

        Returns
        -------
        int
            The total number of messages actually removed.
        """
        if not messages:
            return 0

        with self._lock:
            current = self._load_entire_list()
            removed_count = 0
            for msg in messages:
                if msg in current:
                    current.remove(msg)
                    removed_count += 1
            self._save_entire_list(current)
            return removed_count

    @handle_exceptions(default_return_value=[])
    def _load_entire_list(self) -> List[Dict[str, Any]]:
        """
        Load the entire list of messages from the JSON file.

        Returns
        -------
        List[Dict[str, Any]]
            A list of message dictionaries, or an empty list if the file is
            missing or the data is not a valid JSON list.
        """
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        else:
            logger.warning("%s does not contain a JSON list; ignoring.", self.path)
            return []

    @handle_exceptions(default_return_value=None)
    def _save_entire_list(self, all_data: List[Dict[str, Any]]) -> None:
        """
        Overwrite the JSON file with the given list of messages.

        Parameters
        ----------
        all_data : List[Dict[str, Any]]
            The list of messages to write to disk.
        """
        if not all_data:
            # Optionally remove the file if empty
            if self.path.exists():
                self.path.unlink()
                logger.debug("Removed empty JSON file %s", self.path)
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(all_data, f)
