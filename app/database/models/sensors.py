from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.firebase import db
from app.logging_config import setup_logger
import json

logger = setup_logger(__name__)


class Sensors:
    @classmethod
    def get_collection(cls):
        return db.collection("sensors")

    @classmethod
    def create(cls, sensor_data):
        collection = cls.get_collection()
        doc_ref = collection.document()  # Auto-generate a document ID
        doc_ref.set(sensor_data)
        return doc_ref.id

    @classmethod
    def get_sensors_by_controller(cls, controller_id):
        collection = cls.get_collection()
        # Create a FieldFilter for the query.
        field_filter = FieldFilter("controllerID", "==", controller_id)
        docs = collection.where(filter=field_filter).stream()
        return [
            {"sensorID": doc.get("sensorID"), "type": doc.get("type")} for doc in docs
        ]

    @classmethod
    def process_sensor_data_batch(cls, sensor_data_list):
        collection = cls.get_collection()
        batch = db.batch()
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

                doc_ref = collection.document(sensor_id)
                # Use set with merge to upsert the document and push the new reading using ArrayUnion.
                batch.set(
                    doc_ref,
                    {
                        "sensorID": sensor_id,
                        "readings": firestore.ArrayUnion([reading]),
                    },
                    merge=True,
                )

                # Track the latest reading for each sensor.
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

        if latest_readings:
            batch.commit()
            logger.info("Successfully processed sensor data batch")
            return True, latest_readings
        else:
            logger.warning("No valid sensor data to process")
            return False, {}

    @classmethod
    def get_sensor_type(cls, sensorID):
        collection = cls.get_collection()
        doc_ref = collection.document(sensorID)
        doc = doc_ref.get()
        if doc.exists:
            return doc.get("type")
        else:
            logger.error(f"Sensor with ID {sensorID} not found")
            return None


def create_new_sensors(plant_data):
    return Sensors.create(plant_data)
