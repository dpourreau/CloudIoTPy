"""
Offline Storage Base Class for CloudIoTPy.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class OfflineStorage(ABC):
    """
    Abstract base class for an offline store of unsent IoT messages.

    Subclasses must implement the following:
    - add_messages(messages)
    - load_messages(limit)
    - remove_messages(messages)

    Typical Usage
    -------------
    1. Call add_messages() whenever new messages cannot be sent immediately.
    2. Use load_messages() (with a limit) to retrieve a batch of messages for
       sending.
    3. Remove messages via remove_messages() after they are successfully
       delivered.
    """

    @abstractmethod
    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Add (append) new messages to storage without removing existing ones.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            The new messages to store.
        """
        pass

    @abstractmethod
    def load_messages(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Load and return up to `limit` oldest messages from storage.

        Parameters
        ----------
        limit : int, optional
            The maximum number of messages to return. If 0 or negative,
            all stored messages are returned.

        Returns
        -------
        List[Dict[str, Any]]
            A list of message dicts, in the order they were stored
            (oldest first).
        """
        pass

    @abstractmethod
    def remove_messages(self, messages: List[Dict[str, Any]]) -> int:
        """
        Remove one or multiple messages from storage.

        Parameters
        ----------
        messages : List[Dict[str, Any]]
            The messages to remove (exact matches).

        Returns
        -------
        int
            The number of messages actually removed.
        """
        pass
