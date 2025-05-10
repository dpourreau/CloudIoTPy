"""
Module for setting up global logging configuration for CloudIoTPy.
"""

import logging
import logging.config
from pathlib import Path

from cloudiotpy.config import config  # our singleton config instance


def setup_global_logging():
    """
    Configure global logging settings for the entire application using the
    singleton config instance.

    Notes
    -----
    1. Retrieves logging parameters such as log level and log file path from
       the configuration.
    2. Constructs a logging configuration dictionary supporting console
       logging.
    3. Adds a file logging handler if a log file is specified.
    4. Applies the configuration via logging.config.dictConfig() so that all
       module loggers (created with logging.getLogger(__name__)) inherit
       these settings.

    The log level is expected to be defined in the configuration (e.g., "INFO",
    "DEBUG", etc.), and the log file is optional.

    Returns
    -------
    None
        No return value.
    """
    # Retrieve log level and log file path from the configuration
    log_level = config.get_log_level()  # e.g., "INFO", "DEBUG", etc.
    log_file = config.get_log_file()

    # Ensure the directory for the log file exists if a log file is specified
    if log_file:
        log_path = Path(log_file)
        if not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a configuration dictionary for logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
        "handlers": {
            # Console handler configuration
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
    }

    # If a log file is specified, add a file handler to the configuration
    if log_file:
        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": log_file,
            "level": log_level,
        }
        # Append the file handler to the list of root handlers
        logging_config["root"]["handlers"].append("file")

    # Apply the logging configuration to the logging system
    logging.config.dictConfig(logging_config)
