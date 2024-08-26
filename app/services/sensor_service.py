import threading
import time
import json
from logging_config import setup_logger

class SensorService:
    def __init__(self, controller_id, redis_client, stop_event):
        self.logger = setup_logger(__name__)
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.stop_event = stop_event
        self.sensors = []
        self.thread = None


    def start(self):
        self.logger.info("Starting sensor service")
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()

    def stop(self):
        self.logger.info("Stopping sensor service")
        if self.thread:
            self.thread.join()

    def restart(self):
        self.stop()
        self.start()

    def update_data(self):
        while not self.stop_event.is_set():
            new_data = self.read_sensor_data()
            
            if new_data:  # Only push if there's data
                for data in new_data:
                    self.redis_client.rpush('sensor_data', json.dumps(data))
            self.stop_event.wait(1)

    def read_sensor_data(self):
        sensor_data = []
        for sensor in self.sensors:
            self.logger.info(f"Reading data from sensor {sensor.sensorID} with GPIO port {sensor.gpioPort}")
            # Simulated sensor reading. Replace with actual sensor reading logic
            sensor_data.append({
                "sensorID": sensor.sensorID, 
                "value": 1,  # Replace with actual sensor value
                "timestamp": time.time()
            })
        return sensor_data
    
    def update_sensors(self, new_sensors):
        self.sensors = new_sensors

    def is_healthy(self):
        return self.thread and self.thread.is_alive()
