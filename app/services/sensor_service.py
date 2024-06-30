import logging
import threading
import database.connection
from database.models import IrrigationControllers
from database.models import Sensors
from database.models import RealtimeSensorData

class SensorService:
    def __init__(self, controller_id, shared_data):
        self.logger = logging.getLogger(__name__)
        self.stop_event = threading.Event()
        self.controller_id = controller_id
        self.sensors_lock = threading.Lock() # For finding new sensors and updating the sensor list
        self.sensors = Sensors.get_all_sensors_by_controller(self.controller_id)
        self.shared_data = shared_data # Shared data between irrigation and sensor services


    def start(self):
        self.logger.info("Starting sensor service")
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()
        self.check_sensors_thread = threading.Thread(target=self.check_for_new_sensors)
        self.check_sensors_thread.start()
        self.save_data_thread = threading.Thread(target=self.save_data_periodically)
        self.save_data_thread.start()
    
    def stop(self):
        self.stop_event.set()
        if self.check_sensors_thread:
            self.check_sensors_thread.join()
        if self.thread:
            self.thread.join()
        if self.save_data_thread:
            self.save_data_thread.join()
        self.logger.info("Stopped sensor service")

    def check_for_new_sensors(self):
        self.stop_event.wait(10)
        current_sensors = set(sensor.sensorID for sensor in self.sensors)
        new_sensors_list = Sensors.get_all_sensors_by_controller(self.controller_id)
        new_sensors = set(sensor.sensorID for sensor in new_sensors_list)

        if current_sensors != new_sensors:
            self.logger.info("New sensor(s) found. Updating sensor list.")
            with self.sensors_lock:
                self.sensors = new_sensors_list

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
        with self.sensors_lock:
            if self.sensors:
                sensor_data = []
                for sensor in self.sensors:
                    self.logger.info(f"Reading data from sensor {sensor.sensorID} with GPIO port {sensor.gpioPort}")
                    sensor_data.append({"sensorID": sensor.sensorID, "value": 1})
                return sensor_data
            else:
                logging.warning("No sensors found for this controller.")
                return []


    def is_healthy(self):
            # Implement your health check logic here.
            # For example, you might check if the sensor is still responsive.
            # For this example, we'll just return True.
            return True