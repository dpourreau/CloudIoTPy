"""
Unit tests for the SQLiteOfflineStorage class.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from cloudiotpy.offline_storage import SQLiteOfflineStorage


class TestSQLiteOfflineStorage(unittest.TestCase):
    """
    Test cases for the SQLiteOfflineStorage class.

    Verifies creation of the database and table, handling of messages through
    add, load, and remove operations, and edge cases such as empty inputs.
    """

    def setUp(self) -> None:
        """
        Prepare a temporary database for each test.

        Creates a temporary directory, instantiates SQLiteOfflineStorage, and
        sets up sample messages.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_storage.db"
        self.storage = SQLiteOfflineStorage(self.db_path)

        self.test_messages = [
            {"id": 1, "data": "test1", "timestamp": 1614556800},
            {"id": 2, "data": "test2", "timestamp": 1614556801},
            {"id": 3, "data": "test3", "timestamp": 1614556802},
        ]

    def tearDown(self) -> None:
        """
        Clean up the temporary database after each test.
        """
        self.temp_dir.cleanup()

    def test_init(self) -> None:
        """
        Check initialization creates a valid database and table.

        Ensures the DB file is present and the 'offline_messages' table exists.
        """
        self.assertEqual(self.storage.db_path, self.db_path)
        self.assertTrue(self.db_path.exists())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' " "AND name='offline_messages'")
            tables = cursor.fetchall()
            self.assertEqual(len(tables), 1)

    def test_add_messages_empty(self) -> None:
        """
        Verify adding an empty list of messages changes nothing.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM offline_messages")
            initial_count = cursor.fetchone()[0]

        self.storage.add_messages([])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM offline_messages")
            final_count = cursor.fetchone()[0]

        self.assertEqual(initial_count, final_count)

    def test_add_messages(self) -> None:
        """
        Confirm rows are inserted for each added message.
        """
        self.storage.add_messages(self.test_messages)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM offline_messages")
            count = cursor.fetchone()[0]
        self.assertEqual(count, 3)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT data FROM offline_messages " "ORDER BY id ASC")
            rows = cursor.fetchall()
        for i, row in enumerate(rows):
            stored_msg = json.loads(row[0])
            self.assertEqual(stored_msg, self.test_messages[i])

    def test_load_messages_empty(self) -> None:
        """
        Validate that loading from an empty DB returns an empty list.
        """
        messages = self.storage.load_messages()
        self.assertEqual(messages, [])

    def test_load_messages_all(self) -> None:
        """
        Ensure loading with limit=0 returns all messages.
        """
        self.storage.add_messages(self.test_messages)
        messages = self.storage.load_messages(0)
        self.assertEqual(len(messages), 3)
        for i, msg in enumerate(messages):
            db_id = msg.pop("_db_id")
            self.assertEqual(msg, self.test_messages[i])
            self.assertIsInstance(db_id, int)

    def test_load_messages_limit(self) -> None:
        """
        Confirm loading with a limit returns the correct subset.
        """
        self.storage.add_messages(self.test_messages)
        messages = self.storage.load_messages(2)
        self.assertEqual(len(messages), 2)
        for i, msg in enumerate(messages):
            db_id = msg.pop("_db_id")
            self.assertEqual(msg, self.test_messages[i])

    def test_remove_messages_empty(self) -> None:
        """
        Verify removing an empty list returns 0.
        """
        count = self.storage.remove_messages([])
        self.assertEqual(count, 0)

    def test_remove_messages(self) -> None:
        """
        Remove messages by their _db_id and confirm the row count changes.
        """
        self.storage.add_messages(self.test_messages)
        loaded_messages = self.storage.load_messages()
        count = self.storage.remove_messages([loaded_messages[0]])
        self.assertEqual(count, 1)
        remaining = self.storage.load_messages()
        self.assertEqual(len(remaining), 2)
        for i, msg in enumerate(remaining):
            db_id = msg.pop("_db_id")
            self.assertEqual(msg, self.test_messages[i + 1])

    def test_remove_nonexistent_message(self) -> None:
        """
        Removing a non-existent _db_id results in 0 removals.
        """
        self.storage.add_messages(self.test_messages)
        non_existent = {"_db_id": 999, "data": "nonexistent"}
        count = self.storage.remove_messages([non_existent])
        self.assertEqual(count, 0)
        messages = self.storage.load_messages()
        self.assertEqual(len(messages), 3)

    def test_remove_message_without_db_id(self) -> None:
        """
        Removing a message lacking _db_id should result in 0 removals.
        """
        self.storage.add_messages(self.test_messages)
        count = self.storage.remove_messages([{"id": 1, "data": "test1"}])
        self.assertEqual(count, 0)
        messages = self.storage.load_messages()
        self.assertEqual(len(messages), 3)

    def test_add_after_remove(self) -> None:
        """
        Ensure the DB can be reused after all messages are removed.
        """
        self.storage.add_messages(self.test_messages[:2])
        loaded_messages = self.storage.load_messages()
        self.storage.remove_messages(loaded_messages)
        new_message = {"id": 4, "data": "test4", "timestamp": 1614556803}
        self.storage.add_messages([new_message])
        messages = self.storage.load_messages()
        self.assertEqual(len(messages), 1)
        msg = messages[0]
        db_id = msg.pop("_db_id")
        self.assertEqual(msg, new_message)

    def test_thread_safety(self) -> None:
        """
        Placeholder for a more comprehensive thread safety test.
        """
        pass


if __name__ == "__main__":
    unittest.main()
