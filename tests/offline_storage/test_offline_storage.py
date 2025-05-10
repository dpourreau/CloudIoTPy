"""
Unit tests for the OfflineStorage abstract base class.
"""

import unittest
from typing import Any, Dict, List

from cloudiotpy.offline_storage import OfflineStorage


class MockOfflineStorage(OfflineStorage):
    """
    Mock implementation of OfflineStorage for testing.

    This class tracks how many times each method is called and stores messages
    in memory.
    """

    def __init__(self) -> None:
        """
        Initialize the MockOfflineStorage.
        """
        self.messages = []
        self.add_count = 0
        self.load_count = 0
        self.remove_count = 0

    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Add (append) new messages to storage.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            Messages to store.
        """
        self.add_count += 1
        self.messages.extend(messages)

    def load_messages(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Load up to `limit` messages from storage.

        Parameters
        ----------
        limit : int, optional
            The maximum number of messages to load. If 0 or negative,
            return all.

        Returns
        -------
        List[Dict[str, Any]]
            A list of stored messages, in FIFO order.
        """
        self.load_count += 1
        if limit <= 0:
            return self.messages.copy()
        return self.messages[:limit]

    def remove_messages(self, messages: List[Dict[str, Any]]) -> int:
        """
        Remove occurrences of specified messages.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            The messages to remove.

        Returns
        -------
        int
            The number of messages actually removed.
        """
        self.remove_count += 1
        removed = 0
        for msg in messages:
            if msg in self.messages:
                self.messages.remove(msg)
                removed += 1
        return removed


class IncompleteStorage(OfflineStorage):
    """
    Incomplete implementation missing required methods.

    Used to confirm that OfflineStorage cannot be instantiated without all
    abstract methods.
    """

    pass


class TestOfflineStorage(unittest.TestCase):
    """
    Test cases for the OfflineStorage abstract base class.

    Verifies that abstract methods cannot be omitted and that an appropriate
    implementation satisfies them.
    """

    def test_abstract_class_instantiation(self) -> None:
        """
        Ensure OfflineStorage cannot be instantiated directly.
        """
        with self.assertRaises(TypeError):
            OfflineStorage()

    def test_incomplete_implementation(self) -> None:
        """
        Check that incomplete implementations raise TypeError.
        """
        with self.assertRaises(TypeError):
            IncompleteStorage()

    def test_complete_implementation(self) -> None:
        """
        Verify that complete implementations can be instantiated.
        """
        storage = MockOfflineStorage()
        self.assertIsInstance(storage, OfflineStorage)

    def test_interface_usage(self) -> None:
        """
        Test using a MockOfflineStorage instance with the OfflineStorage API.
        """
        storage = MockOfflineStorage()
        test_messages = [{"id": 1, "data": "test"}]
        storage.add_messages(test_messages)
        self.assertEqual(storage.add_count, 1)
        loaded = storage.load_messages()
        self.assertEqual(storage.load_count, 1)
        self.assertEqual(loaded, test_messages)
        limited = storage.load_messages(1)
        self.assertEqual(storage.load_count, 2)
        self.assertEqual(limited, test_messages)
        removed = storage.remove_messages(test_messages)
        self.assertEqual(storage.remove_count, 1)
        self.assertEqual(removed, 1)
        self.assertEqual(storage.messages, [])


if __name__ == "__main__":
    unittest.main()
