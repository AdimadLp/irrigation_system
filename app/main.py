import signal
import threading
import redis
from logging_config import setup_logger
from services.irrigation_service import IrrigationService
from services.sensor_service import SensorService
from services.database_service import DatabaseService
from database.models import IrrigationControllers

logger = setup_logger("main")

class MainController:
    def __init__(self):
        self.controller_id = self.initialize_controller()
        self.stop_event = threading.Event()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.sensor_service = SensorService(self.controller_id, self.redis_client, self.stop_event)
        self.irrigation_service = IrrigationService(self.controller_id, self.redis_client, self.stop_event)
        self.database_service = DatabaseService(
            self.controller_id, self.redis_client, self.sensor_service, self.irrigation_service, self.stop_event
        )

    def initialize_controller(self):
        return IrrigationControllers.check_and_save_controller()

    def start_services(self):
        logger.info("Starting all services...")
        self.sensor_service.start()
        self.irrigation_service.start()
        self.database_service.start()

    def stop_services(self):
        logger.info("Stopping all services...")
        self.stop_event.set()  # Signal all services to stop
        self.sensor_service.stop()
        self.irrigation_service.stop()
        self.database_service.stop()

    def check_service_health(self):
        if not self.sensor_service.is_healthy():
            logger.warning("Sensor service unhealthy. Attempting restart.")
            self.sensor_service.restart()
        if not self.irrigation_service.is_healthy():
            logger.warning("Irrigation service unhealthy. Attempting restart.")
            self.irrigation_service.restart()
        if not self.database_service.is_healthy():
            logger.warning("Monitoring service unhealthy. Attempting restart.")
            self.database_service.restart()

    def handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}. Initiating shutdown...")
        self.stop_event.set()

    def run(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        self.start_services()

        try:
            while not self.stop_event.is_set():
                self.check_service_health()
                self.stop_event.wait(10)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop_services()
            logger.info("All services stopped. Exiting.")

def main():
    try:
        controller = MainController()
        controller.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
    finally:
        logger.info("Program terminated.")

if __name__ == "__main__":
    main()