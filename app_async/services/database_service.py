import asyncio
from logging_config import setup_logger
from database.models import (
    Plants,
    Sensors,
    Schedules,
    RealtimeSensorData,
    WateringHistory,
)
import time
from pymongo.errors import NetworkTimeout, ConnectionFailure
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

    async def start(self):
        self.logger.info("Starting database service")
        self.healthy.set()
        await asyncio.gather(self.run(), self.monitor_network())

    async def stop(self):
        self.logger.info("Stopping database service")
        self.stop_event.set()

    async def run(self):
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                await asyncio.wait_for(self.network_available.wait(), timeout=1)
                # Check for new data every 10 seconds
                if current_time - self.last_check_time >= 10:
                    await self.check_for_new_data()
                    self.last_check_time = current_time
                await self.save_sensor_data()
                await self.save_watering_logs()
                await asyncio.sleep(1)
            except asyncio.TimeoutError:
                pass

    async def monitor_network(self):
        while not self.stop_event.is_set():
            if not self.network_available.is_set():
                if await self.network_is_available():
                    self.network_available.set()
                    self.logger.info(
                        "Network connection restored. Resuming operations."
                    )
                else:
                    self.logger.info("Waiting for network connection to be restored...")
            await asyncio.sleep(self.network_check_interval)

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

        except (NetworkTimeout, ConnectionFailure) as e:
            self.logger.error(f"Network error: {e}")
            self.network_available.clear()
            return False, {}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.increment_exception_count()
            return False, {}

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
        )
        self.logger.info("Finished checking for new data.")

    async def check_for_new_plants(self):
        plants = await Plants.get_plants_by_controller_id(self.controller_id)
        if not plants:
            self.logger.warning("No plants found for this controller.")
        await self.irrigation_service.update_plants(plants)

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

    async def is_healthy(self):
        return self.healthy.is_set()

    async def wait_until_healthy(self):
        await self.healthy.wait()
