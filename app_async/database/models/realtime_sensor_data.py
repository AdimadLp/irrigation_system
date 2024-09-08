from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db
from logging_config import setup_logger
from pymongo import UpdateOne

logger = setup_logger(__name__)


class RealtimeSensorData:
    collection: AsyncIOMotorCollection = db.realtime_sensor_data

    @classmethod
    async def update_realtime_sensor_data(self, latest_readings):
        if not latest_readings:
            self.logger.info("No realtime sensor data to update.")
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
            result = await db.realtime_sensor_data.bulk_write(bulk_operations)
            logger.info(f"Updated realtime data for {result.modified_count} sensors")
        else:
            logger.warning("No valid realtime sensor data to update")
