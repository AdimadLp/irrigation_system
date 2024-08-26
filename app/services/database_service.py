import json
import threading
import time
from redis import WatchError
from mongoengine import get_db
from logging_config import setup_logger
from database.models import Plants, Sensors, Schedules, RealtimeSensorData
from database import connection  # Import the connection module

class DatabaseService:
    def __init__(self, controller_id, redis_client, sensor_service, irrigation_service, stop_event):
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.mongo_client = get_db().client  # Get the MongoDB client from the connection
        self.sensor_service = sensor_service
        self.irrigation_service = irrigation_service
        self.stop_event = stop_event
        self.logger = setup_logger(__name__)
        self.max_retries = 5
        self.retry_delay = 5  # Initial delay in seconds
        self.failure_threshold = 10  # Number of consecutive failures before backing off
        self.thread = None
        self.last_check_time = 0

    def start(self):
        self.logger.info("Starting database service")
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.logger.info("Stopping database service")
        self.stop_event.set()
        if self.thread:
            self.thread.join()

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        while not self.stop_event.is_set():
            current_time = time.time()
            
            # Check for new data every 10 seconds
            if current_time - self.last_check_time >= 10:
                self.check_for_new_data()
                self.last_check_time = current_time

            self.save_sensor_data()
            
            self.print_redis_content()  # Debug: Print Redis content
            self.stop_event.wait(1)  # Wait for 1 second or until stop_event is set

    def save_sensor_data(self):
        consecutive_failures = 0
        while not self.stop_event.is_set():
            if consecutive_failures >= self.failure_threshold:
                self.logger.warning(f"Hit failure threshold. Backing off for {self.retry_delay} seconds.")
                if self.stop_event.wait(self.retry_delay):
                    return
                consecutive_failures = 0

            try:
                processed = self.process_batch()
                if processed:
                    consecutive_failures = 0
                else:
                    break  # No more data to process, exit the loop
            except Exception as e:
                self.logger.error(f"Error in save_sensor_data: {e}")
                consecutive_failures += 1

    def process_batch(self):
        with self.redis_client.pipeline() as pipe:
            try:
                pipe.watch('sensor_data')
                pipe.multi()
                pipe.lrange('sensor_data', 0, 99)
                results = pipe.execute()
                sensor_data_list = results[0]

                if not sensor_data_list:
                    return False  # No data to process

                successful_indices = self.process_sensor_data_batch(sensor_data_list)

                # Remove only the successfully processed items
                if successful_indices:
                    print(f"Removing {len(successful_indices)} items from Redis")
                    pipe.multi()
                    for index in sorted(successful_indices, reverse=True):
                        pipe.lset('sensor_data', index, '__DUMMY__')
                    pipe.lrem('sensor_data', 0, '__DUMMY__')
                    pipe.execute()

                return True

            except WatchError:
                self.logger.warning("Concurrent modification detected, retrying...")
                return False

    def process_sensor_data_batch(self, sensor_data_list):
        successful_indices = []
        with self.mongo_client.start_session() as session:
            with session.start_transaction():
                try:
                    for index, sensor_data in enumerate(sensor_data_list):
                        try:
                            sensor_data_json = json.loads(sensor_data.decode('utf-8'))
                            
                            for item in sensor_data_json:  # sensor_data_json is a list of sensor readings
                                # Save sensor data blocks the execution of the thread until the data is saved
                                Sensors.save_sensor_data([item], session=session)
                                # TODO: Prevent blocking the thread by using mongodb timeouts and error handling 

                            #RealtimeSensorData.update_sensor_data(sensor_data_json, session=session)
                            successful_indices.append(index)
                        except json.JSONDecodeError:
                            self.logger.error(f"Failed to parse JSON for item at index {index}")
                        except Exception as e:
                            self.logger.error(f"Error processing sensor data at index {index}: {e}")

                    if successful_indices:
                        session.commit_transaction()
                        self.logger.info(f"Successfully processed {len(successful_indices)} out of {len(sensor_data_list)} items")
                    else:
                        session.abort_transaction()
                        self.logger.warning("No items were successfully processed in this batch")

                except Exception as e:
                    session.abort_transaction()
                    self.logger.error(f"Transaction failed: {e}")
                    return []

        return successful_indices

    def check_for_new_data(self):
        self.logger.info("Checking for new data...")
        self.check_for_new_plants()
        self.check_for_new_sensors()
        self.check_for_new_schedules()
        self.logger.info("Finished checking for new data.")

    def check_for_new_plants(self):
        plants = Plants.get_plants_by_controller_id(self.controller_id)
        if not plants:
            self.logger.warning("No plants found for this controller.")
        self.irrigation_service.update_plants(plants)

    def check_for_new_sensors(self):
        sensors = Sensors.get_sensors_by_controller(self.controller_id)
        if not sensors:
            self.logger.warning("No sensors found for this controller.")
        sensor_types = {sensor.sensorID: sensor.type for sensor in sensors}
        self.sensor_service.update_sensors(sensors)
        self.irrigation_service.update_sensor_types(sensor_types)

    def check_for_new_schedules(self):
        schedules = Schedules.get_schedules_by_controller(self.controller_id)
        if not schedules:
            self.logger.warning("No schedules found for this controller.")
        self.irrigation_service.update_schedules(schedules)

    def print_redis_content(self):
        sensor_data = self.redis_client.lrange('sensor_data', 0, -1)
        self.logger.debug("Redis 'sensor_data' content:")
        for i, data in enumerate(sensor_data):
            self.logger.debug(f"  Item {i}: {data}")

    def is_healthy(self):
        return self.thread.is_alive() if self.thread else False