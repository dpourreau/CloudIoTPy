"""
Azure IoT Hub Client Implementation.
"""

import json
import logging
import random
import threading
import time
from typing import Any, Callable, Dict, Optional

from azure.iot.device import IoTHubDeviceClient, Message, MethodRequest
from azure.iot.device.exceptions import ClientError

from cloudiotpy.common.exceptions import handle_exceptions
from cloudiotpy.iot.iot_client import IIoTClient

logger = logging.getLogger(__name__)


class AzureIoTClient(IIoTClient):
    """
    Azure IoT Hub implementation of the IIoTClient interface.

    This client uses the Azure IoT Hub Device SDK to connect to Azure IoT Hub
    and provides implementations for the methods defined in the IIoTClient
    interface. It handles telemetry, and direct method invocations.
    """

    def __init__(self, connection_string: str) -> None:
        """
        Initialize the Azure IoT Hub client.

        Parameters
        ----------
        connection_string : str
            The IoT Hub device connection string.

        Raises
        ------
        ValueError
            If no connection string is provided.
        """
        self._connection_string = connection_string

        # Internal IoTHub client and connection state
        self._client: Optional[IoTHubDeviceClient] = None
        self._connected = False

        # User-defined callbacks for commands
        self._command_callback: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None

        # Thread safety
        self._connection_lock = threading.Lock()
        self._callback_lock = threading.Lock()

        # Validate required configuration
        if not self._connection_string:
            raise ValueError("Azure IoT connection string is required.")


    def _handle_method_request(self, request: MethodRequest) -> None:
        """
        Handle direct method calls from Azure IoT Hub.

        Parameters
        ----------
        request : MethodRequest
            The direct method request from Azure IoT.
        """
        method_name = request.name
        payload = request.payload or {}

        logger.info(
            "[Azure] Received direct method: %s, payload=%s",
            method_name,
            payload,
        )
        response = None
        with self._callback_lock:
            if self._command_callback:
                try:
                    response = self._command_callback(method_name, payload)
                except Exception as exc:
                    logger.error("[Azure] Error in direct method callback: %s", exc)
                    request.send_response(status=500, payload={"error": str(exc)})
                    return

        if response is not None:
            try:
                request.send_response(status=200, payload=response)
                logger.info("[Azure] Responded to method %s", method_name)
            except Exception as exc:
                logger.error("[Azure] Error sending method response: %s", exc)
                request.send_response(status=500, payload={"error": str(exc)})
        else:
            logger.warning("No valid response for method '%s', returning 404.", method_name)
            request.send_response(status=404, payload={"error": "No handler registered"})

    @handle_exceptions(default_return_value=False)
    def connect(self) -> bool:
        """
        Perform a single connection attempt to Azure IoT Hub.

        Returns
        -------
        bool
            True if the connection was successful, False otherwise.
        """
        with self._connection_lock:
            if self._connected:
                logger.debug("[Azure] Already connected.")
                return True

            try:
                if not self._client:
                    self._client = IoTHubDeviceClient.create_from_connection_string(self._connection_string)
                self._client.connect()
                self._connected = True
                logger.info("[Azure] Connected to IoT Hub.")

                # Assign twin desired patch & method callbacks
                self._client.on_method_request_received = self._handle_method_request
            except ClientError as ce:
                logger.error("[Azure] Client error during connection: %s", ce)
                self._connected = False
                self._client = None
                raise ce
            except Exception as e:
                logger.error("[Azure] Unexpected error during connection: %s", e)
                self._connected = False
                self._client = None
                raise e
            finally:
                logger.debug("[Azure] Connection attempt finished.")

        return True

    @handle_exceptions(default_return_value=False)
    def reconnect(self, max_retries: int = 3) -> bool:
        """
        Attempt to reconnect using an exponential backoff with jitter.

        Parameters
        ----------
        max_retries : int, optional
            Maximum number of reconnection attempts, by default 3.

        Returns
        -------
        bool
            True if reconnection succeeds, False otherwise.
        """
        if self.is_connected():
            logger.debug("[Azure] Already connected.")
            return True

        base_delay = 2.0
        for attempt in range(1, max_retries + 1):
            logger.info("[Azure] Reconnect attempt %d/%d...", attempt, max_retries)
            if self.connect():
                logger.info("[Azure] Reconnected successfully on attempt %d.", attempt)
                return True

            delay = base_delay * (2 ** (attempt - 1))
            jitter = random.uniform(0, 0.3 * delay)
            time.sleep(delay + jitter)

        logger.error("[Azure] Exhausted all reconnect attempts.")
        return False

    @handle_exceptions(default_return_value=None)
    def disconnect(self) -> None:
        """
        Gracefully disconnect from Azure IoT Hub.
        """
        with self._connection_lock:
            if self._client and self._connected:
                try:
                    self._client.disconnect()
                except ClientError as ce:
                    logger.error("[Azure] Client error during disconnect: %s", ce)
                except Exception as e:
                    logger.error("[Azure] Unexpected error during disconnect: %s", e)
                finally:
                    self._connected = False
                    logger.info("[Azure] Disconnected.")

    def is_connected(self) -> bool:
        """
        Check if the client is currently connected to Azure IoT.

        Returns
        -------
        bool
            True if connected, False otherwise.
        """
        with self._connection_lock:
            return self._connected

    @handle_exceptions(default_return_value=False)
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """
        Send telemetry to Azure IoT Hub using `send_message`.

        Parameters
        ----------
        data : Dict[str, Any]
            The telemetry payload (must be JSON-serializable).

        Returns
        -------
        bool
            True if publishing was successful, False otherwise.
        """
        if not self.is_connected() or not self._client:
            logger.error("[Azure] Not connected; cannot send telemetry.")
            return False

        message = Message(json.dumps(data))
        message.content_type = "application/json"
        message.content_encoding = "utf-8"

        self._client.send_message(message)
        logger.debug("[Azure] Telemetry sent: %s", data)
        return True


    def on_command(self, callback: Callable[[str, Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Register a callback for direct method calls.

        Parameters
        ----------
        callback : Callable[[str, Dict[str, Any]], Dict[str, Any]]
            A function that takes (command_name, command_payload) and returns a
            response dictionary.
        """
        with self._callback_lock:
            self._command_callback = callback
            logger.debug("[Azure] Command callback registered.")

    def get_client_info(self) -> Dict[str, str]:
        """
        Return basic info about the Azure IoT client.

        Returns
        -------
        Dict[str, str]
            A dictionary containing 'provider', 'status', 'connection_id'.
        """
        status = "connected" if self.is_connected() else "disconnected"
        # Show only the first segment of the connection string
        cstr = self._connection_string.split(";")[0] if self._connection_string else "unknown"
        return {
            "provider": "azure",
            "status": status,
            "connection_id": cstr,
        }
