"""
SQLite Offline Storage Implementation for CloudIoTPy.
"""

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List

from cloudiotpy.common.exceptions import handle_exceptions
from cloudiotpy.offline_storage.offline_storage import OfflineStorage

logger = logging.getLogger(__name__)


class SQLiteOfflineStorage(OfflineStorage):
    """
    Thread-safe SQLite implementation of the OfflineStorage interface.

    Each message is stored with an auto-increment ID and a JSON column named
    'data'. This class ensures concurrency with a thread lock and uses
    transactions for batch inserts.
    """

    def __init__(self, path: Path) -> None:
        """
        Initialize the SQLiteOfflineStorage.

        Parameters
        ----------
        path : Path
            Path to the SQLite database file. The file is created if it does
            not exist.
        """
        self.path = path
        self._lock = threading.Lock()
        self._init_db()

    @handle_exceptions(default_return_value=None)
    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Insert new rows for each message in one transaction.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            A list of JSON-serializable messages to store.
        """
        if not messages:
            return

        with self._lock, sqlite3.connect(self.path) as conn:
            conn.execute("BEGIN")
            for msg in messages:
                try:
                    raw = json.dumps(msg)
                    conn.execute("INSERT INTO offline_messages (data) VALUES (?)", (raw,))
                except Exception as enc_exc:
                    logger.error(
                        "Failed to encode message %s as JSON: %s",
                        msg,
                        enc_exc,
                    )
            conn.commit()
            logger.debug(
                "Inserted %d new messages into %s",
                len(messages),
                self.path,
            )

    @handle_exceptions(default_return_value=[])
    def load_messages(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Load stored messages up to the specified limit.

        Parameters
        ----------
        limit : int, optional
            Number of messages to retrieve. If limit <= 0, all messages
            are loaded, by default 0.

        Returns
        -------
        List[Dict[str, Any]]
            A list of messages as dictionaries, each with an injected
            '_db_id' field for deletion.
        """
        with self._lock, sqlite3.connect(self.path) as conn:
            if limit > 0:
                rows = conn.execute(
                    "SELECT id, data FROM offline_messages " "ORDER BY id ASC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT id, data FROM offline_messages ORDER BY id ASC").fetchall()

            results = []
            for row_id, raw_json in rows:
                try:
                    parsed = json.loads(raw_json)
                    parsed["_db_id"] = row_id
                    results.append(parsed)
                except Exception as parse_exc:
                    logger.error(
                        "Failed to parse JSON for row %s: %s",
                        row_id,
                        parse_exc,
                    )

            logger.debug(
                "Loaded %d messages from %s (limit=%d).",
                len(results),
                self.path,
                limit,
            )
            return results

    @handle_exceptions(default_return_value=0)
    def remove_messages(self, messages: List[Dict[str, Any]]) -> int:
        """
        Remove messages from the database using their '_db_id' field.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            A list of messages (typically returned by load_messages) to remove.
            Each message should have a valid '_db_id'.

        Returns
        -------
        int
            The total number of messages actually removed.
        """
        if not messages:
            return 0

        row_ids = []
        for msg in messages:
            row_id = msg.get("_db_id")
            if isinstance(row_id, int):
                row_ids.append(row_id)
            else:
                logger.warning("Message lacks valid '_db_id': %s", msg)

        if not row_ids:
            return 0

        with self._lock, sqlite3.connect(self.path) as conn:
            placeholders = ",".join(["?"] * len(row_ids))
            sql = f"DELETE FROM offline_messages WHERE id IN ({placeholders})"
            cur = conn.execute(sql, row_ids)
            removed = cur.rowcount
            logger.debug(
                "Removed %d messages from %s in one query. IDs: %s",
                removed if removed is not None else 0,
                self.path,
                row_ids,
            )
            return removed if removed is not None else 0

    @handle_exceptions(log_exception=True)
    def _init_db(self) -> None:
        """
        Initialize the SQLite database.

        Creates the offline_messages table if it does not exist and ensures that
        the parent directory of the database file is present.
        """
        parent_dir = self.path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Created directory for SQLite database: %s", parent_dir)

        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS offline_messages (
                    id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT    NOT NULL
                )
                """
            )
        logger.debug("Ensured table 'offline_messages' exists in %s", self.path)
