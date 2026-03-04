# GCM BLE Server

[![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Linux](https://img.shields.io/badge/OS-Linux-red?logo=linux)](https://www.linux.org/)
[![BlueZ 5.50+](https://img.shields.io/badge/BlueZ-5.50%2B-blue)](http://www.bluez.org/)
[![Status: Active](https://img.shields.io/badge/Status-Active-success)](https://github.com)
[![Research: Security](https://img.shields.io/badge/Research-Security-orange)](https://github.com)

A Bluetooth Low Energy (BLE) GATT server that emulates a Continuous Glucose Monitoring (CGM) device. This project demonstrates real-time medical device communication over BLE using the standard GATT protocol.

## Table of Contents

- [Overview](#overview)
- [Project Objectives](#project-objectives)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Data Format](#data-format)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [License](#license)

## Overview

Without access to expensive real CGM hardware (~$100-500), we reverse-engineered the official Bluetooth Glucose Service specification and built a fully functional GATT server. The server broadcasts glucose readings exactly as real CGM devices do, enabling:

- **Live real-time glucose monitoring** via nRF Connect or any BLE app
- **Protocol understanding** without a proprietary black-box device
- **Security research** and vulnerability analysis
- **Mobile app development** without expensive hardware

## Project Objectives

**Current (Phase 1):**
- ✅ Full GATT server emulating real CGM devices
- ✅ Real-time glucose data transmission (5-second intervals)
- ✅ Bluetooth Health Device Profile (HDP) compliance
- ✅ Standard SIG Glucose Service specification

**Upcoming (Phase 2-5):**
- 🔄 **Data Interception**: Capture and analyze BLE glucose packets
- 🔄 **Replay Attacks**: Test vulnerability to packet replay
- 🔄 **Security Analysis**: Identify weaknesses in CGM protocols
- 🔄 **Hardening**: Implement encryption, authentication, anti-replay mechanisms

## System Requirements

- **OS**: Linux with BlueZ support (Kali Linux recommended)
- **Hardware**: Bluetooth 4.0+ USB adapter or built-in adapter
- **Python**: 3.6+
- **Dependencies**: `dbus-python`, `PyGObject`

## Installation

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip bluez bluez-tools libglib2.0-dev libdbus-1-dev

# Install Python packages
sudo pip3 install dbus-python PyGObject
```

## Quick Start

### 1. Verify Bluetooth Hardware

```bash
# Check Bluetooth adapter is connected
lsusb | grep -i bluetooth

# List available adapters
hcitool dev
```

### 2. Start the Server

```bash
# Enable Bluetooth service
sudo systemctl restart bluetooth
sudo hciconfig hci0 up

# Run the GCM server
sudo python3 gcm_ble_server.py
```

**Expected Output:**
```
GATT application registered
Advertisement registered

GCM BLE Simulator Running...
Device Name: GCM-Simulator
Waiting for connections...

[14:32:15] Glucose: 125 mg/dL
[14:32:20] Glucose: 132 mg/dL
[14:32:25] Glucose: 118 mg/dL
```

### 3. Connect Mobile Device

1. Open **nRF Connect** app on your phone
2. Scan for Bluetooth devices
3. Find and connect to **"GCM-Simulator"**
4. View real-time glucose readings (updates every 5 seconds)

## Data Format

Glucose readings are transmitted in the standard Bluetooth SFLOAT format used by real CGM devices.

**Packet Structure (7 bytes):**
```
Byte 0      Bytes 1-2          Bytes 3-4
Flags       Sequence Number    Glucose Value (SFLOAT)
```

**Example:** Hex `00 01 00 A8 00` → Sequence #1, 160 mg/dL

**Packet Breakdown:**
- **First 4 bytes** (`00 01 00`): Flags (1 byte) + Sequence (2 bytes, little-endian)
- **Last 2 bytes** (`A8 00`): Glucose value in Bluetooth SFLOAT format (16-bit)

For detailed protocol explanation, see [GATT_PROTOCOL.md](GATT_PROTOCOL.md#glucose-data-format).

## Architecture

**GATT Service Configuration:**
- **Service UUID**: `00001808` (Glucose Service - SIG standardized)
- **Characteristic UUID**: `00002a18` (Glucose Measurement)
- **Properties**: Read + Notify
- **Update Interval**: Every 5 seconds
- **Device Name**: GCM-Simulator

**Technical Stack:**
- GATT (Generic Attribute Profile) - standard BLE medical device protocol
- BlueZ - Linux Bluetooth implementation
- D-Bus - system message bus for BlueZ integration
- Python 3 - clean, maintainable codebase

## Troubleshooting

**Bluetooth adapter not found:**
```bash
lsusb | grep -i bluetooth
hcitool dev
```

**"Permission denied" error:**
Always use `sudo`:
```bash
sudo python3 gcm_ble_server.py
```

**"No such device" error:**
```bash
sudo systemctl restart bluetooth
sudo hciconfig hci0 up
```

**Device not visible on mobile:**
```bash
# Restart and bring up adapter
sudo systemctl restart bluetooth
sudo hciconfig hci0 up

# Kill any existing server
pkill -f gcm_ble_server

# Start fresh
sudo python3 gcm_ble_server.py
```

**Cannot register GATT application:**
Another application may be using hci0. Stop it and restart Bluetooth, then try again.

## Roadmap

**Current (Phase 1):** ✅ Complete
- GATT server with real-time glucose simulation
- Mobile app integration via nRF Connect

**Planned (Phase 2-5):**
- **Phase 2**: BLE packet interception and analysis
- **Phase 3**: Replay attack vulnerability testing  
- **Phase 4**: Security hardening (encryption, authentication)
- **Phase 5**: Real-world CGM device comparison and security assessment

For research objectives and implementation details, see [GATT_PROTOCOL.md](GATT_PROTOCOL.md#roadmap).



## Documentation

For detailed technical information about GATT protocol, BlueZ integration, and architecture, see [GATT_PROTOCOL.md](GATT_PROTOCOL.md).

## License

MIT License

## Author

Amit
