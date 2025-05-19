import asyncio
from server_app.logging_config import setup_logger
from server_app.database.models import (
    Plants,
    Sensors,
    Schedules,
    Pumps,
    RealtimeSensorData,
    Logs,
)
import time


class DatabaseService:
    def __init__(
        self,
        controller_id,
        sensor_service,
        irrigation_service,
        stop_event,
    ):
        self.controller_id = controller_id
        self.sensor_service = sensor_service
        self.irrigation_service = irrigation_service
        self.stop_event = stop_event
        self.logger = setup_logger(__name__)
        self.batch_size = 100
        self.healthy = asyncio.Event()
        self.healthy.set()
        self.exception_count = 0
        self.exception_threshold = 5
        self.reset_time = 60
        self.network_check_interval = 1
        self.network_available = asyncio.Event()
        self.network_available.set()
        self.last_check_time = 0

        # In-memory data structures
        self.plants_cache = []  # Stores list of plant dicts
        self.watering_logs_queue = []  # Stores list of watering log dicts
        self.sensor_data_queue = []  # Stores list of sensor data JSON strings
        self.logs_queue = []  # Stores list of log JSON strings
        self.data_lock = asyncio.Lock()  # To protect concurrent access to queues

    async def start(self):
        self.logger.info("Starting database service")
        self.healthy.set()
        await self.initialize_plants()
        await self.run()

    async def stop(self):
        self.logger.info("Stopping database service")
        self.stop_event.set()

    async def initialize_plants(self):
        try:
            self.logger.info("Initializing plants")
            new_plants = await Plants.get_plants_by_controller_id(self.controller_id)

            if new_plants:
                self.logger.info("Plants in mongodb found, updating internal cache")
                async with self.data_lock:
                    self.plants_cache = new_plants
                await self.irrigation_service.update_plants(new_plants)
            else:
                self.logger.warning(
                    f"No plants found in MongoDB for controller {self.controller_id}. Clearing internal cache."
                )
                async with self.data_lock:
                    self.plants_cache = []
                await self.irrigation_service.update_plants([])

        except Exception as e:
            self.logger.error(f"Error initializing plants: {str(e)}")
            self.healthy.clear()

    async def run(self):
        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Check if network is available
                if not await self.network_is_available():
                    self.logger.warning(
                        "Network not available, skipping this iteration"
                    )
                    await asyncio.sleep(1)
                    continue

                # Check for new data every 10 seconds
                if current_time - self.last_check_time >= 10:
                    await self.check_for_new_data()
                    self.last_check_time = current_time

                await self.save_sensor_data()
                await self.save_watering_logs()
                await asyncio.sleep(1)
            except asyncio.TimeoutError:
                pass

    async def network_is_available(self):
        try:
            # Try to connect to a known IP address (e.g., Google's DNS server)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("8.8.8.8", 53), timeout=5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
            return False
        except Exception as e:
            self.logger.error(f"Error checking network availability: {e}")
            return False

    async def save_watering_logs(self):
        try:
            async with self.data_lock:
                if not self.watering_logs_queue:
                    return
                logs_to_process = list(self.watering_logs_queue)

            if not logs_to_process:
                return

            watering_data = []
            for log_data in logs_to_process:
                plant_id = log_data["plantID"]
                timestamp = log_data["timestamp"]
                watering_data.append((plant_id, timestamp))

            # Bulk update watering history for plants
            updated_count = await Plants.bulk_update_watering_history(watering_data)
            self.logger.info(f"Updated watering history for {updated_count} plants")

            async with self.data_lock:
                self.watering_logs_queue = self.watering_logs_queue[
                    len(logs_to_process) :
                ]

            self.logger.info(f"Processed {len(logs_to_process)} watering logs")

        except Exception as e:
            self.logger.error(f"Error processing watering logs: {str(e)}")

    async def save_sensor_data(self):
        try:
            sensor_data_list_batch = []
            async with self.data_lock:
                if not self.sensor_data_queue:
                    return {}
                count_to_process = min(len(self.sensor_data_queue), self.batch_size)
                sensor_data_list_batch = self.sensor_data_queue[:count_to_process]

            if not sensor_data_list_batch:
                return {}

            success, latest_readings = await Sensors.process_sensor_data_batch(
                sensor_data_list_batch
            )
            await RealtimeSensorData.update_realtime_sensor_data(latest_readings)

            if success:
                async with self.data_lock:
                    self.sensor_data_queue = self.sensor_data_queue[
                        len(sensor_data_list_batch) :
                    ]
                self.logger.info(
                    f"Removed {len(sensor_data_list_batch)} sensor data items from queue"
                )
            else:
                self.logger.warning(
                    "Transaction failed. Data remains in queue for retry."
                )

            """
        except (NetworkTimeout, ConnectionFailure) as e:
            self.logger.error(f"Network error: {e}")
            self.network_available.clear()
            return False, {}
            """
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.increment_exception_count()
            return False, {}

    async def save_logs(self):
        try:
            logs_batch = []
            async with self.data_lock:
                if not self.logs_queue:
                    return
                count_to_process = min(len(self.logs_queue), self.batch_size)
                logs_batch = self.logs_queue[:count_to_process]

            if not logs_batch:
                return

            inserted_count = await Logs.process_logs(logs_batch)

            async with self.data_lock:
                self.logs_queue = self.logs_queue[inserted_count:]
            self.logger.info(f"Inserted {inserted_count} logs into the database")

        except Exception as e:
            self.logger.error(f"Error processing logs: {str(e)}")

    def increment_exception_count(self):
        self.exception_count += 1
        if self.exception_count >= self.exception_threshold:
            self.logger.error(
                "Too many errors within a short period. Marking as unhealthy."
            )
            self.healthy.clear()

    def reset_exception_count(self):
        self.exception_count = 0
        self.healthy.set()

    async def check_for_new_data(self):
        self.logger.info("Checking for new data...")
        await asyncio.gather(
            self.check_for_new_plants(),
            self.check_for_new_sensors(),
            self.check_for_new_schedules(),
            self.check_for_new_pumps(),
        )
        self.logger.info("Finished checking for new data.")

    async def check_for_new_plants(self):
        plants = await Plants.get_plants_by_controller_id(self.controller_id)
        if not plants:
            self.logger.warning("No plants found for this controller.")
            async with self.data_lock:
                self.plants_cache = []
        else:
            async with self.data_lock:
                self.plants_cache = plants
        await self.irrigation_service.update_plants(plants if plants else [])

    async def check_for_new_sensors(self):
        sensors = await Sensors.get_sensors_by_controller(self.controller_id)
        if not sensors:
            self.logger.warning("No sensors found for this controller.")
        else:
            sensor_types = {sensor["sensorID"]: sensor["type"] for sensor in sensors}
            await self.sensor_service.update_sensors(sensors)
            await self.irrigation_service.update_sensor_types(sensor_types)

    async def check_for_new_schedules(self):
        schedules = await Schedules.get_schedules_by_controller(self.controller_id)
        if not schedules:
            self.logger.warning("No schedules found for this controller.")
        await self.irrigation_service.update_schedules(schedules)

    async def check_for_new_pumps(self):
        pumps = await Pumps.get_pumps_by_controller(self.controller_id)
        if not pumps:
            self.logger.warning("No pumps found for this controller.")
        await self.irrigation_service.update_pumps(pumps)

    async def is_healthy(self):
        return self.healthy.is_set()

    async def wait_until_healthy(self):
        await self.healthy.wait()

    async def add_watering_log(self, log_data: dict):
        async with self.data_lock:
            self.watering_logs_queue.append(log_data)
        self.logger.debug(f"Added watering log to queue: {log_data}")

    async def add_sensor_data_item(self, sensor_data_json: str):
        async with self.data_lock:
            self.sensor_data_queue.append(sensor_data_json)
        self.logger.debug(f"Added sensor data to queue: {sensor_data_json[:50]}...")

    async def add_log_item(self, log_json: str):
        async with self.data_lock:
            self.logs_queue.append(log_json)
        self.logger.debug(f"Added general log to queue: {log_json[:50]}...")

    async def get_cached_plants(self):
        async with self.data_lock:
            return list(self.plants_cache)
