# Configuration System

The CloudIoTPy library uses a sophisticated, multi-layered configuration system that combines settings from different sources with varying priorities. This document explains how the configuration system works and how to use it effectively.

## Overview

The configuration system is implemented in the `cloudiotpy.config` module and consists of the following key component:

- **ConfigLoader**: Loads configuration from a local JSON file and validates mandatory keys.

## Configuration File Example

You must supply all required settings in your configuration file located at `configs_json/cloud_config.json`. An example configuration file (located at `configs_json/cloud_config_template.json`) might look like:

```python
{
  "iot_client": {
    "provider": "aws",
    "aws": {
      "client_id": "your_device_name",
      "endpoint": "your_endpoint",
      "cert_path": "your_cert_path",
      "key_path": "your_key_path",
      "root_ca_path": "your_root_ca_path",
      "clean_session": false
    },
    "azure": {
      "connection_string": "your_connection_string"
    }
  },
  "offline_storage": {
    "type": "sqlite",
    "path": "data/offline_messages.sqlite"
  },
  "sensor": {
    "read_interval": 300,
    "max_retries": 3,
    "co2_self_calibration": true,
    "enable_stc31c": true,
    "enable_shtc3": true,
    "enable_sps30": true
  },
  "logging": {
    "logging_level": "INFO",
    "log_file": "logs/cloudiotpy.log"
  }
}
```
> **Need a step‑by‑step walkthrough?**  
> See the dedicated guides for [AWS IoT Core](using_AWS_IoT_Core.md) or [Azure IoT Hub](using_Azure-IoT_Hub.md).

## Using the Configuration System

### Basic Usage

The configuration system is automatically used when you create an `IoTManager` instance.

```python
from cloudiotpy.iot.iot_manager import IoTManager
from cloudiotpy.config import config

# Load configuration (this loads the local JSON file and merges with cloud configuration if provided)
config.load_config()

# Create an IoTManager instance – no parameters are needed since configuration is handled centrally
manager = IoTManager()
```