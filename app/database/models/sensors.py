from logging_config import setup_logger
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    StringField,
    IntField,
    FloatField,
    DateTimeField,
    ListField,
    EmbeddedDocumentField,
)
from mongoengine.errors import ValidationError
from datetime import datetime
from bson import ObjectId  # Add this import statement

logger = setup_logger(__name__)


class SensorReading(EmbeddedDocument):
    value = FloatField(
        required=True
    )  # Assuming the value is a float, adjust as necessary
    timestamp = DateTimeField(default=datetime.now)


class Sensors(Document):
    sensorID = IntField(required=True, unique=True)
    sensorName = StringField(required=True)
    controllerID = IntField(required=True)
    gpioPort = IntField(required=True)
    type = StringField(required=True)
    readings = ListField(EmbeddedDocumentField(SensorReading))
    meta = {"indexes": [{"fields": ["sensorID"], "unique": True}]}

    @staticmethod
    def get_all_sensors_by_controller(controllerID):
        return Sensors.objects(controllerID=controllerID)

    @staticmethod
    def save_sensor_data(data_list):
        for data in data_list:
            sensorID = data.get("sensorID")
            value = data.get("value")

            if sensorID is None:
                logger.error("Missing sensorID")
                continue
            if value is None:
                logger.error(f"Missing value for sensor {sensorID}")
                continue

            sensor = Sensors.objects(sensorID=sensorID).first()
            if sensor:
                # Create a new SensorReading instance
                reading = SensorReading(value=value)
                sensor.readings.append(reading)
                sensor.save()
            else:
                logger.error(f"Sensor with ID {sensorID} not found")

    @staticmethod
    def get_sensor_type(sensorID):
        sensor = Sensors.objects(sensorID=sensorID).first()
        if sensor:
            return sensor.type
        else:
            logger.error(f"Sensor with ID {sensorID} not found")
            return None

    @staticmethod
    def get_new_sensors(since_date):
        """
        Retrieves sensors that have been added to the database since a specified date.

        :param since_date: A datetime object representing the point in time from which new sensors should be identified.
        :return: A list of Sensors documents that were added to the database after the specified date.
        """
        # Use the __raw__ query to leverage MongoDB's $gt (greater than) operator on the _id field.
        # ObjectId creation times can be used to approximate document creation times.
        return Sensors.objects(
            __raw__={"_id": {"$gt": ObjectId.from_datetime(since_date)}}
        )
