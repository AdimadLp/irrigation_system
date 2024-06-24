import logging
from services.irrigation_service import IrrigationService
from services.sensor_service import SensorService
import time

# Configure logging to write to a file, include timestamps, and include the logger's name
logging.basicConfig(
    filename='app.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    sensor_service = SensorService()
    sensor_service.start()

    irrigation_service = IrrigationService()
    irrigation_service.start()

    try:
        while True:
            # Check the health of the services every second
            if not sensor_service.is_healthy() or not irrigation_service.is_healthy():
                if not sensor_service.is_healthy():
                    sensor_service.logger.warning("Sensor service is not healthy!")
                    sensor_service.restart()
                if not irrigation_service.is_healthy():
                    irrigation_service.logger.warning("Irrigation service is not healthy!")
                    irrigation_service.restart()
            else:
                # Process sensor data every second
                sensor_data = sensor_service.get_data()
                irrigation_service.process_sensor_data(sensor_data)

            time.sleep(1)
    except KeyboardInterrupt:
        sensor_service.stop()
        irrigation_service.stop()


if __name__ == "__main__":
    main()