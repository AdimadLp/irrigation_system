import logging
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import StringField, IntField, FloatField, DateTimeField, ListField, EmbeddedDocumentField
from mongoengine.errors import ValidationError
from datetime import datetime

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
            if sensorID is None:
                continue  # Skip if 'sensorID' is not present
            sensor = Sensors.objects(sensorID=sensorID).first()
            if sensor:
                value = data.get('value')
                if value is not None:
                    try:
                        # Create a new SensorReading instance
                        reading = SensorReading(value=value)
                        # Optionally, set the timestamp if provided in data
                        if 'timestamp' in data:
                            reading.timestamp = data['timestamp']
                        sensor.readings.append(reading)
                        sensor.save()
                    except ValidationError as e:
                        print(f"Validation error while saving sensor data: {e}")
                else:
                    print(f"No 'value' key found for sensorID {sensorID}")
            else:
                print(f"Sensor with ID {sensorID} not found")