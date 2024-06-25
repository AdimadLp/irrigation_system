from mongoengine import Document, IntField, DateTimeField
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RealtimeSensorData(Document):
    sensorID = IntField(required=True)
    value = IntField(required=True)
    timestamp = DateTimeField(required=True)
    meta = {'indexes': [{'fields': ['timestamp'], 'unique': False}]}

    @staticmethod
    def update_sensor_data(data_list):
        for data in data_list:
            sensorID = data.get('sensorID')
            value = data.get('value')
            timestamp = datetime.now()

            # Validate the data
            if sensorID is None:
                logger.error(f"Missing sensorID")
                continue
            if value is None:
                logger.error(f"Missing value for sensor {sensorID}")
                continue
            
            # Check if a record with the same sensorID exists
            existing_record = RealtimeSensorData.objects(sensorID=sensorID).first()
            
            if existing_record:
                # Update the existing record
                existing_record.update(value=value, timestamp=timestamp)
                logger.info(f"Updated value with {value} of existing sensor {sensorID} at {timestamp}")
            else:
                # Create a new record
                new_record = RealtimeSensorData(sensorID=sensorID, value=value, timestamp=timestamp)
                new_record.save()
                logger.info(f"Created new sensor {sensorID} and saved value {value} at {timestamp}")