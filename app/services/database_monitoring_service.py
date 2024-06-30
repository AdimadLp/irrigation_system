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
        self.stop_event = threading.Event()
        self.controller_id = controller_id
        self.irrigation_service = irrigation_service
        self.sensor_service = sensor_service
        self.is_running = False

    def start_monitoring(self):
        self.logger.info("Starting monitor service")
        self.is_running = True
        thread = threading.Thread(target=self.monitor_database)
        thread.daemon = True
        thread.start()

    def stop_monitoring(self):
        self.is_running = False

    def monitor_database(self):
        last_check_time = datetime.now()
        while self.is_running:
            # Assuming you want to check for new sensors added since the last check
            current_time = datetime.now()
            new_sensors = Sensors.get_new_sensors(since_date=last_check_time)
            if new_sensors:
                self.sensor_service.update_sensors(new_sensors)

            # Update last_check_time for the next iteration
            last_check_time = current_time

            time.sleep(10)  # Check every 10 seconds, adjust as needed

if __name__ == "__main__":
    irrigation_service = IrrigationService()
    sensor_service = SensorService()
    monitoring_service = DatabaseMonitoringService("controller_id_example", irrigation_service, sensor_service)
    monitoring_service.start_monitoring()