from logging_config import setup_logger
from pymongo import UpdateOne
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    StringField,
    IntField,
    FloatField,
    ListField,
    EmbeddedDocumentField,
)

logger = setup_logger(__name__)


class SensorReading(EmbeddedDocument):
    value = FloatField(required=True)
    timestamp = FloatField(required=True)


class Sensors(Document):
    sensorID = IntField(required=True, unique=True)
    sensorName = StringField(required=True)
    controllerID = IntField(required=True)
    gpioPort = IntField(required=True)
    type = StringField(required=True)
    readings = ListField(EmbeddedDocumentField(SensorReading))
    meta = {"indexes": [{"fields": ["sensorID"], "unique": True}]}

    @staticmethod
    def get_sensors_by_controller(controller_id):
        return Sensors.objects(controllerID=controller_id)

    @staticmethod
    def save_sensor_data(data_list, session=None):
        bulk_operations = []
        for data in data_list:
            sensorID = data.get("sensorID")
            value = data.get("value")
            timestamp = data.get("timestamp")

            if sensorID is None:
                logger.error("Missing sensorID")
                continue
            if value is None:
                logger.error(f"Missing value for sensor {sensorID}")
                continue
            if timestamp is None:
                logger.error(f"Missing timestamp for sensor {sensorID}")
                continue

            reading = SensorReading(value=value, timestamp=timestamp)
            bulk_operations.append(
                UpdateOne(
                    {"sensorID": sensorID},
                    {"$push": {"readings": reading.to_mongo()}},
                    upsert=True,
                )
            )

        if bulk_operations:
            try:
                Sensors._get_collection().bulk_write(bulk_operations, session=session)
                logger.info(f"Saved {len(bulk_operations)} sensor readings")
            except Sensors.DoesNotExist:
                logger.error(f"Sensor with ID {sensorID} not found")
            except Exception as e:
                # TODO: 2024-08-27 01:25:59,196 - sensors.py - save_sensor_data - ERROR - Error saving data for sensor 4: Caused by :: Write conflict during plan execution and yielding is disabled. :: Please retry your operation or multi-document transaction., full error: {'errorLabels': ['TransientTransactionError'], 'ok': 0.0, 'errmsg': 'Caused by :: Write conflict during plan execution and yielding is disabled. :: Please retry your operation or multi-document transaction.', 'code': 112, 'codeName': 'WriteConflict', '$clusterTime': {'clusterTime': Timestamp(1724714759, 8), 'signature': {'hash': b'\xd9\xab\xd0g\x1f,h\x00\xa5\xf2\xe3\x99q\xd8\xb3\x9cH\xb5\xb8\x98', 'keyId': 7364634122427301889}}, 'operationTime': Timestamp(1724714759, 8)}
                logger.error(f"Error uploading data for sensor {sensorID}: {str(e)}")
                raise

    @staticmethod
    def get_sensor_type(sensorID):
        try:
            sensor = Sensors.objects(sensorID=sensorID).get()
            return sensor.type
        except Sensors.DoesNotExist:
            logger.error(f"Sensor with ID {sensorID} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting sensor type for {sensorID}: {str(e)}")
            return None
