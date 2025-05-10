#!/usr/bin/env python3
"""
CloudIoTPy Main Script.
"""


import logging
import os
import signal
import sys
from pathlib import Path

# Import CloudIoTPy modules
from cloudiotpy import IoTManager, config, setup_global_logging


def main():
    """
    Main entry point for the Cloud IoT Project.

    Notes
    -----
    1. Sets up global logging for the application (applied to the project and
       its submodules).
    2. Uses the singleton config instance for configuration management.
    3. Initializes the IoTManager, which connects to the configured cloud
       provider.
    4. Sets up signal handlers for graceful termination.
    5. Starts the IoTManager's data collection and processing.

    The IoTManager handles:
      - Cloud provider connections (AWS IoT Core or Azure IoT Hub)
      - Sensor data acquisition through sensor_py integration
      - Offline storage when cloud connectivity is unavailable
      - Automatic reconnection and message forwarding

    Default configuration values include:
      - Cloud provider: AWS
      - Offline storage: SQLite (data/offline_messages.sqlite)
      - Data acquisition interval: 300 seconds (5 minutes)
      - Maximum reconnection retries: 3
    """
    # Set up global logging for the entire application
    setup_global_logging()

    try:
        # The singleton config instance is already initialized when imported,
        # with auto-reload enabled by default.

        # Use singleton config's utility methods to get specific settings.
        logging.info(
            "Using configuration with provider: %s and log level: %s", 
            config.get_cloud_provider(),
            config.get_log_level()
        )
        logging.info(
            "Data acquisition interval: %ss, max retries: %s",
            config.get_read_interval(),
            config.get_max_retries()
        )

        # Initialize IoTManager - it will create the SensorManager internally.
        iot_manager = IoTManager()

        def graceful_shutdown(signum, frame):
            """
            Signal handler for SIGINT and SIGTERM.

            Ensures a clean shutdown of the IoTManager before exiting.
            """
            logging.info("Graceful shutdown initiated.")
            iot_manager.shutdown()  # Stop sensor readings and cloud connections
            sys.exit(0)

        # Register signal handlers for graceful shutdown.
        signal.signal(signal.SIGINT, graceful_shutdown)
        signal.signal(signal.SIGTERM, graceful_shutdown)

        logging.info("Starting IoT Manager...")
        iot_manager.start()

        # Keep the main thread alive, waiting for signals.
        while True:
            signal.pause()

    except KeyboardInterrupt:
        # Catch Ctrl+C events not handled by the signal handler.
        logging.info("Interrupted by user.")
        if 'iot_manager' in locals():
            iot_manager.shutdown()
    except Exception as e:
        # Log any unexpected exceptions with full stack trace.
        logging.error("Unhandled error in main: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()