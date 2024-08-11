from logging_config import setup_logger
import threading
from datetime import datetime
from database.models import Plants
from database.models import Sensors
from database.models import Pumps
from database.models import Schedules
from database.models import WateringLogs
from services.sensor_service import SensorService
from helpers.thread_safe_list import ThreadSafeList


class IrrigationService:
    def __init__(self, controller_id, shared_data):
        self.logger = setup_logger(__name__)
        self.stop_event = threading.Event()
        self.controller_id = controller_id
        self.shared_data = shared_data
        self.schedules = []

    def start(self):
        self.logger.info("Starting irrigation service")
        self.thread = threading.Thread(target=self.check_for_irrigation)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self.logger.info("Stopped irrigation service")

    def restart(self):
        self.stop()
        self.start()

    def check_for_irrigation(self):
        while not self.stop_event.is_set():
            plants = Plants.get_plants_by_controller_id(self.controller_id)
            for plant in plants:
                if self.is_irrigation_needed(plant):
                    self.logger.info("Irrigation needed!")
                    # Here you would trigger the irrigation process
                else:
                    self.logger.info("No irrigation needed")
                self.stop_event.wait(1)

    def during_time(self, schedule):
        weekdays = schedule["weekdays"]
        startTime = schedule["startTime"]
        endTime = schedule["endTime"]
        # Get the current date and time
        now = datetime.now()

        # Check if today is one of the specified weekdays
        if now.strftime("%A") in weekdays:
            # Check if the current time is within the specified start and end times
            if startTime.time() <= now.time() <= endTime.time():
                return True
        return False

    def is_threshold_met(self, threshold):
        sensor_data = self.shared_data.get()
        for reading in sensor_data:
            # Check which sensor is a moisture sensor
            if Sensors.get_sensor_type(reading["sensorID"]) == "moisture":
                # Check if the moisture level is below the lower limit
                if reading["value"] < threshold:
                    self.logger.info(
                        f"Moisture level is below threshold: {reading['value']} < {threshold}"
                    )
                    return True
                else:
                    self.logger.info(
                        f"Moisture level is above threshold: {reading['value']} >= {threshold}"
                    )
                    return False

        self.logger.warning("No moisture sensor data found")
        return False

    def is_irrigation_needed(self, plant):
        plant_sensors = Plants.get_sensors_by_plant_id(plant["plantID"])

        schedules = Schedules.get_schedules_by_plant_id(plant["plantID"])
        for schedule in schedules:
            if self.during_time(schedule):
                if schedule["type"] == "threshold":
                    if self.is_threshold_met(schedule["threshold"]):
                        return True
                    self.logger.info("Threshold not met")
                elif schedule["type"] == "interval":
                    return True
        return False

    def process_sensor_data(self, sensor_data):
        # Here you would process the sensor data
        self.logger.info(f"Processing sensor data: {sensor_data}")

    def is_healthy(self):
        return self.thread.is_alive()
