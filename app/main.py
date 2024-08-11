from logging_config import setup_logger
from services.irrigation_service import IrrigationService
from services.sensor_service import SensorService
from services.database_monitoring_service import DatabaseMonitoringService
import time
from helpers.thread_safe_list import ThreadSafeList

logger = setup_logger("main")


def main():
    controller_id = None
    try:
        from database.models import IrrigationControllers

        controller_id = IrrigationControllers.check_and_save_controller()
    except Exception as e:
        logger.error(f"Error initializing controller: {e}")

    shared_sensor_data = ThreadSafeList()

    sensor_service = SensorService(controller_id, shared_sensor_data)
    sensor_service.start()

    irrigation_service = IrrigationService(controller_id, shared_sensor_data)
    irrigation_service.start()

    monitoring_service = DatabaseMonitoringService(
        controller_id, irrigation_service, sensor_service
    )
    monitoring_service.start()

    try:
        while True:
            # Check the health of the services every second
            if (
                not sensor_service.is_healthy()
                or not irrigation_service.is_healthy()
                or not monitoring_service.is_healthy()
            ):
                if not sensor_service.is_healthy():
                    sensor_service.logger.error("Sensor service is not healthy!")
                    sensor_service.restart()
                if not irrigation_service.is_healthy():
                    irrigation_service.logger.error(
                        "Irrigation service is not healthy!"
                    )
                    irrigation_service.restart()
                if not monitoring_service.is_healthy():
                    monitoring_service.logger.error(
                        "Monitoring service is not healthy!"
                    )
                    monitoring_service.restart

            time.sleep(1)
    except KeyboardInterrupt:
        sensor_service.stop()
        irrigation_service.stop()


if __name__ == "__main__":
    main()
