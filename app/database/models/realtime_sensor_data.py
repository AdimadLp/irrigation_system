from mongoengine import Document, IntField, DateTimeField
from datetime import datetime

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
            if sensorID is None or value is None:
                print(f"Missing data for sensorID: {sensorID}, value: {value}")
                continue
            
            # Check if a record with the same sensorID and timestamp exists
            existing_record = RealtimeSensorData.objects(sensorID=sensorID).first()
            
            if existing_record:
                # Update the existing record
                existing_record.update(value=value, timestamp=timestamp)
            else:
                # Create a new record
                new_record = RealtimeSensorData(sensorID=sensorID, value=value, timestamp=timestamp)
                new_record.save()