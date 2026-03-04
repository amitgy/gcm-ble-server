# GATT Protocol & GCM Implementation Guide

## Table of Contents

1. [What is GATT?](#what-is-gatt)
2. [What is GCM (Continuous Glucose Monitoring)?](#what-is-gcm)
3. [Why BlueZ & D-Bus?](#why-bluez--d-bus)
4. [Architecture Overview](#architecture-overview)
5. [Glucose Data Format](#glucose-data-format)
6. [Implementation Details](#implementation-details)

---

## What is GATT?

### GATT = Generic Attribute Profile

GATT is a standardized protocol in Bluetooth Low Energy (BLE) that defines how two devices communicate and exchange data using a **Client-Server model**.

### Key Concepts

#### 1. **Service**
A collection of data and functionality related to a specific feature. Services are identified by **UUIDs** (Universally Unique Identifiers).

```
Example: Glucose Service
UUID: 00001808-0000-1000-8000-00805f9b34fb
```

#### 2. **Characteristic**
A data container within a service that holds actual values and defines how they can be accessed.

```
Example: Glucose Measurement Characteristic
UUID: 00002a18-0000-1000-8000-00805f9b34fb
Flags: Read, Notify
```

#### 3. **Properties/Flags**
Defines how a characteristic can be used:

| Property | Description |
|----------|-------------|
| **Read** | Client can request current value |
| **Write** | Client can send data to server |
| **Notify** | Server sends unsolicited updates to client |
| **Indicate** | Like Notify but requires acknowledgment |

### GATT Communication Flow

```
BLE Server (Kali)          BLE Client (Mobile App)
    |                              |
    |--- Advertisement Packet ---->|
    |                              |
    |<--- Connection Request ------|
    |                              |
    |--- GATT Service Discovered <-|
    |                              |
    |--- Glucose Value (Notify) --->|
    |--- Glucose Value (Notify) --->|
    |--- Glucose Value (Notify) --->|
```

### Why GATT is Needed

- **Standardized Communication**: Medical devices follow Bluetooth Health Device Profile (HDP) which uses GATT
- **Low Power**: GATT is optimized for energy efficiency
- **Real-time Updates**: Notifications allow server to push data instead of client polling
- **Interoperability**: Any BLE-capable device can connect to a GATT server

---

## What is GCM (Continuous Glucose Monitoring)?

### Overview

A Continuous Glucose Monitor is a medical device that:
- Measures blood glucose levels continuously (every 5-15 minutes)
- Transmits data wirelessly to a receiver or mobile application
- Helps patients with diabetes manage blood sugar levels in real-time

### Why GCM is Important

- **Real-time Alerts**: Warns of dangerous glucose levels
- **Trend Analysis**: Shows glucose direction (rising/falling)
- **Reduced Fingersticks**: Less frequent blood tests needed
- **Better Control**: Improves medication timing and dosing

### GCM Data Characteristics

- **Measurement Interval**: Every 5-15 seconds (varies by device)
- **Accuracy**: ±10-15% of reference glucose meters
- **Range**: Typically 40-400 mg/dL
- **Trend Information**: Shows rate of change

---

## Why BlueZ & D-Bus?

### BlueZ: The Linux Bluetooth Stack

**BlueZ** is the official Bluetooth implementation for Linux. It provides:

1. **Kernel-Level Bluetooth Support**: Hardware abstraction for Bluetooth adapters
2. **GATT Server/Client Implementation**: Built-in BLE stack
3. **Device Management**: Pairing, bonding, connection handling

```
┌─────────────────────────────────┐
│   BlueZ Bluetooth Stack         │
│  (Kernel Module: Bluetooth)     │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│   D-Bus Interface (bluez API)   │
│  (org.bluez service)            │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│  Python Application             │
│  (gcm_ble_server.py)            │
└─────────────────────────────────┘
```

### D-Bus: Inter-Process Communication

**D-Bus** is a message bus system that allows applications to communicate with system services.

**In our case:**
- BlueZ exposes its functionality through D-Bus
- Our Python app communicates with BlueZ via D-Bus
- We can register GATT services, characteristics, and handle connections

### Key D-Bus Objects in Our Implementation

```python
BLUEZ_SERVICE_NAME = "org.bluez"           # BlueZ service
GATT_MANAGER_IFACE = "org.bluez.GattManager1"    # Register GATT apps
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"  # Advertise
GATT_SERVICE_IFACE = "org.bluez.GattService1"    # Define services
GATT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"  # Define characteristics
```

### D-Bus Method Call Example

```python
service_manager = dbus.Interface(
    bus.get_object(BLUEZ_SERVICE_NAME, adapter),
    GATT_MANAGER_IFACE,
)

# Call RegisterApplication on BlueZ
service_manager.RegisterApplication(
    app.get_path(),  # Our GATT app path
    {},
    reply_handler=register_app_cb,
    error_handler=print
)
```

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────┐
│   Mobile Application (Android/iOS)      │
│   - Displays glucose readings            │
│   - Connects via BLE                     │
└────────────┬────────────────────────────┘
             │ BLE Wireless
┌────────────▼────────────────────────────┐
│   GCM BLE Server (gcm_ble_server.py)    │
│                                          │
│   ┌──────────────────────────────────┐  │
│   │  GATT Application                │  │
│   │  - Manages Services              │  │
│   │  - Manages Characteristics       │  │
│   └──────────────────────────────────┘  │
│                                          │
│   ┌──────────────────────────────────┐  │
│   │  Advertisement                   │  │
│   │  - Broadcasts device presence    │  │
│   │  - Service UUIDs                 │  │
│   └──────────────────────────────────┘  │
└────────────┬────────────────────────────┘
             │ D-Bus
┌────────────▼────────────────────────────┐
│   BlueZ Daemon                           │
│   - Bluetooth Stack                      │
│   - Device Management                    │
└────────────┬────────────────────────────┘
             │ Kernel
┌────────────▼────────────────────────────┐
│   Bluetooth Hardware (hci0)              │
│   - BLE Controller                       │
│   - Radio Transceiver                    │
└─────────────────────────────────────────┘
```

### Code Components

#### 1. **Advertisement Class**
Broadcasts the device's presence and available services:

```python
class Advertisement(dbus.service.Object):
    def get_properties(self):
        return {
            LE_ADVERTISEMENT_IFACE: {
                "Type": "peripheral",                    # Server mode
                "ServiceUUIDs": [GLUCOSE_SERVICE_UUID],  # What services we offer
                "LocalName": "GCM-Simulator",            # Device name
                "IncludeTxPower": dbus.Boolean(True),
            }
        }
```

#### 2. **Application Class**
Manages all GATT services and characteristics:

```python
class Application(dbus.service.Object):
    def __init__(self, bus):
        self.services = []  # Container for services
    
    def add_service(self, service):
        self.services.append(service)
    
    def GetManagedObjects(self):
        # Returns all services and characteristics to BlueZ
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for char in service.characteristics:
                response[char.get_path()] = char.get_properties()
        return response
```

#### 3. **Service Class**
Represents a GATT Service:

```python
class Service(dbus.service.Object):
    def __init__(self, bus, index, uuid, primary=True):
        self.uuid = uuid                      # Service identifier
        self.characteristics = []             # Data containers
        self.primary = primary                # Primary vs secondary service
```

#### 4. **GlucoseCharacteristic Class**
The actual data container that sends glucose readings:

```python
class GlucoseCharacteristic(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.uuid = GLUCOSE_MEASUREMENT_UUID  # Characteristic ID
        self.notifying = False                # Notification state
        self.sequence = 0                     # Packet counter
    
    def ReadValue(self, options):
        # Called when client reads characteristic
        return self.generate_glucose_packet()
    
    def StartNotify(self):
        # Called when client enables notifications
        self.notifying = True
        GLib.timeout_add(5000, self.notify)  # Send every 5 seconds
    
    def notify(self):
        # Push glucose data to connected client
        value = self.generate_glucose_packet()
        self.PropertiesChanged(...)  # Signal change to client
```

---

## Glucose Data Format

### Bluetooth SFLOAT (16-bit) Format

Glucose values are encoded in Bluetooth's SFLOAT (Special Float) format:

```
┌─────────────┬──────────────────────┐
│ Exponent    │ Mantissa             │
│ (4 bits)    │ (12 bits)            │
├─────────────┼──────────────────────┤
│ bits 15-12  │ bits 11-0            │
└─────────────┴──────────────────────┘

Format: (Exponent << 12) | (Mantissa & 0x0FFF)
```

### Complete Packet Structure

```
Byte 0          Bytes 1-2           Bytes 3-4
Flags           Sequence            Glucose (SFLOAT)
00              01 00               A8 00
(1 byte)        (2 bytes, LE)       (2 bytes, LE)
```

### Packet Breakdown Example

**Hex Packet**: `00 01 00 A8 00`

| Field | Hex | Binary | Meaning |
|-------|-----|--------|---------|
| Flags | 00 | 00000000 | No optional fields |
| Seq (LE) | 01 00 | 00000001 00000000 | Packet #1 |
| Glucose (LE) | A8 00 | 10101000 00000000 | SFLOAT for 160 mg/dL |

### Decoding Example

```python
# Received bytes: [0x00, 0x01, 0x00, 0xA8, 0x00]

flags = bytes[0]              # 0x00
sequence = bytes[1] | (bytes[2] << 8)   # 0x0001 = 1
sfloat_raw = bytes[3] | (bytes[4] << 8) # 0x00A8

# Decode SFLOAT
exponent = (sfloat_raw >> 12) & 0x0F
mantissa = sfloat_raw & 0x0FFF

# Convert mantissa to signed 12-bit
if mantissa & 0x0800:
    mantissa = -(~(mantissa - 1) & 0x0FFF)

glucose = mantissa * (10 ** exponent)  # 160 mg/dL
```

### Implementation in Code

```python
def encode_sfloat(value):
    """
    Encode integer glucose value into Bluetooth 16-bit SFLOAT
    Format: 12-bit mantissa + 4-bit exponent (base 10)
    """
    exponent = 0
    mantissa = int(value)
    
    # Clamp values to prevent overflow
    if mantissa > 2047:
        mantissa = 2047
    if mantissa < -2048:
        mantissa = -2048
    
    return (exponent << 12) | (mantissa & 0x0FFF)

def generate_glucose_packet(self):
    glucose_value = random.randint(80, 160)  # Random value 80-160 mg/dL
    self.sequence += 1
    
    flags = 0x00  # No optional fields
    sfloat = encode_sfloat(glucose_value)
    
    # Pack: flags (1 byte) + sequence (2 bytes LE) + sfloat (2 bytes LE)
    packet = struct.pack("<BHH", flags, self.sequence, sfloat)
    
    return dbus.ByteArray(packet)
```

---

## Implementation Details

### Initialization Flow

```python
def main():
    # 1. Setup D-Bus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    # 2. Get adapter (hci0)
    adapter = "/org/bluez/hci0"
    
    # 3. Create manager interfaces
    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        GATT_MANAGER_IFACE,
    )
    
    # 4. Create GATT hierarchy
    app = Application(bus)
    service = Service(bus, 0, GLUCOSE_SERVICE_UUID)
    char = GlucoseCharacteristic(bus, 0, service)
    service.add_characteristic(char)
    app.add_service(service)
    
    # 5. Register with BlueZ
    service_manager.RegisterApplication(app.get_path(), {})
    
    # 6. Run event loop
    mainloop = GLib.MainLoop()
    mainloop.run()
```

### Client Connection Sequence

```
Client                          Server
  |                                |
  |-------- Scan (Discover) ------->|
  |<----- Advertisement Packet -----|
  |                                |
  |------- Connect Request -------->|
  |<----- Connect Response --------|
  |                                |
  |--- Read Service UUIDs -------->|
  |<--- Services & Characteristics |
  |                                |
  |-- Enable Notifications ------->|
  |<--- Glucose Value (every 5s) --|
  |<--- Glucose Value (every 5s) --|
  |<--- Glucose Value (every 5s) --|
  |                                |
```

### Notification Mechanism

```python
def StartNotify(self):
    """Client requests notifications"""
    if self.notifying:
        return
    print("Notifications started")
    self.notifying = True
    GLib.timeout_add(5000, self.notify)  # Schedule notify() every 5 seconds

def notify(self):
    """Periodically send glucose data to client"""
    if not self.notifying:
        return False
    
    value = self.generate_glucose_packet()
    
    # Signal property change to client via D-Bus
    self.PropertiesChanged(
        GATT_CHARACTERISTIC_IFACE,
        {"Value": value},
        [],
    )
    
    return True  # Keep calling this function
```

---

## Security & Compliance

### Medical Device Standards

This implementation follows:
- **Bluetooth Health Device Profile (HDP)**
- **Glucose Service Specification (SIG)**
- **IEEE 11073 (Personal Health Devices)**

### UUID Standards

- **Glucose Service**: `00001808-0000-1000-8000-00805f9b34fb` (SIG assigned)
- **Glucose Measurement**: `00002a18-0000-1000-8000-00805f9b34fb` (SIG assigned)

### Real Device Considerations

When connecting to real CGM devices:
- Implement bonding/pairing for security
- Add encryption/authentication
- Validate checksums on packets
- Implement battery monitoring
- Add historical data storage

---

## Troubleshooting Guide

### BlueZ Not Finding Adapter

```bash
# Check available adapters
bluetoothctl list

# If hci0 not found, try:
sudo hciconfig -a
sudo hcitool dev
```

### D-Bus Permission Denied

```bash
# Run with sudo
sudo python3 gcm_ble_server.py

# Or add user to bluetooth group
sudo usermod -a -G bluetooth $USER
```

### Service Not Registering

```bash
# Check BlueZ service status
sudo systemctl status bluetooth

# Check D-Bus for bluez
dbus-send --system --print-reply --dest=org.bluez / org.freedesktop.DBus.ObjectManager.GetManagedObjects
```

---

## References

- [Bluetooth Core Specification](https://www.bluetooth.com/specifications/specs/)
- [Bluetooth Health Device Profile](https://www.bluetooth.com/specifications/specs/health-device-profile-specification/)
- [BlueZ Documentation](http://www.bluez.org/)
- [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-daemon.1.html)
- [IEEE 11073 Standard](https://standards.ieee.org/standard/11073-20601-2014.html)
