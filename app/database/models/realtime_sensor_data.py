from mongoengine import Document, IntField, FloatField
from logging_config import setup_logger

logger = setup_logger(__name__)

class RealtimeSensorData(Document):
    sensorID = IntField(required=True)
    value = IntField(required=True)
    timestamp = FloatField(required=True)
    meta = {'indexes': [{'fields': ['timestamp'], 'unique': False}]}

    @staticmethod
    def update_sensor_data(data_list):
        for data in data_list:
            sensorID = data.get('sensorID')
            value = data.get('value')
            timestamp = data.get('timestamp')

            # Validate the data
            if sensorID is None:
                logger.error(f"Missing sensorID")
                continue
            if value is None:
                logger.error(f"Missing value for sensor {sensorID}")
                continue
            if timestamp is None:
                logger.error(f"Missing timestamp for sensor {sensorID}")
                continue
            
            # Get the existing record if it exists
            existing_record = RealtimeSensorData.objects(sensorID=sensorID).first()
            
            if existing_record:
                # Update the existing record
                existing_record.update(value=value, timestamp=timestamp)
                logger.info(f"Updated value with {value} of existing sensor {sensorID}")
            else:
                # Create a new record
                new_record = RealtimeSensorData(sensorID=sensorID, value=value, timestamp=timestamp)
                new_record.save()
                logger.info(f"Created new sensor {sensorID} and saved value {value}")