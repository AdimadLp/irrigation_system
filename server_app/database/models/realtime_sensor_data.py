from motor.motor_asyncio import AsyncIOMotorCollection
from app.database.database import db_connection
from app.logging_config import setup_logger
from pymongo import UpdateOne

logger = setup_logger(__name__)


class RealtimeSensorData:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.realtime_sensor_data

    @classmethod
    async def update_realtime_sensor_data(cls, latest_readings):
        collection = await cls.get_collection()
        if collection is None:
            return None
        if not latest_readings:
            logger.info("No realtime sensor data to update.")
            return

        bulk_operations = []

        for sensor_id, reading in latest_readings.items():
            bulk_operations.append(
                UpdateOne(
                    {"sensorID": sensor_id},
                    {"$set": {"lastReading": reading}},
                    upsert=True,
                )
            )

        if bulk_operations:
            result = await collection.bulk_write(bulk_operations)
            logger.info(f"Updated realtime data for {result.modified_count} sensors")
        else:
            logger.warning("No valid realtime sensor data to update")
