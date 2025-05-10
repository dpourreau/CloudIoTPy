# Offline Storage System

The `cloudiotpy.offline_storage` module provides a robust offline storage system that enables IoT devices to cache messages locally when connectivity to the cloud is unavailable. This document explains how the offline storage system works and how to use it.

## Overview

The offline storage system is designed with an abstract interface (`OfflineStorage`) and concrete implementations for different storage types:

- `SQLiteOfflineStorage`: Uses a SQLite database file for reliable, transactional storage
- `JSONOfflineStorage`: Uses a JSON file for simpler, human-readable storage

All implementations provide the same interface for adding, loading, and removing messages.

## Key Features

- **Consistent API**: All storage types implement the same interface
- **Configurable storage type**: Choose SQLite for reliability or JSON for simplicity
- **Error resilience**: All operations use the centralized error handling system
- **Store and forward**: Messages are stored when offline and forwarded when connectivity is restored

## Using Offline Storage

### Basic Usage

```python
from cloudiotpy.offline_storage.offline_storage_sqlite import SQLiteOfflineStorage

# Create an offline storage instance
storage = SQLiteOfflineStorage(storage_path="data/offline_messages.sqlite")

# Add messages to storage when network is unavailable
messages = [
    {"timestamp": 1614556800, "temperature": 22.5, "humidity": 45.0},
    {"timestamp": 1614556860, "temperature": 22.7, "humidity": 44.8}
]
storage.add_messages(messages)

# When network is available again, load and send messages
pending_messages = storage.load_messages(limit=10)
if send_to_cloud(pending_messages):
    # Remove successfully sent messages
    storage.remove_messages(pending_messages)
```

### Configuration

The default offline storage settings are configured in the `IoTManager`'s default configuration:

```python
# Default settings in JSON file
"offline_storage_type": "sqlite",
"offline_storage_path": "data/offline_messages.sqlite"
```

You can override these settings through the configuration system or by explicitly providing different values when creating the `IoTManager`.

## Storage Implementations

### SQLite Storage

The `SQLiteOfflineStorage` class uses a SQLite database file for storage. This provides:

- ACID transactions
- Reliability in case of power loss
- Efficient message retrieval
- Smaller memory footprint for large message volumes

Example configuration:

```python
from cloudiotpy.offline_storage.offline_storage_sqlite import SQLiteOfflineStorage

storage = SQLiteOfflineStorage(storage_path="data/offline_messages.sqlite")
```

### JSON Storage

The `JSONOfflineStorage` class uses a JSON file for storage. This provides:

- Human-readable message format
- Easy debugging and inspection
- Simpler implementation (no database dependencies)

Example configuration:

```python
from cloudiotpy.offline_storage.offline_storage_json import JSONOfflineStorage

storage = JSONOfflineStorage(storage_path="data/offline_messages.json")
```
