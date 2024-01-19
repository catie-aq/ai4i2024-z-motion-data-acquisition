#
#
# Usage example :
# python data_acquisition.py "6TRON Sensor 1" --output-dir acquired_data/ --files-prefix 1_ --stream-config 1
#
# where :
# 1 outputs : t,raw_acceleration_x,raw_acceleration_y,raw_acceleration_z,rotation_speed_x,rotation_speed_y,rotation_speed_z,magnetic_field_x,magnetic_field_y,magnetic_field_z
# 2 outputs : t,raw_acceleration_x,raw_acceleration_y,raw_acceleration_z,yaw,pitch,roll
# 3 outputs : t,raw_acceleration_x,raw_acceleration_y,raw_acceleration_z,quaternion_w,quaternion_x,quaternion_y,quaternion_z

import sys, termios, tty, os, time

import asyncio
from bleak import BleakClient, BleakScanner, BleakError
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from threading import RLock, Thread
import argparse
import time
import csv


def term_display(string):
    sys.stdout.write(string + "\r\n")
    sys.stdout.flush()


class BleScanner():
    """
    Allows to scan, print detected devices, and return MAC address of the resquested device if found
    """

    def __init__(
            self,
            show_new_devices=False
            ):
        self._detected_devices = []
        self._device_name = None
        self._detected_address = None
        self._show_new_devices = show_new_devices

    async def scan(self, name, scan_timeout=5.0):
        self._device_name = name
        scanner = BleakScanner(self.scan_callback)
        term_display("Scanning BLE peripherals...")
        await scanner.start()
        await asyncio.sleep(scan_timeout)
        await scanner.stop()
        return self._detected_address

    async def scan_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        if not (device.address, device.name) in self._detected_devices:
            self._detected_devices.append((device.address, device.name))
            if self._show_new_devices:
                term_display("New device: ", device.address, "- RSSI: ", advertisement_data.rssi, "-", device.name)
            if sensor_local_name == device.name:
                term_display("{} sensor found ({})".format(device.name, device.address))
                self._detected_address = device.address        




class BleSensor():

    def __init__(
        self,
        name,
        verbose = False
        ):
        self._name = name
        self._verbose = verbose
        self._address = None
        self._peripheral = None
        self._notifications = {}

    async def connect(self, scan_timeout=5.0):
        with scan_lock:
            # Get address
            scanner = BleScanner()
            self._address = await scanner.scan(self._name)
            if not self._address:
                term_display("Sensor {} not found".format(self._name))
                return False

            # Connect to sensor
            term_display("Connecting to sensor ({})...".format(self._address))
            try:
                self._peripheral = BleakClient(self._address)
                await self._peripheral.connect()
                term_display("Connected")
                return True

            except BleakError as err:
                term_display("Error connecting to sensor {}".format(self._name))
                term_display (err)
                return False
            except asyncio.exceptions.TimeoutError:
                term_display("Timeout when connecting to sensor {}".format(self._name))

    def is_connected(self):
        return self._peripheral.is_connected

    async def print_services(self):
        svcs = self._peripheral.services
        term_display("Services:")
        for service in svcs:
            term_display(service)
            for char in service.characteristics:
                term_display("\t", char)

    async def enable_notifications(self, characteristic, callback):
        try:
            await self._peripheral.start_notify(characteristic, callback=callback)

        except BleakError as e:
            if self._verbose:
                term_display("Error enabling notifications for {} {}".format(self._name, e))

    async def disable_notifications(self, characteristic):
        try:
            await self._peripheral.stop_notify(characteristic)

        except BleakError as e:
            if self._verbose:
                term_display("Error stopping notifications for {} {}".format(self._name, e))

    async def write_characteristic(self, char, value):
        try:
            if self._verbose:
                term_display(value)
            await self._peripheral.write_gatt_char(char, value)
        except BleakError as e:
            if self._verbose:
                term_display("Error writing characteristic ", e)

    def disconnect(self):
        if self._peripheral:
            try:
                self._peripheral.disconnect()
            except BleakError:
                if self._verbose:
                    term_display("Error when disconnecting")



PRECISION = 6


class SensorHandler():

    def __init__(
        self,
        sensor_name,
        stream_config,
        csv_logger=None,
        verbose=False
        ):
        self._sensor_local_name = sensor_name
        self._stream_config = stream_config
        self._csv_logger = csv_logger
        self._verbose = verbose

        self._alive = True
        self._sensor = BleSensor(sensor_name, verbose=self._verbose)
        self._rx_buffer = bytearray()

        self._reconnect = True
        self._ref_timestamp = 0

        self._is_streaming_data = False
        

    def on_battery_level_notification(self, sender, data):
        battery_level = int.from_bytes(data, byteorder="little")
        term_display("[{}] Battery level: {} %".format(self._sensor_local_name, battery_level))
                

    def on_rx_stream_notification(self, sender, data):
        """Simple notification handler which prints the data received."""

        config = int(data[0])

        if config != self._stream_config:
            term_display("Config values not matching : %s <-> %s" % (config, self._stream_config))
            exit(0)

        t = round(time.time() - self._ref_timestamp, 4)
        if self._stream_config == 0:
            accX = round(float(int.from_bytes(data[1:3], byteorder='little', signed=True)/100.0), PRECISION)
            accY = round(float(int.from_bytes(data[3:5], byteorder='little', signed=True)/100.0), PRECISION)
            accZ = round(float(int.from_bytes(data[5:7], byteorder='little', signed=True)/100.0), PRECISION)
            gyrX = round(float(int.from_bytes(data[7:9], byteorder="little", signed=True)/100.0), PRECISION)
            gyrY = round(float(int.from_bytes(data[9:11], byteorder="little", signed=True)/100.0), PRECISION)
            gyrZ = round(float(int.from_bytes(data[11:13], byteorder="little", signed=True)/100.0), PRECISION)
            magX = round(float(int.from_bytes(data[13:15], byteorder="little", signed=True)/100.0), PRECISION)
            magY = round(float(int.from_bytes(data[15:17], byteorder="little", signed=True)/100.0), PRECISION)
            magZ = round(float(int.from_bytes(data[17:19], byteorder="little", signed=True)/100.0), PRECISION)
            row = [t, accX, accY, accZ, gyrX, gyrY, gyrZ, magX, magY, magZ]
            if self._verbose:
                term_display(row)
            if self._csv_logger is not None:
                self._csv_logger.write(row)

        elif self._stream_config == 1:
            accX = round(float(int.from_bytes(data[1:3], byteorder='little', signed=True)/100.0), PRECISION)
            accY = round(float(int.from_bytes(data[3:5], byteorder='little', signed=True)/100.0), PRECISION)
            accZ = round(float(int.from_bytes(data[5:7], byteorder='little', signed=True)/100.0), PRECISION)
            yaw = round(float(int.from_bytes(data[7:9], byteorder="little", signed=True)/100.0), PRECISION)
            pitch = round(float(int.from_bytes(data[9:11], byteorder="little", signed=True)/100.0), PRECISION)
            roll = round(float(int.from_bytes(data[11:13], byteorder="little", signed=True)/100.0), PRECISION)
            row = [t, accX, accY, accZ, yaw, pitch, roll]
            if self._verbose:
                term_display(row)
            if self._csv_logger is not None:
                self._csv_logger.write(row)

        elif self._stream_config == 2:
            accX = round(float(int.from_bytes(data[1:3], byteorder='little', signed=True)/100.0), PRECISION)
            accY = round(float(int.from_bytes(data[3:5], byteorder='little', signed=True)/100.0), PRECISION)
            accZ = round(float(int.from_bytes(data[5:7], byteorder='little', signed=True)/100.0), PRECISION)
            qW = round(float(int.from_bytes(data[7:9], byteorder="little", signed=True)/16384), PRECISION)
            qX = round(float(int.from_bytes(data[9:11], byteorder="little", signed=True)/16384), PRECISION)
            qY = round(float(int.from_bytes(data[11:13], byteorder="little", signed=True)/16384), PRECISION)
            qZ = round(float(int.from_bytes(data[13:15], byteorder="little", signed=True)/16384), PRECISION)
            row = [t, accX, accY, accZ, qW, qX, qY, qZ]
            if self._verbose:
                term_display(row)
            if self._csv_logger is not None:
                self._csv_logger.write(row)

    async def run(self):
        # Connect to BLE sensor
        while not await self._sensor.connect():
            term_display("Unable to connect to BLE sensor {}".format(self._sensor_local_name))

        if self._verbose:
            await self._sensor.print_services()

        # Apply stream config
        await self._sensor.write_characteristic("6e400002-b5a3-f393-e0a9-e50e24dcca9e", self._stream_config.to_bytes(1, "little"))

        # Enable desired notifications
        await self._sensor.enable_notifications("00002a19-0000-1000-8000-00805f9b34fb", self.on_battery_level_notification) # Battery Level characteristic
        await self._sensor.enable_notifications("6e400003-b5a3-f393-e0a9-e50e24dcca9e", self.on_rx_stream_notification) # Stream service receive characteristic

        self._ref_timestamp = time.time()

        # Logger activation / information
        if self._csv_logger:
            self._csv_logger.activate()
            term_display("\r\nPress [space] to start recording data......")
            term_display("Press [q] / [ctrl+c] to quit...\r\n")

        # Main loop
        while self._alive:
            if self._sensor.is_connected():
                await asyncio.sleep(1)
            else:
                term_display("Sensor {} Disconnected !".format(self._sensor_local_name))
                term_display("Reconnecting...")
                while not await self._sensor.connect():
                    term_display("Unable to connect to BLE sensor {}".format(self._sensor_local_name))
                # Apply stream config
                await self._sensor.write_characteristic("6e400002-b5a3-f393-e0a9-e50e24dcca9e", self._stream_config.to_bytes(1, "little"))
                # Enable desired notifications
                await self._sensor.enable_notifications("00002a19-0000-1000-8000-00805f9b34fb", self.on_battery_level_notification) # Battery Level characteristic
                await self._sensor.enable_notifications("6e400003-b5a3-f393-e0a9-e50e24dcca9e", self.on_rx_stream_notification) # Stream service receive characteristic

    def start(self):
        if self._verbose:
            term_display("Starting Asyncio task for sensor {}".format(self._sensor_local_name))
        return asyncio.create_task(self.run())

    def stop(self):
        self._sensor.disconnect()
        self._alive = False

    def disconnect(self):
        self._reconnect = False
        self._sensor.disconnect()

    def is_streaming_data(self):
        return self._is_streaming_data



CONFIG_ROWS_NAMES = {
    0: [
    "t",
    "raw_acceleration_x",
    "raw_acceleration_y",
    "raw_acceleration_z",
    "rotation_speed_x",
    "rotation_speed_y",
    "rotation_speed_z",
    "magnetic_field_x",
    "magnetic_field_y",
    "magnetic_field_z",
    ],

    1: [
    "t",
    "raw_acceleration_x",
    "raw_acceleration_y",
    "raw_acceleration_z",
    "yaw",
    "pitch",
    "roll"
    ],

    2: [
    "t",
    "raw_acceleration_x",
    "raw_acceleration_y",
    "raw_acceleration_z",
    "quaternion_w",
    "quaternion_x",
    "quaternion_y",
    "quaternion_z"
    ]
}


class CsvLogger():

    def __init__(self,
        output_dir_path,
        file_name_prefix,
        stream_config
        ):
        self._output_dir_path = output_dir_path
        self._file_name_prefix = file_name_prefix
        self._stream_config = stream_config
        self._is_actived = False
        self._logging_engaged = False
        self._epoch = 0
        self._csv_file_path = None
        self._config_rows_names = CONFIG_ROWS_NAMES[self._stream_config]


    def activate(self):
        self._is_actived = True


    def is_activated(self):
        return self._is_actived


    def start_capture(self):
        self._logging_engaged = True
        self._epoch += 1
        self.ensure_file_exists()


    def stop_capture(self):
        self._logging_engaged = False


    def is_logging_engaged(self):
        return self._logging_engaged


    def ensure_file_exists(self):
        csv_file_name = "%s%s.csv" % (self._file_name_prefix, self._epoch)
        csv_file_path = os.path.join(self._output_dir_path, csv_file_name)
        if not self._csv_file_path or self._csv_file_path != csv_file_path:
            self._csv_file_path = csv_file_path
            if not os.path.isfile(self._csv_file_path):
                with open(self._csv_file_path, "w") as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(self._config_rows_names)

    def write(self, row):
        if self._is_actived and self._logging_engaged:
            with open(self._csv_file_path, "a") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(row)

    def get_csv_file_path(self):
        return self._csv_file_path



class KeystrokeHandler(Thread):

    def __init__(self, logger=None):
        Thread.__init__(self)
        self._c = None
        self._logger = logger

    def getch(self):
        # from : https://ubuntuforums.org/showthread.php?t=2394609
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def run(self):
        while True:
            c = self.getch()

            if c == " ":
                if self._logger and self._logger.is_activated():
                    if self._logger.is_logging_engaged():
                        self._logger.stop_capture()
                        term_display("Stopped.\r\n")
                        term_display("Press [q] / [ctrl+c] to quit...")
                        term_display("Press [space] to record new data...\r\n")
                    else:
                        self._logger.start_capture()
                        term_display("Recording data in file %s..." % self._logger.get_csv_file_path())

            elif ord(c) in [3, 113, 120, 122]:   # 3 : Ctrl+C, q: 113, x : 120 : z, 122 : 
                term_display("\nPress ctrl+c to stop definitively...\n")
                break


async def run():
    try:
        csv_logger = CsvLogger(
            output_dir_path=output_dir_path,
            file_name_prefix=file_name_prefix,
            stream_config=stream_config
        )

        z_motion = SensorHandler(
            sensor_name=sensor_local_name,
            csv_logger=csv_logger,
            stream_config=stream_config
            )
        
        keystroke_handler_thread = KeystrokeHandler(csv_logger)
        keystroke_handler_thread.daemon = True
        keystroke_handler_thread.start()
        
        z_motion.start()

        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        z_motion.stop()







if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("sensor_local_name", metavar="BLE_SENSOR_NAME", help="Usage example : python data_acquisition.py \"6TRON Sensor 1\" --output-dir acquired_data/ --files-prefix 1_ --stream-config 1")
    parser.add_argument("--stream-config", type=str, help="stream config: 1, 2 or 3", required=True)
    parser.add_argument("--output-dir", type=str, help="output dir path", required=True)
    parser.add_argument("--files-prefix", type=str, help="output log files prefix", required=True)

    args = parser.parse_args()
    sensor_local_name = args.sensor_local_name
    output_dir_path = args.output_dir
    file_name_prefix = args.files_prefix
    stream_config = int(args.stream_config) - 1

    # create the lock object to schedule the scanner access
    global scan_lock
    scan_lock = RLock()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        term_display("Closing")
        exit(0)
