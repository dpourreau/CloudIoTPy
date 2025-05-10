"""
Unit tests for the JSONOfflineStorage class.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from cloudiotpy.offline_storage import JSONOfflineStorage


class TestJSONOfflineStorage(unittest.TestCase):
    """
    Test cases for the JSONOfflineStorage class.

    Verifies that JSONOfflineStorage correctly adds, loads, and removes
    messages, including edge cases like empty and non-existent files.
    """

    def setUp(self) -> None:
        """
        Set up a temporary file for each test.

        Initializes a JSONOfflineStorage instance with a temporary JSON file.
        Also prepares a list of sample test messages.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name) / "test_storage.json"
        self.storage = JSONOfflineStorage(self.temp_path)

        # Sample test messages
        self.test_messages = [
            {"id": 1, "data": "test1", "timestamp": 1614556800},
            {"id": 2, "data": "test2", "timestamp": 1614556801},
            {"id": 3, "data": "test3", "timestamp": 1614556802},
        ]

    def tearDown(self) -> None:
        """
        Clean up the temporary directory after each test.
        """
        self.temp_dir.cleanup()

    def test_init(self) -> None:
        """
        Test initialization of the JSONOfflineStorage object.

        Ensures the storage path is set and no file is created until data is
        actually added.
        """
        self.assertEqual(self.storage.path, self.temp_path)
        self.assertFalse(self.temp_path.exists())

    def test_add_messages_empty(self) -> None:
        """
        Test adding an empty list of messages.

        Verifies no file is created and storage remains empty.
        """
        self.storage.add_messages([])
        self.assertFalse(self.temp_path.exists())

    def test_add_messages(self) -> None:
        """
        Test adding a list of messages.

        Verifies that the JSON file is created and contains all messages.
        """
        self.storage.add_messages(self.test_messages)
        self.assertTrue(self.temp_path.exists())
        with open(self.temp_path, "r") as f:
            stored_data = json.load(f)
        self.assertEqual(len(stored_data), 3)
        self.assertEqual(stored_data, self.test_messages)

    def test_load_messages_empty(self) -> None:
        """
        Test loading messages from a non-existent file.

        Verifies an empty list is returned when the file does not exist.
        """
        messages = self.storage.load_messages()
        self.assertEqual(messages, [])

    def test_load_messages_all(self) -> None:
        """
        Test loading all messages when limit=0.

        Verifies it returns all added messages.
        """
        self.storage.add_messages(self.test_messages)
        messages = self.storage.load_messages(0)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages, self.test_messages)

    def test_load_messages_limit(self) -> None:
        """
        Test loading messages with a specific limit.

        Verifies only the first N messages are returned.
        """
        self.storage.add_messages(self.test_messages)
        messages = self.storage.load_messages(2)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages, self.test_messages[:2])

    def test_remove_messages_empty(self) -> None:
        """
        Test removing an empty list of messages.

        Verifies that remove_messages returns 0 and nothing changes.
        """
        count = self.storage.remove_messages([])
        self.assertEqual(count, 0)

    def test_remove_messages(self) -> None:
        """
        Test removing a subset of messages.

        Verifies only the specified messages are removed from storage.
        """
        self.storage.add_messages(self.test_messages)
        count = self.storage.remove_messages([self.test_messages[0]])
        self.assertEqual(count, 1)
        messages = self.storage.load_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages, self.test_messages[1:])

    def test_remove_nonexistent_message(self) -> None:
        """
        Test removing a message that does not exist in storage.

        Verifies that the remove count is 0 and the stored data is unchanged.
        """
        self.storage.add_messages(self.test_messages)
        non_existent = {"id": 999, "data": "nonexistent"}
        count = self.storage.remove_messages([non_existent])
        self.assertEqual(count, 0)
        messages = self.storage.load_messages()
        self.assertEqual(len(messages), 3)

    def test_remove_all_messages_creates_empty_file(self) -> None:
        """
        Test removing all messages.

        Verifies the file is removed once all messages are deleted.
        """
        self.storage.add_messages(self.test_messages)
        count = self.storage.remove_messages(self.test_messages)
        self.assertEqual(count, 3)
        self.assertFalse(self.temp_path.exists())

    def test_add_after_remove(self) -> None:
        """
        Test adding messages again after removing all of them.

        Verifies storage re-creates the file and contains only the new data.
        """
        self.storage.add_messages(self.test_messages[:2])
        self.storage.remove_messages(self.test_messages[:2])
        new_message = {"id": 4, "data": "test4", "timestamp": 1614556803}
        self.storage.add_messages([new_message])
        messages = self.storage.load_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], new_message)

    def test_thread_safety(self) -> None:
        """
        Placeholder test for thread safety.

        A more robust test would involve concurrent operations with multiple
        threads.
        """
        pass


if __name__ == "__main__":
    unittest.main()
