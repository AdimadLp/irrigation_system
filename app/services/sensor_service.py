from logging_config import setup_logger
import threading
import database.connection
from database.models import IrrigationControllers
from database.models import Sensors
from database.models import RealtimeSensorData
from helpers.thread_safe_list import ThreadSafeList


class SensorService:
    def __init__(self, controller_id, shared_data):
        self.logger = setup_logger(__name__)
        self.stop_event = threading.Event()
        self.controller_id = controller_id
        self.sensors = ThreadSafeList().overwrite(
            Sensors.get_all_sensors_by_controller(self.controller_id)
        )
        self.shared_data = (
            shared_data  # Shared data between irrigation and sensor services
        )

    def start(self):
        self.logger.info("Starting sensor service")
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()
        self.save_data_thread = threading.Thread(target=self.save_data_periodically)
        self.save_data_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        if self.save_data_thread:
            self.save_data_thread.join()
        self.logger.info("Stopped sensor service")

    def restart(self):
        self.stop()
        self.start()

    def update_data(self):
        while not self.stop_event.is_set():
            new_data = self.read_sensor_data()
            self.shared_data.overwrite(new_data)
            RealtimeSensorData.update_sensor_data(new_data)
            self.stop_event.wait(1)

    def save_data_periodically(self):
        while not self.stop_event.is_set():
            if len(self.shared_data) > 0:
                Sensors.save_sensor_data(self.shared_data.get())
                self.logger.info("Sensor data saved to database.")
            self.stop_event.wait(300)

    def read_sensor_data(self):
        self.stop_event.wait(1)  # Sleep for a while to simulate reading sensor data
        if self.sensors:
            sensor_data = []
            for sensor in self.sensors:
                self.logger.info(
                    f"Reading data from sensor {sensor.sensorID} with GPIO port {sensor.gpioPort}"
                )
                sensor_data.append({"sensorID": sensor.sensorID, "value": 1})
            return sensor_data
        else:
            logging.warning("No sensors found for this controller.")
            return []

    def is_healthy(self):
        return self.thread.is_alive()
