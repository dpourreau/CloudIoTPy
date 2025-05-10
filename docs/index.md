# CloudIoTPy Documentation

Welcome to the CloudIoTPy documentation. This guide provides detailed information about the various components of the CloudIoTPy library, a multi-cloud IoT client that offers a unified interface for cloud connectivity, sensor integration, and offline storage capabilities.

## Table of Contents

### Core Concepts
- [Error Handling System](error_handling.md) - Learn about the centralized error handling system
- [Configuration System](configuration_system.md) - Understand the multi-layered configuration approach
- [Offline Storage](offline_storage.md) - Find out how to use the store-and-forward capabilities

### Cloud‑Specific Setup
- [AWS IoT Core](using_AWS_IoT_Core.md) - Walks through setup with AWS IoT Core
- [Azure IoT Hub](using_Azure-IoT_Hub.md) - Walks through setup with Azure IoT Hub and CosmosDB

### Getting Started
- See the [main README](../README.md) for installation and basic usage
- [Quick Start Guide](#quick-start-guide) - Below on this page

### API Reference
- Core Components
  - `IoTManager` - Central orchestration class
  - `IIoTClient` - Abstract interface for cloud providers
  - `ConfigLoader` - Configuration management system
  - `OfflineStorage` - Storage interface
  - `OfflineStorageService` - Local buffer and resend manager

### Cloud Provider Integration
- AWS IoT Core
  - Utilizes AWS IoT Device SDK for AWS IoT Core connectivity
- Azure IoT Hub
  - Uses azure-iot-device for Azure IoT Hub connectivity

### Advanced Topics
- Thread Safety - All operations in CloudIoTPy are designed to be thread-safe
- Error Resilience - Built-in reconnection logic and offline caching

## Quick Start Guide

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/CloudIoTPy.git
cd CloudIoTPy

# Run the installation script
bash install.sh

# Activate the virtual environment
source venv/bin/activate
```

### Basic Usage

```python
from cloudiotpy.iot.iot_manager import IoTManager

# Create an IoT manager
manager = IoTManager()

# Connect to cloud provider (AWS by default)
manager.connect()

# Send telemetry data
manager.send_telemetry({
    "device_id": "device-001",
    "temperature": 22.5,
    "humidity": 45.0
})

# Disconnect when done
manager.disconnect()
```

## Contributing to Documentation

If you'd like to improve this documentation:

1. Fork the repository
2. Make your changes to the documentation files in the `docs/` directory
3. Submit a pull request with your changes

We appreciate your contributions to making CloudIoTPy easier to use for everyone!
