# Using CloudIoTPy with AWS IoT Core

## Introduction

CloudIoTPy is a Python-based library for connecting IoT devices to various cloud providers (AWS, Azure, etc.) through a consistent API.

When configured for AWS IoT Core, it:

- Connects via MQTT over TLS.
- Lets you publish telemetry to a custom topic (e.g., devices/<your_client_id>/telemetry ).
- Supports receiving commands from the cloud on a corresponding commands topic.
- Stores messages offline when your device is disconnected and flushes them upon reconnect.

This document walks through:

1. Creating an AWS IoT “Thing” using the AWS IoT wizard.
3. Setting up the cloud_config.json in CloudIoTPy with your certificate paths, endpoint, etc.
4. Running the project, verifying that telemetry is sent, and viewing messages in the AWS IoT console.

## Prerequisites

1. AWS Account with IoT Core access.  
2. Python 3.8+ on your device.  
3. CloudIoTPy source code (cloned or downloaded).  

## Creating and Configuring the AWS IoT Device

This section walks you through setting up your device in AWS IoT Core using the AWS Console wizard. We'll use this to create a "Thing" (a digital representation of your physical device), generate the required certificates, test the connection, apply a custom policy, and create a shadow for state management.

### Step 1: Navigate to AWS IoT Core

In the [AWS Management Console](https://console.aws.amazon.com/), go to IoT Core.  
From the left-hand menu, click **Connect → Connect one device**.  
Prepare your device and click **Next**.

### Step 2: Define Thing Properties

Choose **Create a new thing** and enter a name for your device under Thing name (e.g., `MyThing`).  
Optionally, configure thing type, searchable attributes, groups, or billing groups.
Click **Next**.

### Step 3: Choose platform and SDK

Select **Linux / macOS** or **Windows** depending on your OS.
Select **Python** as **AWS IoT Device SDK**.
Click **Next**.

### Step 4: Download the connection kit

1. Click **Download connection kit**. AWS will generate a ZIP archive (e.g. `connect_device_package.zip`) containing:
   - Your device certificate (`MyThing.cert.pem`)
   - Your private key (`MyThing.private.key`)
   - A shell script (`start.sh`) to test the connection and to download the Amazon Root CA certificate (`root-CA.crt`)
   - A default IoT policy file (JSON)

2. Extract the ZIP on your device and **store these files securely**.

3. Copy the following into your project’s AWS config folder:

```
ProjectDire/config/aws/
├── MyThing.cert.pem
├── MyThing.private.key
└── root-CA.crt
```

### Step 5: Run connection kit

On your device, open a terminal in `connect_device_package` and make the script executable:

```bash
chmod +x start.sh
./start.sh
```

This tests your device's connectivity to AWS IoT Core and downloads the root CA certificate if not present.
> Once you’ve verified that it connects cleanly, hit `Control + C` to terminate the script.

### Step 6: Update the Policy for Full Functionality

In the AWS Console, navigate to **IoT Core → Manage → Security → Policies**, select your policy (e.g., `MyThing-Policy`), and edit it in **JSON** mode using the template below.

#### Policy Template

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": "arn:aws:iot:eu-west-3:1234567890:client/MyThing"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:eu-west-3:1234567890:topicfilter/devices/MyThing/commands/*",
        "arn:aws:iot:eu-west-3:1234567890:topic/devices/MyThing/commands/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "iot:Publish",
      "Resource": [
        "arn:aws:iot:eu-west-3:1234567890:topic/devices/MyThing/telemetry",
        "arn:aws:iot:eu-west-3:1234567890:topic/devices/MyThing/commands/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "iot:Receive",
      "Resource": "arn:aws:iot:eu-west-3:1234567890:topic/devices/MyThing/telemetry"
    }
  ]
}
```

#### Replace the following placeholders

- `eu-west-3` → your **AWS region** (e.g., `us-east-1`, `eu-west-1`, etc.)
- `1234567890` → your **AWS account ID**
- `MyThing` → your **Thing name**

#### How to find them

- **Region**: Displayed in the top-right corner of the AWS Console (e.g., `Paris (eu-west-3)`).
- **Account ID**: Click your account name (top-right) → **My Account** → copy your **12-digit AWS account ID**.
- **Thing Name**: Go to **IoT Core → Manage → Things** and use the name of your registered device.

>**Make sure to save this as a new policy version and activate it** by checking the "Set the edited version as the active version for this policy" option before saving.

## Configuring CloudIoTPy via `cloud_config.json`

- Go to **IoT Core** in the AWS Console.
- In the left-hand menu, click **Connect → Domain configurations**.
- Under **Domain configurations**, find the **Domain name** (e.g., `XXXXXXXXXXXXXXXX.amazonaws.com`).
- Copy this value — it is your device’s **endpoint** for connecting via MQTT/TLS.

> The `cloud_config.json` file must be located at: `ProjectDire/configs_json/cloud_config.json`

An example configuration:

```json
{
  "iot_client": {
    "provider": "aws",
    "aws": {
      "client_id": "MyThing",
      "endpoint": "abcdefghklmn-ats.iot.eu-west-3.amazonaws.com",
      "cert_path": "config/aws/MyThing.cert.pem",
      "key_path": "config/aws/MyThing.private.key",
      "root_ca_path": "config/aws/root-CA.crt",
      "clean_session": false
    }
  },
  "offline_storage": {
    "type": "sqlite",
    "path": "data/offline_messages.sqlite"
  },
  "sensor": {
    "read_interval": 300,
    "max_retries": 3
  },
  "logging": {
    "logging_level": "DEBUG",
    "log_file": "logs/cloudiotpy.log"
  }
}
```

## Running CloudIoTPy

```bash
# In the project root:
python3 main.py
```

### What Happens

- The script loads `cloud_config.json`
- AWSIoTClient connects and subscribes
- Telemetry is published regularly to `devices/MyThing/telemetry`
- Messages show in AWS IoT console

## Viewing Telemetry

Use the **MQTT test client** in AWS Console:  
Subscribe to `devices/MyThing/telemetry` and watch for incoming data.

You're all set with CloudIoTPy and AWS IoT Core!
