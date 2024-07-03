import logging
from services.irrigation_service import IrrigationService
from services.sensor_service import SensorService
from services.database_monitoring_service import DatabaseMonitoringService
import time
import threading
from helpers.thread_safe_list import ThreadSafeList


# Configure logging to write to a file, include timestamps, and include the logger's name
logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main():
    controller_id = None
    try:
        from database.models import IrrigationControllers

        controller_id = IrrigationControllers.check_and_save_controller()
    except Exception as e:
        logging.error(f"Error initializing controller: {e}")

    shared_sensor_data = ThreadSafeList()

    sensor_service = SensorService(controller_id, shared_sensor_data)
    sensor_service.start()

    irrigation_service = IrrigationService(controller_id, shared_sensor_data)
    irrigation_service.start()

    monitoring_service = DatabaseMonitoringService(
        controller_id, irrigation_service, sensor_service
    )
    monitoring_service.start_monitoring()

    try:
        while True:
            # Check the health of the services every second
            if not sensor_service.is_healthy() or not irrigation_service.is_healthy():
                if not sensor_service.is_healthy():
                    sensor_service.logger.warning("Sensor service is not healthy!")
                    sensor_service.restart()
                if not irrigation_service.is_healthy():
                    irrigation_service.logger.warning(
                        "Irrigation service is not healthy!"
                    )
                    irrigation_service.restart()

            time.sleep(1)
    except KeyboardInterrupt:
        sensor_service.stop()
        irrigation_service.stop()


if __name__ == "__main__":
    main()
