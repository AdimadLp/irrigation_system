from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.firebase import db
from app.logging_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class RealtimeSensorData:
    @classmethod
    async def get_collection(cls):
        collection_name = "realtime_sensor_data"
        return db.collection(collection_name)

    @classmethod
    async def update_realtime_sensor_data(cls, latest_readings):
        collection = await cls.get_collection()
        if not latest_readings:
            logger.info("No realtime sensor data to update.")
            return

        batch = db.batch()
        updated_count = 0

        for sensor_id, reading in latest_readings.items():
            try:
                # Format the reading for Firestore
                formatted_reading = {
                    "value": reading["value"],
                    "timestamp": datetime.fromtimestamp(reading["timestamp"]),
                }

                doc_ref = collection.document(sensor_id)
                batch.set(
                    doc_ref, {"sensorID": sensor_id, "lastReading": formatted_reading}
                )
                updated_count += 1
            except (ValueError, KeyError, TypeError) as e:
                logger.error(
                    f"Error processing reading for sensor {sensor_id}: {e}, reading: {reading}"
                )
        try:
            batch.commit()
            logger.info(f"Updated realtime data for {updated_count} sensors")

        except Exception as e:
            logger.error(f"Error committing realtime sensor data batch: {e}")
