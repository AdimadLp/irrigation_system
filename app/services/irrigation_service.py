import logging
import threading
import time
from database.models import Plants
from database.models import Pumps
from database.models import Schedules
from database.models import WateringLogs
from services.sensor_service import SensorService

class IrrigationService:
    def __init__(self, controller_id):
        self.logger = logging.getLogger(__name__)
        self.stop_event = threading.Event()
        self.controller_id = controller_id 

    def start(self):
        self.logger.info("Starting irrigation service")
        self.thread = threading.Thread(target=self.check_for_irrigation)
        self.thread.start()
    
    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self.logger.info("Stopped irrigation service")

    def check_for_irrigation(self):
        while True:
            if self.stop_event.is_set():
                break
            if self.is_irrigation_needed():
                self.logger.info("Irrigation needed!")
                # Here you would trigger the irrigation process
            time.sleep(1)

    def is_schedule_active(self, schedule):
        # Implement logic to check if the schedule is active
        # For this example, we'll just return True
        return True
    
    def is_threshold_met(self, lower_moisture_limit, sensor_data):
        # Implement logic to check if the threshold is met
        # For this example, we'll just return True
        self.logger.info(f"Checking if threshold is met. Lower limit: {lower_moisture_limit}, Sensor data: {sensor_data}")
        return True

    def is_irrigation_needed(self):
        plants = Plants.get_plants_by_controller_id(self.controller_id)
        for plant in plants:
            schedules = Schedules.get_schedules_by_plant_id(plant["plantID"])
            for schedule in schedules:
                if self.is_schedule_active(schedule):
                    sensor_data = SensorService.get_data()
                    if self.is_threshold_met(plant["lowerMoistureLimit"], sensor_data):
                        return True

    def process_sensor_data(self, sensor_data):
        # Here you would process the sensor data
        self.logger.info(f"Processing sensor data: {sensor_data}")


    def is_healthy(self):
            # Implement your health check logic here.
            # For example, you might check if the sensor is still responsive.
            # For this example, we'll just return True.
            return True