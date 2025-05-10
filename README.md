# CloudIoTPy

A multi-cloud IoT client library that provides a unified interface for connecting IoT devices to different cloud providers (AWS, Azure), with integrated sensor data collection and offline storage capabilities.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Unified Cloud Interface**: Seamlessly connect to AWS IoT Core and Azure IoT Hub with a consistent API.
- **Offline Storage**: Built-in store-and-forward capability using either SQLite or JSON storage.
- **Sensor Integration**: Direct integration with sensor_py for reading data from Sensirion sensors.

---

## Sensor Integration & Customization

CloudIoTPy ships with out-of-the-box support for Sensirion sensors via the `sensor_py` submodule, but you can:

### 1. Enable & Wire Supported Sensors
1. In `configs_json/cloud_config.json`, set the flags under `"sensor"` to `true` for any of the built-in sensors:
   ```json
   "sensor": {
     "enable_stc31c": true,
     "enable_shtc3": true,
     "enable_sps30": true,
     …
   }
   ```

2. Physically connect each enabled sensor exactly as described in **`sensor_py/docs/SENSOR_CONNECTION_GUIDE.md`** (I²C/UART pins, power rails, etc.).
3. No code changes needed—`SensorReadingService` will use the default `SensorManager` from the submodule.

### 2. Provide Your Own SensorManager

If you have other sensors or want a custom integration:

1. In the `sensor_py/` submodule, create or extend **`sensor_manager.py`** with a class implementing:

   ```python
   class SensorManager:
       def initialize(self) -> None:
           """Set up your sensors (e.g. open I²C/UART ports)."""

       def read_data(self) -> Dict[str, Any]:
           """
           Return a dict of readings, e.g.
           {"temperature": 22.5, "humidity": 55.2}.
           """
   ```
4. Enable your sensors in the JSON config. Add the flags under the `"sensor"` section of `configs_json/cloud_config.json` (e.g. `"enable_shtc3": true`, `"enable_sps30": true`, etc.).
2. Edit **`cloudiotpy/sensors_integration/sensor_reading_service.py`** to import your `SensorManager` instead of the default, and read the same "sensor" flags from the loaded config to decide which sensors to initialize and poll.
3. If your data format or rate differs, tweak **`cloudiotpy/preprocessor/telemetry_preprocessor.py`** to adjust batching, thresholding, or filtering rules.

For full details on wiring and the built-in Sensirion drivers (STC31-C, SHTC3, SPS30), check out the **SensorPy** submodule’s README and `docs/SENSOR_CONNECTION_GUIDE.md`.

## Documentation

For more detailed documentation, please see the [docs/](docs/index.md) directory, which includes:

- [Configuration System](docs/configuration_system.md) - In-depth guide to the multi-layered configuration
- [Offline Storage](docs/offline_storage.md) - Complete reference for the offline storage capabilities

---

## Project Structure

```
CloudIoTPy/
│── README.md
│── install.sh                            # Installation script
│── setup.py
│── pyproject.toml
│── main.py                               # Entry point
│
├── cloudiotpy/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── logging_setup.py
│   │   └── exceptions.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   └── cloud_config_manager.py
│   ├── iot/
│   │   ├── __init__.py
│   │   ├── iot_client.py
│   │   ├── iot_manager.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── aws_client.py
│   │       └── azure_client.py
│   ├── offline_storage/
│   │   ├── __init__.py
│   │   ├── offline_storage.py
│   │   ├── offline_storage_json.py
│   │   ├── offline_storage_sqlite.py
│   │   └── offline_storage_service.py
│   ├── sensors_integration/
│   │   ├── __init__.py
│   │   └── sensor_reading_service.py
│   └── preprocessor/
│       ├── __init__.py
│       └── telemetry_preprocessor.py
│
├── sensor_py/                             # SensorPy Git submodule for sensor integration
├── configs_json/
│   └── cloud_config_template.json        # Example config template
├── docs/
│   ├── index.md
│   ├── configuration_system.md
│   ├── error_handling.md
│   └── offline_storage.md
├── tests/
│   ├── run_tests.py
│   ├── config/
│   │   ├── test_cloud_config_manager.py
│   │   └── test_config_loader.py
│   └── offline_storage/
│       ├── test_offline_storage.py
│       ├── test_offline_storage_json.py
│       └── test_offline_storage_sqlite.py
```
---

## Installation

### Prerequisites

Make sure you have:

* **Python 3.8+**
* **Git** (for cloning the repo and its submodules)
* **GCC** & **Make** (to build the native `sensor_py` drivers)
* **Linux** system with I²C/UART support (for hardware sensors)

---

### 1. Clone the Repository

```bash
git clone --recursive git@github.com:dpourreau/CloudIoTPy.git
cd CloudIoTPy
```

---

### 2. Install with the Script

Use the bundled `install.sh` to set up a virtualenv, build drivers, and install everything you need:

* **Standard install**

  ```bash
  ./install.sh
  ```

* **With development dependencies**

  ```bash
  ./install.sh --dev
  ```

This will automatically install:

* `awsiotsdk` – AWS IoT Device SDK v2
* `azure-iot-device`, `azure-identity` – Azure IoT Hub SDKs
* `sqlite3` (built-in)
* `sensor_py` drivers

---

### 3. Post-Installation & Running

1. **Configure**

   * Copy `configs_json/cloud_config_template.json` → `configs_json/cloud_config.json`
   * Edit your credentials, endpoint, paths, etc.
   * For detailed setup, follow the [AWS IoT Core guide](docs/using_AWS_IoT_Core.md) or [Azure IoT Hub guide](docs/using_Azure-IoT_Hub.md).

2. **Run**

   ```bash
   # If the script didn’t already activate it:
   source venv/bin/activate
   
   # In the project root:
   python3 main.py
   ```

---

## Licensing

This project is licensed under the [MIT License](LICENSE).

### Included Submodules and Licensing

This repository uses Git submodules that are also open source:

- [`SensorPy`](https://github.com/dpourreau/SensorPy) — Licensed under the MIT License. See [`sensor_py/LICENSE`](https://github.com/dpourreau/SensorPy/blob/main/LICENSE).
    - Internally includes:
        - [`pm-gas-sensor-drivers`](https://github.com/dpourreau/pm-gas-sensor-drivers) — Uses source code from Sensirion AG, licensed under the BSD 3-Clause License. See [`sensor_py/pm-gas-sensor-drivers/LICENSE`](https://github.com/dpourreau/pm-gas-sensor-drivers/blob/main/LICENSE).
