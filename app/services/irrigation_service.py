import asyncio
from datetime import datetime, date
from app.logging_config import setup_logger
import json
import time
from app.database.models.plants import Plants


class IrrigationService:
    def __init__(self, controller_id, redis_client, stop_event, test=False):
        self.logger = setup_logger(__name__)
        self.controller_id = controller_id
        self.redis_client = redis_client
        self.stop_event = stop_event
        self.plants = []
        self.schedules = []
        self.pumps = []
        self.sensor_types = {}
        self.healthy = asyncio.Event()
        self.healthy.set()
        self.last_watered_times = {}
        self.plants_initialized = asyncio.Event()
        self.test = test
        if test is False:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)
            self.GPIO = GPIO

    async def start(self):
        self.logger.info(
            f"Starting irrigation service for controller {self.controller_id}"
        )
        self.healthy.set()
        try:
            await self.wait_for_plants()
            await self.initialize_last_watered_times()
            self.check_irrigation_task = asyncio.create_task(
                self.check_for_irrigation()
            )
            self.logger.info("Irrigation check task created")
        except Exception as e:
            self.logger.error(f"Error starting irrigation service: {str(e)}")
            self.healthy.clear()
            raise

    async def wait_for_plants(self):
        try:
            self.logger.info("Waiting for plants to be initialized...")
            await self.plants_initialized.wait()
            self.logger.info("Plants initialized")
        except Exception as e:
            self.logger.error("Failed waiting for plants")

    async def stop(self):
        self.logger.info("Stopping irrigation service")
        self.stop_event.set()

        if hasattr(self, "check_irrigation_task"):
            self.check_irrigation_task.cancel()
            try:
                await self.check_irrigation_task
            except asyncio.CancelledError:
                pass

        if not self.test:
            for pump in self.pumps:
                try:
                    self.GPIO.setup(pump["gpioPort"], self.GPIO.OUT)
                    self.GPIO.output(
                        pump["gpioPort"], self.GPIO.HIGH
                    )  # Set GPIO port to HIGH
                    self.GPIO.cleanup(pump["gpioPort"])  # Free the GPIO port
                except Exception as e:
                    self.logger.error(
                        f"Error setting GPIO port {pump['gpioPort']} to HIGH: {str(e)}"
                    )

        self.logger.info("Irrigation service stopped")

    async def restart(self):
        await self.stop()
        await self.start()

    async def initialize_last_watered_times(self):
        try:
            if not self.plants:
                self.logger.warning(
                    "No plants available. Skipping initialization of last watered times."
                )
                return

            redis_logs = await self.redis_client.lrange("watering_logs", 0, -1)
            redis_logs = [json.loads(log) for log in redis_logs]

            plant_ids = [plant["plantID"] for plant in self.plants]
            redis_plant_ids = set(log["plantID"] for log in redis_logs)
            mongodb_plant_ids = set(plant_ids) - redis_plant_ids

            # Get last watering times from Redis
            for log in redis_logs:
                plant_id = log["plantID"]
                if plant_id in plant_ids and plant_id not in self.last_watered_times:
                    self.last_watered_times[plant_id] = log["timestamp"]
            self.logger.debug(
                f"Initialized last watered times for {len(redis_logs)} plants from Redis"
            )

            # Get last watering times from MongoDB for remaining plants
            if mongodb_plant_ids:
                mongodb_times = await Plants.get_last_watering_times(
                    list(mongodb_plant_ids)
                )
                if mongodb_times is not None:
                    self.last_watered_times.update(mongodb_times)
                    self.logger.debug(
                        f"Initialized last watered times for {len(mongodb_times)} plants from MongoDB"
                    )
                else:
                    self.logger.debug(f"mongodb_times is none")

            self.logger.info(
                f"Initialized last watered times for {len(self.last_watered_times)} plants"
            )
        except Exception as e:
            self.logger.error(f"Error initializing last watered times: {str(e)}")

    async def irrigate_plant(self, plant):
        try:
            # Simulating irrigation process
            self.logger.info(f"Irrigating plant {plant['plantID']}")

            pump_id = plant["pumpIDs"][0]
            pump = next(
                (p for p in self.pumps if p["plantID"] == plant["plantID"]), None
            )  # Get the pump from self.pumps

            if pump is None:
                self.logger.error(f"Could not find pump with id {pump_id}")
                return

            flow_rate = pump["flowRate"]

            irrigation_time = (
                60 * plant["waterRequirement"] / flow_rate
            )  # Calculate irrigation time in seconds
            self.logger.debug(
                f"Watering plant {plant['plantID']} with pump {pump_id} with {flow_rate}ml of flowrate for {irrigation_time}s on gpio port {pump['gpioPort']}"
            )
            if not self.test:

                self.GPIO.setup(pump["gpioPort"], self.GPIO.OUT)
                self.GPIO.output(pump["gpioPort"], self.GPIO.LOW)  # Start the pump
                await asyncio.sleep(irrigation_time)
                self.GPIO.output(pump["gpioPort"], self.GPIO.HIGH)  # Stop the pump
                self.GPIO.cleanup(pump["gpioPort"])  # Free the GPIO port

            # Create watering log
            watering_log = {
                "plantID": plant["plantID"],
                "timestamp": time.time(),
            }

            # Send watering log to Redis
            await self.redis_client.rpush("watering_logs", json.dumps(watering_log))

            # Update last_watered_times
            self.last_watered_times[plant["plantID"]] = watering_log["timestamp"]

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
        current_weekday = now.strftime("%A")
        current_time = now.time()

        # Convert startTime string to time object
        try:
            if isinstance(schedule["startTime"], str):
                schedule_start_time = datetime.strptime(
                    schedule["startTime"], "%H:%M"
                ).time()
            elif isinstance(
                schedule["startTime"], datetime.time
            ):  # Handle if already converted
                schedule_start_time = schedule["startTime"]
            else:
                self.logger.error(
                    f"Unexpected type for startTime in schedule {schedule.get('scheduleID', 'N/A')}: {type(schedule['startTime'])}"
                )
                return False
        except ValueError:
            self.logger.error(
                f"Invalid time format for startTime in schedule {schedule.get('scheduleID', 'N/A')}: {schedule['startTime']}"
            )
            return False  # Cannot compare if format is wrong

        schedule_weekdays = schedule["weekdays"]

        weekday_match = current_weekday in schedule_weekdays
        time_match = schedule_start_time <= current_time

        result = weekday_match and time_match
        return result

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

    async def get_last_watering_time(self, plant_id):
        try:
            watering_logs = await self.redis_client.lrange("watering_logs", 0, -1)
            watering_logs = [json.loads(log) for log in watering_logs]
            plant_logs = [log for log in watering_logs if log["plantID"] == plant_id]
            if plant_logs:
                return plant_logs[-1]["timestamp"]
        except Exception as e:
            self.logger.error(f"Error fetching last watering time: {str(e)}")
        return None

    async def is_irrigation_needed(self, plant):
        plant_schedules = [
            s for s in self.schedules if s["plantID"] == plant["plantID"]
        ]

        last_watered_unix = self.last_watered_times.get(plant["plantID"])
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
                    f"Current time is not within schedule {schedule["scheduleID"]} for plant {plant['plantID']}"
                )
        return False

    async def update_plants(self, new_plants):
        try:
            self.plants = new_plants
            self.logger.info(f"Updated plants: {len(new_plants)} plants")
            self.plants_initialized.set()
        except Exception as e:
            self.logger.error(f"Error updating plants: {str(e)}")

    async def update_schedules(self, new_schedules):
        try:
            self.schedules = new_schedules
            self.logger.info(f"Updated schedules: {len(new_schedules)} schedules")
        except Exception as e:
            self.logger.error(f"Error updating schedules: {str(e)}")

    async def update_pumps(self, new_pumps):
        try:
            self.pumps = new_pumps
            self.logger.info(f"Updated pumps: {len(new_pumps)} pumps")
        except Exception as e:
            self.logger.error(f"Error updating pumps: {str(e)}")

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
        #
