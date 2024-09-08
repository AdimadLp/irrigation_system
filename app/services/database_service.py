import json
import threading
import time
from redis import WatchError
from mongoengine import get_db
from pymongo.errors import NetworkTimeout, ConnectionFailure
from mongoengine.errors import OperationError
from logging_config import setup_logger
from database.models import Plants, Sensors, Schedules, RealtimeSensorData
from database import connection
import socket


class DatabaseService:
    def __init__(
        self,
        controller_id,
        redis_client,
        sensor_service,
        irrigation_service,
        stop_event,
    ):
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.mongo_client = (
            get_db().client
        )  # Get the MongoDB client from the connection
        self.sensor_service = sensor_service
        self.irrigation_service = irrigation_service
        self.stop_event = stop_event
        self.logger = setup_logger(__name__)
        self.batch_size = 100
        self.thread = None
        self.last_check_time = 0
        self.healthy = True
        self.exception_count = 0
        self.exception_threshold = 5
        self.reset_time = 60
        self.retry_interval = 10
        self.last_exception_time = 0

    def start(self):
        self.logger.info("Starting database service")
        self.thread = threading.Thread(target=self.run)
        self.healthy = True
        self.thread.start()

    def stop(self):
        self.logger.info("Stopping database service")
        self.stop_event.set()
        if self.thread:
            self.thread.join()

    def restart(self):
        self.logger.info("Restarting database service due to repeated errors")
        self.stop()
        self.start()
        self.reset_exception_count()

    def run(self):
        while not self.stop_event.is_set():
            current_time = time.time()

            if current_time - self.last_exception_time >= self.reset_time:
                self.reset_exception_count()

            # Check for new data every 10 seconds
            if current_time - self.last_check_time >= 10:
                self.check_for_new_data()
                self.last_check_time = current_time

            self.save_sensor_data()

            self.stop_event.wait(1)  # Wait for 1 second or until stop_event is set

    def save_sensor_data(self):
        try:
            with self.redis_client.pipeline() as pipe:
                # Fetch the data to be processed
                sensor_data_list = self.redis_client.lrange(
                    "sensor_data", 0, self.batch_size - 1
                )

                if not sensor_data_list:
                    return

                # Determine the actual batch size
                actual_batch_size = len(sensor_data_list)

                # Watch the key
                pipe.watch("sensor_data")

                # Process the data
                success = self.process_sensor_data_batch(sensor_data_list)

                if success and actual_batch_size > 0:
                    pipe.multi()
                    pipe.ltrim(
                        "sensor_data", actual_batch_size, -1
                    )  # Remove processed items
                    pipe.execute()
                    self.logger.info(f"Removed {actual_batch_size} items from Redis")
                elif not success:
                    self.logger.warning(
                        "Transaction failed. Data remains in Redis for retry."
                    )

        except WatchError:
            self.logger.warning("Concurrent modification detected, verifying data...")
            # Verify that the data hasn't changed
            current_data_list = self.redis_client.lrange(
                "sensor_data", 0, actual_batch_size - 1
            )
            if sensor_data_list == current_data_list:
                self.logger.info(
                    "Data hasn't changed, ignoring WatchError and proceeding."
                )
                with self.redis_client.pipeline() as pipe:
                    pipe.multi()
                    pipe.ltrim(
                        "sensor_data", actual_batch_size, -1
                    )  # Remove processed items
                    pipe.execute()
                    self.logger.info(f"Removed {actual_batch_size} items from Redis")
            else:
                self.logger.warning("Data changed")
                self.increment_exception_count()

    def process_sensor_data_batch(self, sensor_data_list):
        try:
            with self.mongo_client.start_session() as session:
                with session.start_transaction(max_commit_time_ms=5000):
                    processed_count = self._process_sensor_data(
                        sensor_data_list, session
                    )
                    session.commit_transaction()
                    self.logger.info(f"Successfully processed {processed_count} items")
                    if processed_count < len(sensor_data_list):
                        self.logger.warning(
                            f"{len(sensor_data_list) - processed_count} items failed to process and will be deleted."
                        )
                    return True

        except (NetworkTimeout, ConnectionFailure, OperationError) as e:
            self.logger.error(f"Network error: {e}")
            self.wait_for_network()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.increment_exception_count()
            return False

    def _process_sensor_data(self, sensor_data_list, session):
        sensor_data_json_list = []
        for sensor_data in sensor_data_list:
            try:
                sensor_data_json_list.append(json.loads(sensor_data.decode("utf-8")))
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON for item: {sensor_data}")
                continue

        Sensors.save_sensor_data(sensor_data_json_list, session=session)
        return len(sensor_data_json_list)

    def wait_for_network(self):
        """Warte, bis eine Internetverbindung besteht, aber überprüfe dabei regelmäßig das Stop-Event."""
        self.logger.info("Waiting for network connection to be restored...")

        # Solange keine Internetverbindung verfügbar ist, aber das Stop-Event nicht gesetzt wurde, wird gewartet.
        while not self.network_is_available():
            if self.stop_event.wait(self.retry_interval):
                # Falls das Stop-Event während der Wartezeit ausgelöst wird, beende die Schleife.
                self.logger.info("Stop event received. Exiting wait_for_network.")
                return

        self.logger.info("Network connection restored. Resuming operations.")

    def network_is_available(self):
        """Überprüft, ob eine Internetverbindung besteht."""
        try:
            # Teste die Internetverbindung über Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False

    def increment_exception_count(self):
        current_time = time.time()
        self.exception_count += 1
        self.last_exception_time = current_time

        if self.exception_count >= self.exception_threshold:
            self.logger.error(
                "Too many errors within a short period. Restarting the thread."
            )
            self.healthy = False

    def reset_exception_count(self):
        self.exception_count = 0
        self.last_exception_time = 0

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
        sensor_data = self.redis_client.lrange("sensor_data", 0, -1)
        self.logger.debug("Redis 'sensor_data' content:")
        for i, data in enumerate(sensor_data):
            self.logger.debug(f"  Item {i}: {data}")

    def is_healthy(self):
        return self.healthy and self.thread.is_alive() if self.thread else False

    # TODO: Implement a exception count mechanism to mark the service as unhealthy
