#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
import struct
import random
from datetime import datetime

BLUEZ_SERVICE_NAME = "org.bluez"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

GLUCOSE_SERVICE_UUID = "00001808-0000-1000-8000-00805f9b34fb"
GLUCOSE_MEASUREMENT_UUID = "00002a18-0000-1000-8000-00805f9b34fb"

mainloop = None


# ---------- Helper: Bluetooth SFLOAT (16-bit) ---------- #
def encode_sfloat(value):
    """
    Encode integer glucose value into Bluetooth 16-bit SFLOAT
    Format: 12-bit mantissa + 4-bit exponent (base 10)
    """
    exponent = 0
    mantissa = int(value)

    if mantissa > 2047:
        mantissa = 2047
    if mantissa < -2048:
        mantissa = -2048

    return (exponent << 12) | (mantissa & 0x0FFF)


# ---------- Advertisement ---------- #
class Advertisement(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/advertisement"

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            LE_ADVERTISEMENT_IFACE: {
                "Type": "peripheral",
                "ServiceUUIDs": dbus.Array([GLUCOSE_SERVICE_UUID], signature="s"),
                "LocalName": "GCM-Simulator",
                "IncludeTxPower": dbus.Boolean(True),
            }
        }

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        return self.get_properties()[interface]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        print("Advertisement released")


# ---------- GATT Application ---------- #
class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = "/"
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for char in service.characteristics:
                response[char.get_path()] = char.get_properties()
        return response


class Service(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/service"

    def __init__(self, bus, index, uuid, primary=True):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                "UUID": self.uuid,
                "Primary": self.primary,
                "Characteristics": dbus.Array(
                    [c.get_path() for c in self.characteristics],
                    signature="o",
                ),
            }
        }


class GlucoseCharacteristic(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = service.path + "/char" + str(index)
        self.bus = bus
        self.service = service
        self.uuid = GLUCOSE_MEASUREMENT_UUID
        self.notifying = False
        self.sequence = 0
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            GATT_CHARACTERISTIC_IFACE: {
                "Service": self.service.get_path(),
                "UUID": self.uuid,
                "Flags": ["read", "notify"],
            }
        }

    def generate_glucose_packet(self):
        glucose_value = random.randint(80, 160)
        self.sequence += 1

        flags = 0x00  # No optional fields
        sfloat = encode_sfloat(glucose_value)

        packet = struct.pack("<BHH", flags, self.sequence, sfloat)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Glucose: {glucose_value} mg/dL")

        return dbus.ByteArray(packet)

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE,
                         in_signature="a{sv}",
                         out_signature="ay")
    def ReadValue(self, options):
        return self.generate_glucose_packet()

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE)
    def StartNotify(self):
        if self.notifying:
            return
        print("Notifications started")
        self.notifying = True
        GLib.timeout_add(5000, self.notify)

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE)
    def StopNotify(self):
        print("Notifications stopped")
        self.notifying = False

    def notify(self):
        if not self.notifying:
            return False

        value = self.generate_glucose_packet()

        self.PropertiesChanged(
            GATT_CHARACTERISTIC_IFACE,
            {"Value": value},
            [],
        )

        return True

    @dbus.service.signal(DBUS_PROP_IFACE, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


# ---------- Main ---------- #
def register_app_cb():
    print("GATT application registered")


def register_ad_cb():
    print("Advertisement registered")


def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter = "/org/bluez/hci0"

    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        GATT_MANAGER_IFACE,
    )

    ad_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        LE_ADVERTISING_MANAGER_IFACE,
    )

    app = Application(bus)
    service = Service(bus, 0, GLUCOSE_SERVICE_UUID)
    char = GlucoseCharacteristic(bus, 0, service)

    service.add_characteristic(char)
    app.add_service(service)

    advertisement = Advertisement(bus, 0)

    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=print)

    ad_manager.RegisterAdvertisement(advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=print)

    print("\nGCM BLE Simulator Running...")
    print("Device Name: GCM-Simulator")
    print("Waiting for connections...\n")

    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()

