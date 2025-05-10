"""
Sensor Reading Service for CloudIoTPy.
"""

import datetime
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from cloudiotpy.config import config
from sensor_py.sensorpy.sensor_manager import SensorManager

logger = logging.getLogger(__name__)


class SensorReadingService:
    """
    Periodically reads data from sensors using a SensorManager.

    This class manages a background thread that polls sensors at a configured
    interval. The data is then passed to an optional on_new_data callback.
    """

    def __init__(self, on_new_data: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        Initialize the SensorReadingService.

        Parameters
        ----------
        on_new_data : Optional[Callable[[Dict[str, Any]], None]], optional
            A callback function that accepts a Dict of sensor data. This is
            invoked after each reading. Typically provided by IoTManager.
        """
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sensor_manager = self._create_sensor_manager()
        self._on_new_data = on_new_data

    def start(self) -> None:
        """
        Start the background thread to read sensor data.

        Notes
        -----
        If the sensor manager is not available, this method logs an error and
        returns without starting the thread.
        """
        if self._thread and self._thread.is_alive():
            logger.warning("SensorReadingService is already running.")
            return

        if not self._sensor_manager:
            logger.error("No sensor manager available; cannot start sensor reading.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._reading_loop,
            daemon=True,
            name="SensorReadingServiceThread",
        )
        self._thread.start()
        logger.info(
            "SensorReadingService started with interval %ds.",
            config.get_read_interval(),
        )

    def stop(self) -> None:
        """
        Stop the background thread that reads sensor data.

        Notes
        -----
        If the service is not running, logs that it is already stopped.
        """
        if not self._thread or not self._thread.is_alive():
            logger.info("SensorReadingService is not running or already stopped.")
            return

        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self._thread = None

        logger.info("SensorReadingService stopped.")

    def _reading_loop(self) -> None:
        """
        Continuous loop to read sensor data until stopped.

        Steps
        -----
        1. Retrieve the read interval from config.
        2. Read data from the sensor manager.
        3. Attach a timestamp.
        4. Invoke the on_new_data callback if present.
        5. Sleep for read_interval seconds, checking for stop signals.
        """
        while not self._stop_event.is_set():
            read_interval = config.get_read_interval()
            data = {}

            try:
                data = self._sensor_manager.read_all()
            except Exception as e:
                logger.error("Error reading sensor data: %s", e)

            # Add a timestamp for clarity
            data["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"

            # If there's a callback, invoke it with the new data
            if self._on_new_data:
                try:
                    self._on_new_data(data)
                except Exception as e:
                    logger.error("Error in on_new_data callback: %s", e)

            # Sleep in 1-second increments so we can check the stop_event.
            for _ in range(read_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def _create_sensor_manager(self) -> Optional[SensorManager]:
        """
        Create a SensorManager using the current configuration.

        Returns
        -------
        Optional[SensorManager]
            The instantiated SensorManager, or None if creation fails.
        """
        try:
            sensor_config = config.get_sensor_config()
            lib_path = Path(__file__).resolve().parent.parent.parent / "sensor_py" / "drivers_c" / "build"

            co2_self_cal = sensor_config.get("co2_self_calibration", False)
            enable_stc31c = sensor_config.get("enable_stc31c", True)
            enable_shtc3 = sensor_config.get("enable_shtc3", True)
            enable_sps30 = sensor_config.get("enable_sps30", True)

            manager = SensorManager(
                lib_path=lib_path,
                co2_self_calibration=co2_self_cal,
                enable_stc31c=enable_stc31c,
                enable_shtc3=enable_shtc3,
                enable_sps30=enable_sps30,
            )
            logger.info("SensorManager initialized for SensorReadingService.")
            return manager
        except Exception as e:
            logger.error("Failed to create SensorManager: %s", e)
            return None
