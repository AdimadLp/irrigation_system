import asyncio
from datetime import datetime, date
from logging_config import setup_logger
import json
import time
from database.models.plants import Plants


class IrrigationService:
    def __init__(self, controller_id, redis_client, stop_event):
        self.logger = setup_logger(__name__)
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.stop_event = stop_event
        self.plants = []
        self.schedules = []
        self.sensor_types = {}
        self.healthy = asyncio.Event()
        self.healthy.set()

    async def start(self):
        self.logger.info(
            f"Starting irrigation service for controller {self.controller_id}"
        )
        self.healthy.set()
        try:
            self.check_irrigation_task = asyncio.create_task(
                self.check_for_irrigation()
            )
            self.logger.info("Irrigation check task created")
        except Exception as e:
            self.logger.error(f"Error starting irrigation service: {str(e)}")
            self.healthy.clear()
            raise

    async def stop(self):
        self.logger.info("Stopping irrigation service")
        self.stop_event.set()
        if hasattr(self, "check_irrigation_task"):
            self.check_irrigation_task.cancel()
            try:
                await self.check_irrigation_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Irrigation service stopped")

    async def restart(self):
        await self.stop()
        await self.start()

    async def irrigate_plant(self, plant):
        try:
            # Simulating irrigation process
            self.logger.info(f"Irrigating plant {plant['plantID']}")
            await asyncio.sleep(2)  # Simulating irrigation time

            # Create watering log
            watering_log = {
                "plantID": plant["plantID"],
                "timestamp": time.time(),
            }

            # Send watering log to Redis
            await self.redis_client.rpush("watering_logs", json.dumps(watering_log))

            self.logger.info(f"Irrigation completed for plant {plant['plantID']}")
        except Exception as e:
            self.logger.error(f"Error during irrigation: {str(e)}")

    async def check_for_irrigation(self):
        self.logger.info("Starting irrigation check loop")
        while not self.stop_event.is_set():
            try:
                for plant in self.plants:
                    self.logger.debug(
                        f"Checking irrigation for plant {plant['plantID']}"
                    )
                    if await self.is_irrigation_needed(plant):
                        self.logger.info(
                            f"Irrigation needed for plant {plant['plantID']}!"
                        )
                        await self.irrigate_plant(plant)
                    else:
                        self.logger.debug(
                            f"No irrigation needed for plant {plant['plantID']}"
                        )
                await asyncio.sleep(5)  # Wait 5 seconds before the next check cycle
            except asyncio.CancelledError:
                self.logger.info("Irrigation check loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in check_for_irrigation: {str(e)}")
                self.healthy.clear()
                await asyncio.sleep(5)  # Wait before retrying
        self.logger.info("Irrigation check loop ended")

    def during_time(self, schedule):
        now = datetime.now()
        return (
            now.strftime("%A") in schedule["weekdays"]
            and schedule["startTime"].time() <= now.time()
        )

    async def is_threshold_met(self, threshold):
        try:
            sensor_data = await self.redis_client.get("sensor_data")
            sensor_data = eval(sensor_data or "[]")
            for reading in sensor_data:
                sensor_type = self.sensor_types.get(reading["sensorID"])
                if sensor_type == "moisture":
                    if reading["value"] < threshold:
                        self.logger.info(
                            f"Moisture level is below threshold: {reading['value']} < {threshold}"
                        )
                        return True
                    else:
                        self.logger.info(
                            f"Moisture level is above threshold: {reading['value']} >= {threshold}"
                        )
                        return False
            self.logger.warning("No moisture sensor data found")
        except Exception as e:
            self.logger.error(f"Error fetching or processing sensor data: {str(e)}")
        return False

    async def is_irrigation_needed(self, plant):
        plant_schedules = [
            s for s in self.schedules if s["plantID"] == plant["plantID"]
        ]
        last_watered_unix = await Plants.get_last_watering_time(plant["plantID"])
        now = datetime.now()

        if last_watered_unix is not None:
            last_watered_date = date.fromtimestamp(last_watered_unix)
        else:
            last_watered_date = None

        for schedule in plant_schedules:
            if self.during_time(schedule):
                if last_watered_date is None or last_watered_date < now.date():
                    if schedule["type"] == "threshold":
                        return await self.is_threshold_met(schedule["threshold"])
                    elif schedule["type"] == "interval":
                        return True
                else:
                    self.logger.debug(f"Plant {plant['plantID']} already watered today")
            else:
                self.logger.debug(
                    f"Current time is not within schedule for plant {plant['plantID']}"
                )
        return False

    async def update_plants(self, new_plants):
        try:
            self.plants = new_plants
            self.logger.info(f"Updated plants: {len(new_plants)} plants")
        except Exception as e:
            self.logger.error(f"Error updating plants: {str(e)}")

    async def update_schedules(self, new_schedules):
        try:
            self.schedules = new_schedules
            self.logger.info(f"Updated schedules: {len(new_schedules)} schedules")
        except Exception as e:
            self.logger.error(f"Error updating schedules: {str(e)}")

    async def update_sensor_types(self, new_sensor_types):
        try:
            self.sensor_types = new_sensor_types
            self.logger.info(f"Updated sensor types: {len(new_sensor_types)} sensors")
        except Exception as e:
            self.logger.error(f"Error updating sensor types: {str(e)}")

    async def is_healthy(self):
        return self.healthy.is_set()

    async def wait_until_healthy(self):
        await self.healthy.wait()
