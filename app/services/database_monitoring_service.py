import threading
import time
import logging
from datetime import datetime
from app.services.irrigation_service import IrrigationService
from app.services.sensor_service import SensorService
from database.models import Plants
from database.models import Sensors
from database.models import Pumps
from database.models import Schedules


class DatabaseMonitoringService:
    def __init__(self, controller_id, irrigation_service, sensor_service):
        self.logger = logging.getLogger(__name__)
        self.controller_id = controller_id
        self.irrigation_service = irrigation_service
        self.sensor_service = sensor_service
        self.is_running = False
        self.plants = []

    def start_monitoring(self):
        self.logger.info("Starting monitor service")
        self.is_running = True
        thread = threading.Thread(target=self.monitor_database)
        thread.daemon = True
        thread.start()

    def stop_monitoring(self):
        self.is_running = False

    def monitor_database(self):
        while self.is_running:
            self.check_for_new_plants()
            self.check_for_new_sensors()
            self.check_for_new_schedules()

            time.sleep(10)  # Check every 10 seconds, adjust as needed

    def check_for_new_plants(self):
        if self.plants:
            current_plants = set(plant.plantID for plant in self.plants)
        else:
            current_plants = set()
        new_plants_list = Plants.get_plants_by_controller_id(self.controller_id)
        new_plants = set(plant.plantID for plant in new_plants_list)

        if current_plants != new_plants:
            self.logger.info("New plant(s) found. Updating plant list.")
            self.plants = new_plants_list

    def check_for_new_sensors(self):
        if self.sensor_service.sensors:
            current_sensors = set(
                sensor.sensorID for sensor in self.sensor_service.sensors
            )
        else:
            current_sensors = set()
        new_sensors_list = Sensors.get_all_sensors_by_controller(self.controller_id)
        new_sensors = set(sensor.sensorID for sensor in new_sensors_list)

        if current_sensors != new_sensors:
            self.logger.info("New sensor(s) found. Updating sensor list.")
            self.sensor_service.sensors = new_sensors_list

    def check_for_new_schedules(self):
        if self.irrigation_service.schedules:
            current_schedules = set(
                schedule.scheduleID for schedule in self.irrigation_service.schedules
            )
        else:
            current_schedules = set()
        new_schedules_list = Schedules.get_schedules_by_plant_id(self.controller_id)
        new_schedules = set(schedule.scheduleID for schedule in new_schedules_list)

        if current_schedules != new_schedules:
            self.logger.info("New schedule(s) found. Updating schedule list.")
            self.irrigation_service.schedules = new_schedules_list


if __name__ == "__main__":
    irrigation_service = IrrigationService()
    sensor_service = SensorService()
    monitoring_service = DatabaseMonitoringService(
        "1", irrigation_service, sensor_service
    )
    monitoring_service.start_monitoring()
