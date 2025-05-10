"""
IoT Client Interface for multi-cloud IoT implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class IIoTClient(ABC):
    """
    Abstract interface for IoT clients across different cloud providers.

    This interface defines the common operations that all cloud-specific
    implementations must support, including:
    - Connection management
    - Telemetry data transmission
    - Remote method invocation

    Implementations should:
    1. Apply the handle_exceptions decorator to methods interacting with
       external services.
    2. Provide clear error messages on failures.
    3. Maintain thread-safety for all operations.

    To add a new cloud provider implementation:
    1. Create a new class inheriting from IIoTClient.
    2. Implement all abstract methods with provider-specific logic.
    3. Decorate the methods interacting with external services using
       handle_exceptions.
    4. Ensure proper thread safety with locks.
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the cloud IoT service.

        Implementations should handle connection timeouts, authentication
        errors, and network issues gracefully, using handle_exceptions.

        Returns
        -------
        bool
            True if connection was successful, False otherwise.
        """
        ...

    @abstractmethod
    def reconnect(self, max_retries: int = 3) -> bool:
        """
        Attempt to reconnect to the cloud IoT service using a retry strategy.

        This method should implement exponential backoff and can optionally
        run indefinitely until a connection is made (based on user preference).

        Parameters
        ----------
        max_retries : int, optional
            Maximum number of reconnection attempts before giving up. If
            indefinite retries are desired, use a high number or manage it
            in user code.

        Returns
        -------
        bool
            True if reconnection was successful, False otherwise.
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect from the cloud IoT service.
        """
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the client is currently connected.

        Returns
        -------
        bool
            True if connected, False otherwise.
        """
        ...

    @abstractmethod
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """
        Send telemetry data to the cloud.

        Parameters
        ----------
        data : Dict[str, Any]
            A dictionary containing telemetry data to send, which must be
            JSON-serializable.

        Returns
        -------
        bool
            True if the data was sent successfully, False otherwise.
        """
        ...


    @abstractmethod
    def on_command(self, callback: Callable[[str, Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Register a callback for commands or direct methods from the cloud.

        Parameters
        ----------
        callback : Callable[[str, Dict[str, Any]], Dict[str, Any]]
            A function that accepts a command name (str) and payload (dict),
            and returns a response dict.
        """
        ...

    @abstractmethod
    def get_client_info(self) -> Dict[str, str]:
        """
        Get basic information about the client and its connection.

        Returns
        -------
        Dict[str, str]
            Information about the client, such as provider name or
            connection status.
        """
        ...
