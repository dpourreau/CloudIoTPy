"""
AWS IoT Core Client Implementation.
"""

import concurrent.futures
import datetime
import json
import logging
import os
import random
import threading
import time
from typing import Any, Callable, Dict, Optional

from awscrt import mqtt as awscrt_mqtt
from awsiot import mqtt_connection_builder

from cloudiotpy.common.exceptions import handle_exceptions
from cloudiotpy.iot.iot_client import IIoTClient

logger = logging.getLogger(__name__)

SUBSCRIBE_TIMEOUT_SECS = 5
PUBLISH_TIMEOUT_SECS = 5

class AWSIoTClient(IIoTClient):
    """
    AWS IoT Core implementation of the IIoTClient interface.

    This client leverages the AWS IoT Device SDK v2 to connect to AWS IoT Core
    and implements all required IIoTClient methods.
    """

    def __init__(
        self,
        endpoint: str,
        client_id: str,
        cert_path: str,
        key_path: str,
        root_ca_path: Optional[str] = None,
        clean_session: bool = False,
    ) -> None:
        """
        Initialize the AWS IoT Core client.

        Parameters
        ----------
        endpoint : str
            The AWS IoT Core endpoint.
        client_id : str
            The client ID to use when connecting.
        cert_path : str
            Path to the client certificate.
        key_path : str
            Path to the client private key.
        root_ca_path : str, optional
            Path to the root CA certificate, by default None.
        clean_session : bool, optional
            Whether to use a clean MQTT session each time, by default False.

        Raises
        ------
        FileNotFoundError
            If any of the provided certificate/key/CA paths cannot be found.
        ValueError
            If the basic AWS IoT Core configuration is missing.
        """
        self._endpoint = endpoint
        self._client_id = client_id
        self._cert_path = cert_path
        self._key_path = key_path
        self._root_ca_path = root_ca_path
        self._clean_session = clean_session

        if not os.path.exists(self._cert_path):
            raise FileNotFoundError(f"AWS Certificate file not found: {self._cert_path}")
        if not os.path.exists(self._key_path):
            raise FileNotFoundError(f"AWS Private Key file not found: {self._key_path}")
        if self._root_ca_path and not os.path.exists(self._root_ca_path):
            raise FileNotFoundError(f"AWS Root CA file not found: {self._root_ca_path}")

        # Initialize connection state
        self._connected = False
        self._mqtt_connection = None

        # User-provided callbacks
        self._command_callback: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None

        self._connection_lock = threading.Lock()
        self._callback_lock = threading.Lock()

        if not all(
            [
                self._endpoint,
                self._client_id,
                self._cert_path,
                self._key_path,
            ]
        ):
            raise ValueError("AWS IoT Core configuration incomplete. " "Provide endpoint, client_id, cert_path, and key_path.")

        # Topics for telemetry, commands, etc.
        self._telemetry_topic = f"devices/{self._client_id}/telemetry"
        self._command_topic = f"devices/{self._client_id}/commands/#"
        self._command_response_topic_prefix = f"devices/{self._client_id}/commands/response"

    @handle_exceptions(default_return_value=False)
    def connect(self) -> bool:
        """
        Perform a single attempt to connect to AWS IoT Core.

        Subscribes to necessary command topics after a successful connection.

        Returns
        -------
        bool
            True if the connection succeeded, False otherwise.
        """
        with self._connection_lock:
            if self._connected:
                logger.debug("Already connected to AWS IoT Core.")
                return True

            # Build the MQTT connection via mutual TLS
            self._mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self._endpoint,
                port=8883,
                cert_filepath=self._cert_path,
                pri_key_filepath=self._key_path,
                client_id=self._client_id,
                clean_session=self._clean_session,
                keep_alive_secs=60,
                ca_filepath=self._root_ca_path,
            )

            # Connect and wait until it's done
            connect_future = self._mqtt_connection.connect()
            try:
                connect_future.result(timeout=SUBSCRIBE_TIMEOUT_SECS)
            except concurrent.futures.TimeoutError:
                logger.error("Timeout while waiting for MQTT connect() ACK from AWS IoT Core.")
                return False
            except Exception as e:
                logger.error(f"Error connecting to AWS IoT Core: {e}")
                return False

            self._connected = True
            logger.info(f"Connected to AWS IoT Core at {self._endpoint}.")

            # Subscribe to commands
            try:
                subscribe_future, _ = self._mqtt_connection.subscribe(
                    topic=self._command_topic,
                    qos=awscrt_mqtt.QoS.AT_LEAST_ONCE,
                    callback=self._on_command_message,
                )
                subscribe_future.result(timeout=SUBSCRIBE_TIMEOUT_SECS)
            except Exception as sub_err:
                logger.error(f"Error subscribing to command topic: {sub_err}")

        return True

    @handle_exceptions(default_return_value=False)
    def reconnect(self, max_retries: int = 3) -> bool:
        """
        Attempt to reconnect with exponential backoff and jitter.

        Parameters
        ----------
        max_retries : int, optional
            Maximum number of reconnection attempts, by default 3.

        Returns
        -------
        bool
            True if reconnection was successful, False otherwise.
        """
        if self._connected:
            logger.debug("Already connected to AWS IoT Core.")
            return True

        base_delay = 2.0
        for attempt in range(1, max_retries + 1):
            logger.info(f"[AWS] Reconnection attempt {attempt}/{max_retries}...")
            if self.connect():
                logger.info(f"[AWS] Reconnected successfully on attempt {attempt}.")
                return True
            delay = base_delay * (2 ** (attempt - 1))
            jitter = random.uniform(0, 0.3 * delay)
            time.sleep(delay + jitter)

        logger.error("[AWS] All reconnection attempts failed.")
        return False

    @handle_exceptions(default_return_value=None)
    def disconnect(self) -> None:
        """
        Disconnect gracefully from AWS IoT Core.
        """
        with self._connection_lock:
            if self._mqtt_connection and self._connected:
                try:
                    disconnect_future = self._mqtt_connection.disconnect()
                    # Add a reasonable timeout to avoid blocking forever
                    disconnect_future.result(timeout=5)
                except concurrent.futures.TimeoutError:
                    logger.error("Timeout while waiting for MQTT disconnect() ACK from AWS IoT Core.")
                except Exception as exc:
                    logger.error(f"Error disconnecting from AWS IoT Core: {exc}")
                finally:
                    self._connected = False
                    logger.info("Disconnected from AWS IoT Core.")

    def is_connected(self) -> bool:
        """
        Check if the client is currently connected to AWS IoT Core.

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
        Publish a telemetry message to AWS IoT Core on self._telemetry_topic.

        Parameters
        ----------
        data : Dict[str, Any]
            Telemetry payload (must be JSON-serializable).

        Returns
        -------
        bool
            True if publish was successful, False otherwise.
        """
        if not self.is_connected() or not self._mqtt_connection:
            logger.error("Cannot send telemetry; not connected to AWS IoT Core.")
            return False

        payload = json.dumps(data)
        publish_future, _ = self._mqtt_connection.publish(
            topic=self._telemetry_topic,
            payload=payload,
            qos=awscrt_mqtt.QoS.AT_LEAST_ONCE,
        )
        try:
            # Wait for puback
            publish_future.result(timeout=PUBLISH_TIMEOUT_SECS)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout while publishing telemetry data.")
            return False
        except Exception as e:
            logger.error(f"Error publishing telemetry: {e}")
            return False

        logger.debug(f"Telemetry published: {data}")
        return True

    def on_command(self, callback: Callable[[str, Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Register a callback for inbound commands from AWS IoT Core.

        Parameters
        ----------
        callback : Callable[[str, Dict[str, Any]], Dict[str, Any]]
            A function that takes (command_name, command_payload) and returns a
            response payload dict.
        """
        with self._callback_lock:
            self._command_callback = callback
            logger.debug("AWS command callback registered.")

    def get_client_info(self) -> Dict[str, str]:
        """
        Return basic info about the AWS IoT client.

        Returns
        -------
        Dict[str, str]
            A dictionary with 'provider', 'status', 'endpoint', 'client_id'.
        """
        status = "connected" if self.is_connected() else "disconnected"
        return {
            "provider": "aws",
            "status": status,
            "endpoint": str(self._endpoint),
            "client_id": str(self._client_id),
        }

    def _on_command_message(self, topic, payload, **kwargs) -> None:
        """
        Callback for incoming command messages on
        'devices/{client_id}/commands/#'.

        Parameters
        ----------
        topic : str
            The MQTT topic where the command was received.
        payload : bytes
            The raw MQTT message payload.
        """
        try:
            payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else payload
            payload_dict = json.loads(payload_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON payload for command: {payload}")
            return

        logger.debug(f"Received command on topic {topic}: {payload_dict}")
        if not self._command_callback:
            logger.debug("No command callback registered. Ignoring command.")
            return

        command_name = payload_dict.get("command", "")
        command_payload = payload_dict.get("payload", {})
        if not command_name:
            logger.warning("Command message did not contain a 'command' field.")
            return

        with self._callback_lock:
            try:
                response = self._command_callback(command_name, command_payload)
            except Exception as exc:
                logger.error(f"Error in command callback: {exc}")
                response = None

        if response is not None:
            resp_topic = f"{self._command_response_topic_prefix}/{command_name}"
            resp_msg = {
                "response": response,
                "command": command_name,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            }
            try:
                pub_future, _ = self._mqtt_connection.publish(
                    topic=resp_topic,
                    payload=json.dumps(resp_msg),
                    qos=awscrt_mqtt.QoS.AT_LEAST_ONCE,
                )
                pub_future.result(timeout=PUBLISH_TIMEOUT_SECS)
                logger.debug(f"Sent command response to {resp_topic}: {resp_msg}")
            except concurrent.futures.TimeoutError:
                logger.error(f"Timeout while publishing command response on topic {resp_topic}")
            except Exception as e:
                logger.error(f"Publish error on topic {resp_topic}: {e}")
