import logging
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import StringField, IntField, FloatField, DateTimeField, ListField, EmbeddedDocumentField
from mongoengine.errors import ValidationError
from datetime import datetime

logger = logging.getLogger(__name__)

class SensorReading(EmbeddedDocument):
    value = FloatField(required=True)  # Assuming the value is a float, adjust as necessary
    timestamp = DateTimeField(default=datetime.now)

class Sensors(Document):
    sensorID = IntField(required=True, unique=True)
    sensorName = StringField(required=True)
    controllerID = IntField(required=True)
    gpioPort = IntField(required=True)
    type = StringField(required=True)
    readings = ListField(EmbeddedDocumentField(SensorReading))
    meta = {'indexes': [{'fields': ['sensorID'], 'unique': True}]}

    @staticmethod
    def get_all_sensors_by_controller(controllerID):
        return Sensors.objects(controllerID=controllerID)
    
    @staticmethod
    def save_sensor_data(data_list):
        for data in data_list:
            sensorID = data.get('sensorID')
            value = data.get('value')

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