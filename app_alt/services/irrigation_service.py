import threading
from datetime import datetime
from logging_config import setup_logger

class IrrigationService:
    def __init__(self, controller_id, redis_client, stop_event):
        self.logger = setup_logger(__name__)
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.stop_event = stop_event
        self.plants = []
        self.schedules = []
        self.sensor_types = {}
        self.thread = None

    def start(self):
        self.logger.info("Starting irrigation service")
        self.thread = threading.Thread(target=self.check_for_irrigation)
        self.thread.start()

    def stop(self):
        self.logger.info("Stopping irrigation service")
        if self.thread:
            self.thread.join()

    def restart(self):
        self.stop()
        self.start()

    def check_for_irrigation(self):
        while not self.stop_event.is_set():
            for plant in self.plants:
                if self.is_irrigation_needed(plant):
                    self.logger.info(f"Irrigation needed for plant {plant['plantID']}!")
                    # TODO: Trigger irrigation process here
                else:
                    self.logger.debug(f"No irrigation needed for plant {plant['plantID']}")
                self.stop_event.wait(1)

    def during_time(self, schedule):
        now = datetime.now()
        return (now.strftime("%A") in schedule['weekdays'] and
                schedule['startTime'].time() <= now.time() <= schedule['endTime'].time())


    def is_threshold_met(self, threshold):
        sensor_data = eval(self.redis_client.get('sensor_data') or '[]')
        for reading in sensor_data:
            sensor_type = self.sensor_types.get(reading['sensorID'])
            if sensor_type == 'moisture':
                if reading['value'] < threshold:
                    self.logger.info(f"Moisture level is below threshold: {reading['value']} < {threshold}")
                    return True
                else:
                    self.logger.info(f"Moisture level is above threshold: {reading['value']} >= {threshold}")
                    return False
        self.logger.warning("No moisture sensor data found")
        return False

    def is_irrigation_needed(self, plant):
        plant_schedules = [s for s in self.schedules if s['plantID'] == plant['plantID']]
        for schedule in plant_schedules:
            if self.during_time(schedule):
                if schedule['type'] == 'threshold':
                    # TODO: return self.is_threshold_met(schedule['threshold'])
                    return True
                elif schedule['type'] == 'interval':
                    return True
        return False

    def update_plants(self, new_plants):
        self.plants = new_plants

    def update_schedules(self, new_schedules):
        self.schedules = new_schedules

    def update_sensor_types(self, new_sensor_types):
        self.sensor_types = new_sensor_types

    def is_healthy(self):
        return self.thread and self.thread.is_alive()
