import logging
import threading
import time

class IrrigationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stop_event = threading.Event()

    def start(self):
        self.logger.info("Starting sensor service")
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()
    
    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self.logger.info("Stopped sensor service")

    def update_data(self):
        while not self.stop_event.is_set():
            new_data = self.read_sensor_data()
            with self.data_lock:
                self.data.append(new_data)
            time.sleep(1)  # Sleep for a while to simulate reading sensor data

    def process_sensor_data(self, sensor_data):
        # Here you would process the sensor data
        self.logger.info(f"Processing sensor data: {sensor_data}")


    def is_healthy(self):
            # Implement your health check logic here.
            # For example, you might check if the sensor is still responsive.
            # For this example, we'll just return True.
            return True