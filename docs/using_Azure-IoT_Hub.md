# Using CloudIoTPy with Azure IoT Hub

## Introduction

CloudIoTPy is a multi-cloud IoT client library that provides a unified interface for connecting devices to cloud providers. This guide details the end-to-end process—from creating and registering an IoT device in Azure to configuring CloudIoTPy and setting up message routing to an Azure CosmosDB container.

---

## Prerequisites

- **Azure Subscription**: Permissions to create resources.
- **Azure IoT Hub**: An active IoT Hub resource.
- **Azure CosmosDB**: For NoSQL data storage.
- **Python 3.8+**
- **Git**: For cloning the repository and managing submodules.
- **Required Packages**: See installation instructions below.

---

## Create Azure IoT Hub

### Create an IoT Hub

1. Sign in to [Azure Portal](https://portal.azure.com/).
2. **Create a resource** → Search for **IoT Hub** → Click **Create**.
3. Fill in the details:
   - **Subscription**: Choose your Azure subscription.
   - **Resource Group**: Select or create one.
   - **IoT Hub Name**: Enter a unique name.
   - **Region**: Choose a region.
   - **Tier**: Select *Free* for testing (limited to 8,000 messages/day).
4. Click **Review + Create** → Click **Create**.
5. Wait for deployment to complete → Click **Go to resource**.

---

### Register a Device

1. In your IoT Hub, navigate to **Device management -> Devices**.
2. Click **+ New** (or **Add Device**).
3. Enter **Device ID** (e.g., **MyDevice**).
4. Choose authentication: Keep **Symmetric Key** selected.
5. Enable **auto-generate keys** (default).
6. Click **Save** to register the device.
7. Once the device is created, select your device and copy the **Primary connection string** for CloudIoTPy.

---

## Create an Azure CosmosDB NoSQL Account

### Create a CosmosDB Account

1. Go to [Azure Portal](https://portal.azure.com/) → Search for **CosmosDB** in the Marketplace.
2. Select **Azure Cosmos DB** → Click **Create**.
3. Choose **API Type**: Select *Azure Cosmos DB for NoSQL*.
4. Fill in details:
   - **Workload Type**: Choose a workload type.
   - **Subscription**: Choose your Azure subscription.
   - **Resource Group**: Select or create one.
   - **Account Name**: Enter a unique name.
   - **Region**: Choose a region.
   - **Capacity Mode**: *Serverless* or *Provisioned*
6. Click **Review + Create**, then **Create**.
7. Wait for deployment → Click **Go to resource**.

---

### Create a Database and Container

1. In **Azure Cosmos DB** → Open your account.
2. In the left menu, go to **Data Explorer** → Click **+ New Container**.
3. Fill in:
   - **Database ID**: Enter a unique name.
   - **Container ID**: Enter a unique name.
   - **Partition Key** (e.g., `/timestamp` or `/deviceid`)
4. Click **OK** to create.

---

## Route Telemetry Data to the CosmosDB Container

1. Open IoT Hub → Go to **Hub settings -> Message routing**.
2. Click **+ Add** to create a new route.

### Configure the Endpoint

- **Endpoint Type**: Cosmos DB  
- **Endpoint Name**: Enter a name  
- **CosmosDB Account**: Select your account  
- **Database**: Select your database  
- **Container**: Select your container  
- Click **Create + Next**

### Configure the Route

- **Name**: Enter a route name  
- **Data Source**: Device Telemetry Message  
- **Routing Query**: `true`  
- Click **Create + Skip Enrichments**

---

## Configure CloudIoTPy for Azure IoT Hub

CloudIoTPy uses a centralized configuration loaded from a local JSON file. Update your `cloud_config.json` with the following settings.

> Replace the placeholder values with your actual connection strings and credentials.

> The `cloud_config.json` file must be located at: `ProjectDire/configs_json/cloud_config.json`

```json
{
  "iot_client": {
    "provider": "azure",
    "azure": {
      "connection_string": "HostName=YourHubName.azure-devices.net;DeviceId=MyAzureDevice001;SharedAccessKey=YOUR_SHARED_ACCESS_KEY"
    }
  },
  "offline_storage": {
    "type": "sqlite",
    "path": "data/offline_messages.sqlite"
  },
  "sensor": {
    "read_interval": 300,
    "max_retries": 3,
    "enable_stc31c": true,
    "enable_shtc3": true,
    "enable_sps30": true
  },
  "logging": {
    "logging_level": "INFO",
    "log_file": "logs/cloudiotpy.log"
  },
  "config": {
    "reload_interval": 3600
  }
}
```

---

## Running CloudIoTPy

```bash
# In the project root:
python main.py
```

---

## Viewing Telemetry

1. In **Azure Cosmos DB** → Open your account.
2. In the left menu, go to **Data Explorer**.
3. Expand your container and database, then click **Items** to see all telemetry documents.

---

## Operation Summary

1. CloudIoTPy initializes the IoT Manager using the updated config.
2. The manager connects to Azure IoT Hub with the connection string.
3. Telemetry messages are sent and automatically routed to your CosmosDB container.
