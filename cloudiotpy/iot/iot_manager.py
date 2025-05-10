"""
IoT Manager - Main orchestration component for CloudIoTPy.
"""

import logging
import os
import threading
from typing import Any, Dict

from cloudiotpy.common.exceptions import handle_exceptions
from cloudiotpy.config import config

# Import the IoT clients (implemented in providers/)
from cloudiotpy.iot.providers.aws_client import AWSIoTClient
from cloudiotpy.iot.providers.azure_client import AzureIoTClient
from cloudiotpy.offline_storage.offline_storage_service import OfflineStorageService
from cloudiotpy.preprocessor.telemetry_preprocessor import TelemetryPreprocessor

# Import additional services
from cloudiotpy.sensors_integration.sensor_reading_service import SensorReadingService

logger = logging.getLogger(__name__)


class IoTManager:
    """
    High-level manager that orchestrates IoT operations.

    The IoTManager serves as the main entry point for applications using
    CloudIoTPy. It provides a unified interface for IoT operations regardless
    of the underlying cloud provider or storage mechanism.

    Responsibilities
    ---------------
    1. Creates an IoT client based on configuration.
    2. Creates an OfflineStorageService for store-and-forward.
    3. Starts a SensorReadingService for periodic sensor data.
    4. Integrates with a TelemetryPreprocessor to filter minor changes.
    5. Provides thread-safe connect, disconnect, telemetry, and flush methods.
    """

    def __init__(self) -> None:
        """
        Initialize IoTManager with the appropriate IoT client, offline storage
        service, sensor reading service, and telemetry preprocessor.
        """
        # For concurrency - used to protect shared resources
        self._lock = threading.Lock()

        # Create the appropriate IoT client
        self._client = self._create_iot_client()

        # Create offline storage and attach the client
        self._offline_service = OfflineStorageService()
        self._offline_service.attach_client(self._client)

        # Create the telemetry preprocessor
        self._telemetry_preprocessor = TelemetryPreprocessor()

        # Create the sensor reading service and pass a callback for new data
        self._sensor_service = SensorReadingService(on_new_data=self._handle_sensor_data)

        logger.info(
            "IoTManager initialized with provider: %s",
            config.get_cloud_provider(),
        )

    def connect(self) -> bool:
        """
        Attempt a single connection to the IoT service. If successful, flush any
        offline data.

        Returns
        -------
        bool
            True if successfully connected, False otherwise.
        """
        success = self._client.connect()
        if success:
            logger.info(
                "Connected to %s successfully.",
                config.get_cloud_provider(),
            )
            # Try to flush offline queue if we have any
            self._offline_service.flush_data()
        else:
            logger.error(
                "Connection to %s failed.",
                config.get_cloud_provider(),
            )
        return success

    def reconnect(self) -> bool:
        """
        Attempt to reconnect, using max retries from configuration. If successful,
        flush any offline data.

        Returns
        -------
        bool
            True if successfully reconnected, False otherwise.
        """
        
        max_retries = config.get_max_retries()
        success = self._client.reconnect(max_retries)
        if success:
            logger.info(
                "Reconnected to %s.",
                config.get_cloud_provider(),
            )
            self._offline_service.flush_data()
        else:
            logger.error(
                "Reconnection attempts exhausted for %s.",
                config.get_cloud_provider(),
            )
        return success

    def disconnect(self) -> None:
        """
        Gracefully disconnect from the IoT service.
        """
        self._client.disconnect()
        logger.info("Disconnected from %s.", config.get_cloud_provider())

    def is_connected(self) -> bool:
        """
        Check if the manager is currently connected to the IoT service.

        Returns
        -------
        bool
            True if connected, False otherwise.
        """
        return self._client.is_connected()

    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """
        Immediately attempt to send telemetry to the cloud or store offline if
        not connected.

        Parameters
        ----------
        data : Dict[str, Any]
            The telemetry payload, which must be JSON-serializable.

        Returns
        -------
        bool
            True if sent successfully, False otherwise.
        """
        if not self.is_connected():
            logger.warning("Not connected, storing offline.")
            self._offline_service.add_message(data)
            return False

        sent = self._client.send_telemetry(data)
        if not sent:
            logger.warning("Send failed, storing offline.")
            self._offline_service.add_message(data)
            return False

        return True

    def start(self) -> None:
        """
        Connect to the IoT service and start the sensor reading service.
        Flushes any offline data if connected.
        """
        if not self.connect():
            logger.warning("Initial connection failed, trying reconnect.")
            self.reconnect()

        self._sensor_service.start()

    def shutdown(self) -> None:
        """
        Stop sensor reading, and disconnect.
        """
        try:
            self._sensor_service.stop()
        except Exception as e:
            logger.error("Error stopping sensor reading: %s", e)

        try:
            self.disconnect()
        except Exception as e:
            logger.error("Error during shutdown disconnect: %s", e)

    @handle_exceptions(default_return_value=None, log_exception=True)
    def _create_iot_client(self):
        """
        Create an AWS or Azure IoT client based on the current configuration.

        Returns
        -------
        AWSIoTClient or AzureIoTClient
            A cloud-specific IoT client instance.

        Raises
        ------
        ValueError
            If an unknown provider is specified.
        """
        provider = config.get_cloud_provider()
        provider_conf = config.get_provider_config(provider)

        if provider == "aws":
            # Ensure paths are absolute
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
            cert_path = os.path.join(project_root, provider_conf.get("cert_path", ""))
            key_path = os.path.join(project_root, provider_conf.get("key_path", ""))
            root_ca_path = os.path.join(project_root, provider_conf.get("root_ca_path", ""))
            return AWSIoTClient(
                endpoint=provider_conf.get("endpoint"),
                client_id=provider_conf.get("client_id"),
                cert_path=cert_path,
                key_path=key_path,
                root_ca_path=root_ca_path,
                clean_session=provider_conf.get("clean_session", True),
            )
        elif provider == "azure":
            return AzureIoTClient(connection_string=provider_conf.get("connection_string"))
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def on_command(self, callback) -> None:
        """
        Register a callback for commands/direct methods on the underlying IoT
        client.

        Parameters
        ----------
        callback : Callable
            A function to handle incoming command requests.
        """
        self._client.on_command(callback)

    def get_client_info(self) -> Dict[str, str]:
        """
        Retrieve info about the underlying IoT client.

        Returns
        -------
        Dict[str, str]
            A dictionary containing client provider and connection details.
        """
        return self._client.get_client_info()

    def _handle_sensor_data(self, data: Dict[str, Any]) -> None:
        """
        Called by SensorReadingService whenever new sensor data is available.
        Uses TelemetryPreprocessor to decide if the data should be sent.

        Parameters
        ----------
        data : Dict[str, Any]
            The incoming sensor reading.
        """
        # Check if we should send this new data
        if self._telemetry_preprocessor.should_send(data):
            data = self._telemetry_preprocessor.preprocess_data(data)
            self.send_telemetry(data)
        else:
            logger.debug("TelemetryPreprocessor: data not significantly changed, skipping.")
