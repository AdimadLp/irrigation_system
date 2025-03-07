import asyncio
from app.logging_config import setup_logger
from app.database.models import (
    Plants,
    Sensors,
    Schedules,
    Pumps,
    RealtimeSensorData,
    Logs,
)
import time
from google.cloud.firestore_v1.base_query import FieldFilter
import json


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

        # New: Snapshot listener unsubscribe handles
        self.plant_listener = None
        self.sensor_listener = None
        self.schedule_listener = None
        self.pump_listener = None

    async def start(self):
        self.logger.info("Starting database service")
        self.healthy.set()
        self.loop = asyncio.get_running_loop()  # Capture main loop
        await self.initialize_plants()
        # Register snapshot listeners for all data types
        self.register_plants_listener()
        self.register_sensors_listener()
        self.register_schedules_listener()
        self.register_pumps_listener()
        await self.run()

    async def stop(self):
        self.logger.info("Stopping database service")
        self.stop_event.set()
        # Unsubscribe snapshot listeners if they exist.
        if self.plant_listener:
            self.plant_listener.unsubscribe()
            self.logger.info("Plant snapshot listener unsubscribed.")
        if self.sensor_listener:
            self.sensor_listener.unsubscribe()
            self.logger.info("Sensor snapshot listener unsubscribed.")
        if self.schedule_listener:
            self.schedule_listener.unsubscribe()
            self.logger.info("Schedule snapshot listener unsubscribed.")
        if self.pump_listener:
            self.pump_listener.unsubscribe()
            self.logger.info("Pump snapshot listener unsubscribed.")

    async def initialize_plants(self):
        try:
            self.logger.info("Initializing plants")
            plants_json = await self.redis_client.get("all_plants")
            redis_plants = json.loads(plants_json) if plants_json else None

            new_plants = Plants.get_plants_by_controller_id(self.controller_id)

            if new_plants:
                self.logger.info("Plants in mongodb found, updating Redis")
                await self.redis_client.set("all_plants", json.dumps(new_plants))
                await self.irrigation_service.update_plants(new_plants)
            elif redis_plants:
                self.logger.info("No plants in mongodb found, using plants from Redis")
                await self.irrigation_service.update_plants(redis_plants)
            else:
                self.logger.warning("No plants found in Redis or mongodb")
        except Exception as e:
            self.logger.error(f"Error initializing plants: {str(e)}")
            self.healthy.clear()

    async def run(self):
        while not self.stop_event.is_set():
            try:
                # Check if network is available
                if not await self.network_is_available():
                    self.logger.warning(
                        "Network not available, skipping this iteration"
                    )
                    await asyncio.sleep(1)
                    continue

                # Since we are using snapshot listeners now, we no longer need to poll for new data.
                # await self.check_for_new_data()

                await self.save_sensor_data()
                await self.save_watering_logs()
                # await self.save_logs()
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
            watering_logs = await self.redis_client.lrange("watering_logs", 0, -1)
            if not watering_logs:
                return

            watering_data = []
            for log in watering_logs:
                log_data = json.loads(log)
                plant_id = log_data["plantID"]
                timestamp = log_data["timestamp"]
                watering_data.append((plant_id, timestamp))

            # Bulk update watering history for plants
            updated_count = await Plants.bulk_update_watering_history(watering_data)
            self.logger.info(f"Updated watering history for {updated_count} plants")

            # Remove processed logs from Redis
            await self.redis_client.ltrim("watering_logs", len(watering_logs), -1)
            self.logger.info(f"Processed {len(watering_logs)} watering logs")

        except Exception as e:
            self.logger.error(f"Error processing watering logs: {str(e)}")

    async def save_sensor_data(self):
        try:
            sensor_data_list = await self.redis_client.lrange(
                "sensor_data", 0, self.batch_size - 1
            )

            if not sensor_data_list:
                return {}

            success, latest_readings = await Sensors.process_sensor_data_batch(
                sensor_data_list
            )
            await RealtimeSensorData.update_realtime_sensor_data(latest_readings)

            if success:
                await self.redis_client.ltrim("sensor_data", len(sensor_data_list), -1)
                self.logger.info(f"Removed {len(sensor_data_list)} items from Redis")
            else:
                self.logger.warning(
                    "Transaction failed. Data remains in Redis for retry."
                )

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.increment_exception_count()
            return False, {}

    async def save_logs(self):
        try:
            logs = await self.redis_client.lrange("logs", 0, self.batch_size - 1)
            if not logs:
                return

            inserted_count = await Logs.process_logs(logs)
            await self.redis_client.ltrim("logs", inserted_count, -1)
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
        plants = Plants.get_plants_by_controller_id(self.controller_id)
        if not plants:
            self.logger.warning("No plants found for this controller.")
        await self.irrigation_service.update_plants(plants)

    async def check_for_new_sensors(self):
        sensors = Sensors.get_sensors_by_controller(self.controller_id)
        if not sensors:
            self.logger.warning("No sensors found for this controller.")
        else:
            sensor_types = {sensor["sensorID"]: sensor["type"] for sensor in sensors}
            await self.sensor_service.update_sensors(sensors)
            await self.irrigation_service.update_sensor_types(sensor_types)

    async def check_for_new_schedules(self):
        schedules = Schedules.get_schedules_by_controller(self.controller_id)
        if not schedules:
            self.logger.warning("No schedules found for this controller.")
        await self.irrigation_service.update_schedules(schedules)

    async def check_for_new_pumps(self):
        pumps = Pumps.get_pumps_by_controller(self.controller_id)
        if not pumps:
            self.logger.warning("No pumps found for this controller.")
        await self.irrigation_service.update_pumps(pumps)

    async def is_healthy(self):
        return self.healthy.is_set()

    async def wait_until_healthy(self):
        await self.healthy.wait()

    # --- Snapshot Listener Implementations for All Data Types ---

    # Plants listener
    def register_plants_listener(self):
        query = Plants.get_collection().where(
            filter=FieldFilter("controllerID", "==", self.controller_id)
        )
        self.plant_listener = query.on_snapshot(self.plant_snapshot_callback)
        self.logger.info("Plant snapshot listener registered.")

    def plant_snapshot_callback(self, docs, changes, read_time):
        self.logger.info("Plant snapshot update received.")

        async def async_callback():
            plants = await Plants.get_plants_by_controller_id(self.controller_id)
            if not plants:
                self.logger.warning("No plants found for this controller.")
            await self.irrigation_service.update_plants(plants)

        asyncio.run_coroutine_threadsafe(async_callback(), self.loop)

    # Sensors listener
    def register_sensors_listener(self):
        query = Sensors.get_collection().where(
            filter=FieldFilter("controllerID", "==", self.controller_id)
        )
        self.sensor_listener = query.on_snapshot(self.sensor_snapshot_callback)
        self.logger.info("Sensor snapshot listener registered.")

    def sensor_snapshot_callback(self, docs, changes, read_time):
        self.logger.info("Sensor snapshot update received.")
        try:
            sensors = Sensors.get_sensors_by_controller(self.controller_id)
            sensor_types = (
                {sensor["sensorID"]: sensor["type"] for sensor in sensors}
                if sensors
                else {}
            )
            asyncio.run_coroutine_threadsafe(
                self.sensor_service.update_sensors(sensors), self.loop
            )
            asyncio.run_coroutine_threadsafe(
                self.irrigation_service.update_sensor_types(sensor_types), self.loop
            )
        except Exception as e:
            self.logger.error(f"Error processing sensor snapshot: {e}")

    # Schedules listener
    def register_schedules_listener(self):
        query = Schedules.get_collection().where(
            filter=FieldFilter("controllerID", "==", self.controller_id)
        )
        self.schedule_listener = query.on_snapshot(self.schedule_snapshot_callback)
        self.logger.info("Schedule snapshot listener registered.")

    def schedule_snapshot_callback(self, docs, changes, read_time):
        self.logger.info("Schedule snapshot update received.")

        async def async_callback():
            schedules = await Schedules.get_schedules_by_controller(self.controller_id)
            if not schedules:
                self.logger.warning("No schedules found for this controller.")
            await self.irrigation_service.update_schedules(schedules)

        asyncio.run_coroutine_threadsafe(async_callback(), self.loop)

    # Pumps listener
    def register_pumps_listener(self):
        query = Pumps.get_collection().where(
            filter=FieldFilter("controllerID", "==", self.controller_id)
        )
        self.pump_listener = query.on_snapshot(self.pump_snapshot_callback)
        self.logger.info("Pump snapshot listener registered.")

    def pump_snapshot_callback(self, docs, changes, read_time):
        self.logger.info("Pump snapshot update received.")

        async def async_callback():
            pumps = await Pumps.get_pumps_by_controller(self.controller_id)
            if not pumps:
                self.logger.warning("No pumps found for this controller.")
            await self.irrigation_service.update_pumps(pumps)

        asyncio.run_coroutine_threadsafe(async_callback(), self.loop)
