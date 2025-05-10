"""
Offline Storage Service for CloudIoTPy.
"""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from cloudiotpy.common.exceptions import handle_exceptions
from cloudiotpy.config import config
from cloudiotpy.offline_storage import JSONOfflineStorage, OfflineStorage, SQLiteOfflineStorage

logger = logging.getLogger(__name__)


class OfflineStorageService:
    """
    Manages offline storage creation and provides store-and-forward methods.

    This service automatically creates an offline storage backend (JSON or
    SQLite) based on global configuration. It also integrates with an IoT
    client to flush stored messages to the cloud when the client is connected.
    """

    def __init__(self) -> None:
        """
        Initialize the offline storage backend based on global configuration.

        Notes
        -----
        Sets up the correct `OfflineStorage` implementation and stores a
        reference to the IoT client when `attach_client` is called.
        """
        self._lock = threading.Lock()
        self._storage: Optional[OfflineStorage] = None
        self._client = None  # Will store a reference to the IoT client if needed

        # Create offline storage from config
        self._storage = self._create_offline_storage()

    def attach_client(self, client) -> None:
        """
        Store a reference to the IoT client.

        Parameters
        ----------
        client : Any
            The IoT client object that provides a `send_telemetry` method and
            an `is_connected` method.
        """
        self._client = client

    @handle_exceptions(default_return_value=None, log_exception=True)
    def add_message(self, data: Dict[str, Any]) -> None:
        """
        Add a single message to offline storage if available.

        Parameters
        ----------
        data : Dict[str, Any]
            The message data to store offline.
        """
        if not self._storage:
            logger.warning("Offline storage is disabled; message will be discarded.")
            return

        with self._lock:
            self._storage.add_messages([data])

    @handle_exceptions(default_return_value=None, log_exception=True)
    def flush_data(self) -> None:
        """
        Flush messages from offline storage to the cloud if connected.

        This method loads messages in batches (default size 10), attempts to
        send them via the attached IoT client, and removes successfully sent
        messages from storage. If any message fails to send, the flush stops.
        """
        if not self._storage:
            return

        if not self._client or not self._client.is_connected():
            return

        with self._lock:
            while True:
                batch = self._storage.load_messages(limit=10)
                if not batch:
                    break

                success_count = 0
                for msg in batch:
                    if self._client.send_telemetry(msg):
                        success_count += 1
                    else:
                        # Stop if sending fails
                        break

                if success_count > 0:
                    removed = self._storage.remove_messages(batch[:success_count])
                    logger.info("Flushed %d offline messages to cloud.", removed)

                if success_count < len(batch):
                    logger.error("Failed to send some messages in the batch, stopping flush.")
                    break

    def _create_offline_storage(self) -> Optional[OfflineStorage]:
        """
        Create the storage backend from global configuration.

        Returns
        -------
        OfflineStorage or None
            The configured storage, or None if not configured.
        """
        storage_type = config.get_offline_storage_type().lower().strip()
        storage_path = config.get_offline_storage_path()

        if not storage_path:
            logger.warning("No offline storage path provided, offline caching disabled.")
            return None

        if storage_type == "json":
            return JSONOfflineStorage(path=storage_path)
        elif storage_type == "sqlite":
            return SQLiteOfflineStorage(path=storage_path)
        else:
            logger.error("Unknown offline storage type '%s', none used.", storage_type)
            return None
