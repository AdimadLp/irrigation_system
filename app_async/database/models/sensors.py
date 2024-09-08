from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db
from logging_config import setup_logger
import json
from pymongo import UpdateOne

logger = setup_logger(__name__)


class Sensors:
    collection: AsyncIOMotorCollection = db.sensors

    @classmethod
    async def get_sensors_by_controller(cls, controller_id):
        cursor = cls.collection.find(
            {"controllerID": controller_id},
            projection={"sensorID": 1, "type": 1, "_id": 0},
        )
        return await cursor.to_list(length=None)

    async def process_sensor_data_batch(sensor_data_list):
        bulk_operations = []
        latest_readings = {}

        for data_str in sensor_data_list:
            try:
                data = json.loads(data_str)

                if not isinstance(data, dict):
                    raise ValueError("Parsed data is not a dictionary")

                if (
                    "sensorID" not in data
                    or "value" not in data
                    or "timestamp" not in data
                ):
                    raise ValueError("Missing required fields in sensor data")

                sensor_id = data["sensorID"]
                reading = {
                    "value": data["value"],
                    "timestamp": data["timestamp"],
                }

                bulk_operations.append(
                    UpdateOne(
                        {"sensorID": sensor_id},
                        {"$push": {"readings": reading}},
                        upsert=True,
                    )
                )

                # Keep track of the latest reading for each sensor
                if (
                    sensor_id not in latest_readings
                    or data["timestamp"] > latest_readings[sensor_id]["timestamp"]
                ):
                    latest_readings[sensor_id] = reading

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON data: {data_str}")
            except ValueError as ve:
                logger.warning(f"Invalid data format: {ve}")
            except Exception as e:
                logger.error(f"Error processing sensor data: {e}")

        if bulk_operations:
            result = await db.sensors.bulk_write(bulk_operations)
            logger.info(f"Successfully processed {result.modified_count} items")
            return True, latest_readings
        else:
            logger.warning("No valid sensor data to process")
            return False, {}

    @classmethod
    async def get_sensor_type(cls, sensorID):
        sensor = await cls.collection.find_one({"sensorID": sensorID})
        if sensor:
            return sensor.get("type")
        else:
            logger.error(f"Sensor with ID {sensorID} not found")
            return None
