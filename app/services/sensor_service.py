import asyncio
import time
import json
from logging_config import setup_logger


class SensorService:
    def __init__(self, controller_id, redis_client, stop_event):
        self.logger = setup_logger(__name__)
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.stop_event = stop_event
        self.sensors = []
        self.healthy = asyncio.Event()
        self.healthy.set()

    async def start(self):
        self.logger.info("Starting sensor service")
        self.healthy.set()
        asyncio.create_task(self.update_data())

    async def stop(self):
        self.logger.info("Stopping sensor service")
        self.stop_event.set()
        await asyncio.sleep(1)  # Give time for the update_data loop to stop

    async def restart(self):
        await self.stop()
        await self.start()

    async def update_data(self):
        while not self.stop_event.is_set():
            try:
                new_data = await self.read_sensor_data()

                if new_data:  # Only push if there's data
                    for data in new_data:
                        await self.redis_client.rpush("sensor_data", json.dumps(data))
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in update_data: {e}")
                self.healthy.clear()
                await asyncio.sleep(5)  # Wait before retrying

    async def read_sensor_data(self):
        sensor_data = []
        for sensor in self.sensors:
            self.logger.info(
                f"Reading data from sensor {sensor['sensorID']} of type {sensor['type']}"
            )
            # Simulated sensor reading. Replace with actual sensor reading logic
            sensor_data.append(
                {
                    "sensorID": sensor["sensorID"],
                    "value": 1,  # Replace with actual sensor value
                    "timestamp": time.time(),
                }
            )
        return sensor_data

    async def update_sensors(self, new_sensors):
        self.sensors = new_sensors

    async def is_healthy(self):
        return self.healthy.is_set()

    async def wait_until_healthy(self):
        await self.healthy.wait()
