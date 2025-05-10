"""
Configuration Loader for CloudIoTPy.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..common.exceptions import handle_exceptions

logger = logging.getLogger(__name__)

# Default configuration file path in the project's config directory
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs_json" / "cloud_config.json"


class ConfigLoader:
    """
    Loads configuration from a local JSON file and optionally merges it with
    cloud-fetched configuration, with cloud values taking precedence.

    This class validates that mandatory configuration keys are present and
    implements the Singleton pattern so that all parts of the project share
    the same configuration.
    """

    # Singleton instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "ConfigLoader":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                instance._config_lock = threading.RLock()
                cls._instance = instance
            return cls._instance

    def __init__(self):
        """
        Initialize the ConfigLoader with configuration loaded from JSON.

        """
        if self._initialized:
            return

        # local_config will be loaded from the JSON file
        self.local_config: Dict[str, Any] = {}
        self._observers: List[Callable[[Dict[str, Any], Dict[str, Any]], None]] = []
        self._initialized = True

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate that the configuration contains all mandatory keys.

        Parameters
        ----------
        config : Dict[str, Any]
            The configuration dictionary to validate.

        Raises
        ------
        ValueError
            If any mandatory configuration key is missing.
        """
        mandatory = {
            "iot_client": ["provider"],
            "offline_storage": ["type", "path"],
            "sensor": ["read_interval", "max_retries"],
            "logging": ["logging_level"],
        }
        missing = []
        for section, keys in mandatory.items():
            if section not in config:
                missing.append(section)
            else:
                for key in keys:
                    if key not in config[section]:
                        missing.append(f"{section}.{key}")

        # Validate provider-specific settings for iot_client
        if "iot_client" in config:
            provider = str(config["iot_client"].get("provider", "")).lower()
            if provider == "aws":
                aws_mandatory = ["endpoint", "client_id", "cert_path", "key_path"]
                aws_config = config["iot_client"].get("aws", {})
                for key in aws_mandatory:
                    if key not in aws_config or not aws_config[key]:
                        missing.append(f"iot_client.aws.{key}")
            elif provider == "azure":
                azure_mandatory = ["connection_string"]
                azure_config = config["iot_client"].get("azure", {})
                for key in azure_mandatory:
                    if key not in azure_config or not azure_config[key]:
                        missing.append(f"iot_client.azure.{key}")
            else:
                missing.append("iot_client.provider (unknown provider)")

        if missing:
            raise ValueError(f"Mandatory configuration keys missing: {', '.join(missing)}")

    @handle_exceptions(default_return_value={})
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from a local JSON file.

        Parameters
        ----------
        config_path : str, optional
            Path to the local JSON configuration file. If None, uses
            DEFAULT_CONFIG_PATH.

        Returns
        -------
        Dict[str, Any]
            The loaded configuration as a dictionary.

        Raises
        ------
        ValueError
            If the local configuration file is not found or fails to load.
        """
        if config_path is None:
            config_path = str(DEFAULT_CONFIG_PATH)

        if not os.path.exists(config_path):
            raise ValueError(f"Configuration file not found: {config_path}")

        # Load configuration from file
        try:
            with open(config_path, "r") as f:
                file_config = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")

        # Validate mandatory configuration keys
        self._validate_config(file_config)
        self.local_config = file_config

        logger.info("Successfully loaded configuration from %s", config_path)
        return self.local_config

    def get_nested_value(self, path: str, default: Any = None) -> Any:
        """
        Retrieve a nested configuration value using dot notation.

        Parameters
        ----------
        path : str
            The dot-delimited path to the configuration value, e.g.
            "sensor.read_interval".
        default : Any, optional
            The default value to return if the path is missing, by default None.

        Returns
        -------
        Any
            The value found at the specified path, or the default if not found.
        """
        with self._config_lock:
            keys = path.split(".")
            value = self.local_config
            for key in keys:
                if not isinstance(value, dict) or key not in value:
                    return default
                value = value[key]
            return value

    def get_cloud_provider(self) -> str:
        """
        Get the configured cloud provider name.

        Returns
        -------
        str
            The name of the cloud provider (e.g., "aws" or "azure").
        """
        provider = self.get_nested_value("iot_client.provider", "")
        return str(provider).lower()

    def get_offline_storage_path(self) -> Path:
        """
        Retrieve the path for offline storage.

        Returns
        -------
        Path
            The filesystem path used for offline storage.

        Raises
        ------
        ValueError
            If the mandatory "offline_storage.path" key is missing.
        """
        path_str = self.get_nested_value("offline_storage.path")
        if path_str:
            return Path(path_str)
        raise ValueError("Mandatory offline_storage.path is missing")

    def get_offline_storage_type(self) -> str:
        """
        Retrieve the offline storage type.

        Returns
        -------
        str
            The storage type (e.g., "sqlite", "json").
        """
        storage_type = self.get_nested_value("offline_storage.type", "sqlite")
        return str(storage_type).lower()

    def get_log_level(self) -> str:
        """
        Retrieve the configured logging level.

        Returns
        -------
        str
            The log level (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
        """
        log_level = self.get_nested_value("logging.logging_level", "INFO")
        return str(log_level).upper()

    def get_log_file(self) -> Optional[str]:
        """
        Retrieve the configured log file path.

        Returns
        -------
        str or None
            The log file path if specified, otherwise None.
        """
        return self.get_nested_value("logging.log_file", None)

    def get_read_interval(self) -> int:
        """
        Retrieve the data acquisition interval in seconds.

        Returns
        -------
        int
            The data acquisition interval in seconds.
        """
        interval = self.get_nested_value("sensor.read_interval", 300)
        return max(5, int(interval))  # Ensure at least 5 seconds

    def get_max_retries(self) -> int:
        """
        Retrieve the maximum number of sensor reconnection retries.

        Returns
        -------
        int
            The maximum number of sensor retries.
        """
        retries = self.get_nested_value("sensor.max_retries", 0)
        return max(0, int(retries))

    def get_sensor_config(self) -> Dict[str, Any]:
        """
        Retrieve the complete sensor configuration.

        Returns
        -------
        Dict[str, Any]
            The dictionary containing sensor-related settings.
        """
        return self.get_nested_value("sensor", {})

    def get_provider_config(self, provider: str = None) -> Dict[str, Any]:
        """
        Retrieve provider-specific configuration.

        Parameters
        ----------
        provider : str, optional
            The cloud provider name. If None, uses get_cloud_provider().

        Returns
        -------
        Dict[str, Any]
            The dictionary containing provider-specific settings.
        """
        if provider is None:
            provider = self.get_cloud_provider()
        return self.get_nested_value(f"iot_client.{provider}", {})