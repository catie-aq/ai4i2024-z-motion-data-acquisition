"""
Scan/Discovery
--------------
Example showing how to scan for BLE devices.
Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>
"""

import asyncio
from bleak import discover
from bleak import BleakClient, BleakScanner, BleakError
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from threading import RLock
import argparse
import time
from datetime import datetime
import csv

class BleScanner():
    """
    Allows to scan, print detected devices, and return MAC address of the resquested device if found
    """
    def __init__(self):
        self._detected_devices = []
        self._device_name = None
        self._detected_address = None

    async def scan(self, name, scan_timeout=5.0):
        self._device_name = name
        scanner = BleakScanner(self.scan_callback)
        print("Scanning BLE peripherals...")
        await scanner.start()
        await asyncio.sleep(scan_timeout)
        await scanner.stop()

        return self._detected_address

    async def scan_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        if not (device.address, device.name) in self._detected_devices:
            self._detected_devices.append((device.address, device.name))
            print("New device: ", device.address, "- RSSI: ", advertisement_data.rssi, "-", device.name)
            if sensor_local_name == device.name:
                print("{} sensor found ({})".format(device.name, device.address))
                self._detected_address = device.address        

class BleSensor():

    def __init__(self, name, hci_device=0):
        self._name = name
        self._address = None
        self._peripheral = None
        self._notifications = {}

    async def connect(self, scan_timeout=5.0):
        with scan_lock:
            # Get address
            scanner = BleScanner()
            self._address = await scanner.scan(self._name)
            if not self._address:
                print("Sensor {} not found".format(self._name))
                return False

            # Connect to sensor
            print("Connecting to sensor ({})...".format(self._address))
            try:
                self._peripheral = BleakClient(self._address)
                await self._peripheral.connect()
                print("Connected")
                return True

            except BleakError as err:
                print("Error connecting to sensor {}".format(self._name))
                print (err)
                return False
            except asyncio.exceptions.TimeoutError:
                print("Timeout when connecting to sensor {}".format(self._name))

    def is_connected(self):
        return self._peripheral.is_connected

    async def print_services(self):
        svcs = self._peripheral.services
        print("Services:")
        for service in svcs:
            print(service)
            for char in service.characteristics:
                print("\t", char)

    async def enable_notifications(self, characteristic, callback):
        try:
            await self._peripheral.start_notify(characteristic, callback=callback)

        except BleakError as e:
            print("Error enabling notifications for {} {}".format(self._name, e))

    async def disable_notifications(self, characteristic):
        try:
            await self._peripheral.stop_notify(characteristic)

        except BleakError as e:
            print("Error stopping notifications for {} {}".format(self._name, e))

    async def write_characteristic(self, char, value):
        try:
            print(value)
            await self._peripheral.write_gatt_char(char, value)
        except BleakError as e:
            print("Error writing characteristic ", e)

    def disconnect(self):
        if self._peripheral:
            try:
                self._peripheral.disconnect()
            except BleakError:
                print("Error when disconnecting")

class SensorHandler():

    def __init__(self, sensor_name):
        self._alive = True
        self._sensor_local_name = sensor_name
        self._sensor = BleSensor(sensor_name)
        self._rx_buffer = bytearray()
        self._first_write = True
        self._csv_filename_motion = str(self._sensor_local_name) + datetime.utcnow().strftime("_%Y-%m-%d_%H-%M-%S") + ".csv"
        self._reconnect = True
        

    def on_battery_level_notification(self, sender, data):
        battery_level = int.from_bytes(data, byteorder="little")
        print("[{}] Battery level: {} %".format(self._sensor_local_name, battery_level))
                
    def on_rx_stream_notification(self, sender, data):
        """Simple notification handler which prints the data received."""
        #timestamp = int.from_bytes(data[0:4], byteorder='little')
        config = int(data[0])

        if config == 0:
            accX = round(float(int.from_bytes(data[1:3], byteorder='little', signed=True)/100.0), 3)
            accY = round(float(int.from_bytes(data[3:5], byteorder='little', signed=True)/100.0), 3)
            accZ = round(float(int.from_bytes(data[5:7], byteorder='little', signed=True)/100.0), 3)
            gyrX = round(float(int.from_bytes(data[7:9], byteorder="little", signed=True)/100.0), 3)
            gyrY = round(float(int.from_bytes(data[9:11], byteorder="little", signed=True)/100.0), 3)
            gyrZ = round(float(int.from_bytes(data[11:13], byteorder="little", signed=True)/100.0), 3)
            magX = round(float(int.from_bytes(data[13:15], byteorder="little", signed=True)/100.0), 3)
            magY = round(float(int.from_bytes(data[15:17], byteorder="little", signed=True)/100.0), 3)
            magZ = round(float(int.from_bytes(data[17:19], byteorder="little", signed=True)/100.0), 3)

            print(config, accX, accY, accZ, gyrX, gyrY, gyrZ, magX, magY, magZ)

            if self._first_write:
                self._first_write = False
                with open(self._csv_filename_motion, 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(['acc_x', 'acc_y', 'acc_z', 'gyr_x', 'gyr_y', 'gyr_z', 'magX', 'magY', 'magZ'])
            try:
                with open(self._csv_filename_motion, 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow([accX, accY, accZ, gyrX, gyrY, gyrZ, magX, magY, magZ])
            except OSError as error:
                print("Error opening CSV file {}: {}".format(self._csv_filename_motion, error.strerror))

        if config == 1:
            accX = round(float(int.from_bytes(data[1:3], byteorder='little', signed=True)/100.0), 3)
            accY = round(float(int.from_bytes(data[3:5], byteorder='little', signed=True)/100.0), 3)
            accZ = round(float(int.from_bytes(data[5:7], byteorder='little', signed=True)/100.0), 3)
            yaw = round(float(int.from_bytes(data[7:9], byteorder="little", signed=True)/100.0), 3)
            pitch = round(float(int.from_bytes(data[9:11], byteorder="little", signed=True)/100.0), 3)
            roll = round(float(int.from_bytes(data[11:13], byteorder="little", signed=True)/100.0), 3)

            print(config, accX, accY, accZ, yaw, pitch, roll)

            if self._first_write:
                self._first_write = False
                with open(self._csv_filename_motion, 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(['acc_x', 'acc_y', 'acc_z', 'Yaw', 'Pitch', 'Roll'])
            try:
                with open(self._csv_filename_motion, 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow([accX, accY, accZ, yaw, pitch, roll])
            except OSError as error:
                print("Error opening CSV file {}: {}".format(self._csv_filename_motion, error.strerror))

        if config == 2:
            accX = round(float(int.from_bytes(data[1:3], byteorder='little', signed=True)/100.0), 3)
            accY = round(float(int.from_bytes(data[3:5], byteorder='little', signed=True)/100.0), 3)
            accZ = round(float(int.from_bytes(data[5:7], byteorder='little', signed=True)/100.0), 3)
            qW = round(float(int.from_bytes(data[7:9], byteorder="little", signed=True)/16384), 3)
            qX = round(float(int.from_bytes(data[9:11], byteorder="little", signed=True)/16384), 3)
            qY = round(float(int.from_bytes(data[11:13], byteorder="little", signed=True)/16384), 3)
            qZ = round(float(int.from_bytes(data[13:15], byteorder="little", signed=True)/16384), 3)
            
            print(config, accX, accY, accZ, qW, qX, qY, qZ)

            if self._first_write:
                self._first_write = False
                with open(self._csv_filename_motion, 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(['acc_x', 'acc_y', 'acc_z', 'qW', 'qX', 'qY', 'qZ'])
            try:
                with open(self._csv_filename_motion, 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow([accX, accY, accZ, qW, qX, qY, qZ])
            except OSError as error:
                print("Error opening CSV file {}: {}".format(self._csv_filename_motion, error.strerror))

    async def run(self):
        # Connect to BLE sensor
        while not await self._sensor.connect():
            print("Unable to connect to BLE sensor {}".format(self._sensor_local_name))

        await self._sensor.print_services()

        # Apply stream config
        await self._sensor.write_characteristic("6e400002-b5a3-f393-e0a9-e50e24dcca9e", stream_config.to_bytes(1, "little"))

        # Enable desired notifications
        await self._sensor.enable_notifications("00002a19-0000-1000-8000-00805f9b34fb", self.on_battery_level_notification) # Battery Level characteristic
        await self._sensor.enable_notifications("6e400003-b5a3-f393-e0a9-e50e24dcca9e", self.on_rx_stream_notification) # Stream service receive characteristic

        # Main loop
        while self._alive:
            if self._sensor.is_connected():
                await asyncio.sleep(1)
            else:
                print("Sensor {} Disconnected !".format(self._sensor_local_name))
                print("Reconnecting...")
                while not await self._sensor.connect():
                    print("Unable to connect to BLE sensor {}".format(self._sensor_local_name))
                # Apply stream config
                await self._sensor.write_characteristic("6e400002-b5a3-f393-e0a9-e50e24dcca9e", stream_config.to_bytes(1, "little"))
                # Enable desired notifications
                await self._sensor.enable_notifications("00002a19-0000-1000-8000-00805f9b34fb", self.on_battery_level_notification) # Battery Level characteristic
                await self._sensor.enable_notifications("6e400003-b5a3-f393-e0a9-e50e24dcca9e", self.on_rx_stream_notification) # Stream service receive characteristic

    def start(self):
        print("Starting Asyncio task for sensor {}".format(self._sensor_local_name))
        return asyncio.create_task(self.run())

    def stop(self):
        self._sensor.disconnect()
        self._alive = False

    def disconnect(self):
        self._reconnect = False
        self._sensor.disconnect()

async def run():
    try:
        z_motion = SensorHandler(sensor_local_name)
        z_motion.start()

        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        z_motion.stop()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("sensor_local_name", metavar="BLE_SENSOR_NAME", help="sensor to connect to")
    #parser.add_argument("--hci-device", type=int, default=0, help="HCI device to use")
    args = parser.parse_args()
    sensor_local_name = args.sensor_local_name
    #hci_device = args.hci_device

    # Ask for the stream mode of Z_Motion
    response = input("Which kind of data do you want to collect:\n\
        1 - Acceleration (X, Y, Z) + Rotation Speed (X, Y, Z) + Magnetic Field (X, Y, Z)\n\
        2 - Acceleration (X, Y, Z) + Euler andgles (Y, P, R)\n\
        3 - Acceleration (X, Y, Z) + Quaternion (W, X, Y, Z)\n")

    response = int(response)

    if response == 1:
        print("Acceleration (X, Y, Z) + Rotation Speed (X, Y, Z) + Magnetic Field (X, Y, Z) selected")
        time.sleep(1)
        stream_config = 0
    if response == 2:
        print("2 - Acceleration (X, Y, Z) + Euler andgles (Y, P, R) selected")
        time.sleep(1)
        stream_config = 1
    if response == 3:
        print("Acceleration (X, Y, Z) + Quaternion (W, X, Y, Z)")
        time.sleep(1)
        stream_config = 2

    # create the lock object to schedule the scanner access
    global scan_lock
    scan_lock = RLock()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
