from motor.motor_asyncio import AsyncIOMotorCollection
from app.database.database import db_connection
from app.logging_config import setup_logger
import json
from pymongo import UpdateOne

logger = setup_logger(__name__)


class Sensors:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.sensors

    @classmethod
    async def create(cls, sensor_data):
        collection = await cls.get_collection()
        if collection is None:
            return None
        result = await collection.insert_one(sensor_data)
        return result.inserted_id

    @classmethod
    async def get_sensors_by_controller(cls, controller_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        cursor = collection.find(
            {"controllerID": controller_id},
            projection={"sensorID": 1, "type": 1, "_id": 0},
        )
        return await cursor.to_list(length=None)

    @classmethod
    async def process_sensor_data_batch(cls, sensor_data_list):
        collection = await cls.get_collection()
        if collection is None:
            return None
        bulk_operations = []
        latest_readings = {}

        for data_str in sensor_data_list:
            try:
                data = json.loads(data_str)

                if not isinstance(data, dict):
                    raise ValueError("Parsed data is not a dictionary")

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
            result = await collection.bulk_write(bulk_operations)
            logger.info(f"Successfully processed {result.modified_count} items")
            return True, latest_readings
        else:
            logger.warning("No valid sensor data to process")
            return False, {}

    @classmethod
    async def get_sensor_type(cls, sensorID):
        collection = await cls.get_collection()
        if collection is None:
            return None
        sensor = await collection.find_one({"sensorID": sensorID})
        if sensor:
            return sensor.get("type")
        else:
            logger.error(f"Sensor with ID {sensorID} not found")
            return None


async def create_new_sensors(plant_data):
    return await Sensors.create(plant_data)
