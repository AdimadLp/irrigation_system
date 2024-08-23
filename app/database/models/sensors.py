from logging_config import setup_logger
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

            try:
                sensor = Sensors.objects(sensorID=sensorID).get()
                reading = SensorReading(value=value, timestamp=timestamp)
                sensor.readings.append(reading)
                if session:
                    sensor.save(session=session)
                else:
                    sensor.save()
                logger.info(f"Saved reading for sensor {sensorID}")
            except Sensors.DoesNotExist:
                logger.error(f"Sensor with ID {sensorID} not found")
            except Exception as e:
                logger.error(f"Error saving data for sensor {sensorID}: {str(e)}")

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