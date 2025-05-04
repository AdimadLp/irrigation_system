import pytest
import time
from datetime import datetime
from google.cloud.firestore_v1 import DocumentSnapshot
from app.database.models.realtime_sensor_data import RealtimeSensorData
from app.database.firebase import db

# language: python

# Relative imports: import the class to be tested, and the db for cleanup & verification


@pytest.mark.asyncio
async def test_update_valid_realtime_sensor_data():
    # Create valid sensor readings
    sensor1 = "test_sensor_1"
    sensor2 = "test_sensor_2"
    current_time = int(time.time())

    latest_readings = {
        sensor1: {"value": 42, "timestamp": current_time},
        sensor2: {"value": 84, "timestamp": current_time},
    }

    # Call update function
    await RealtimeSensorData.update_realtime_sensor_data(latest_readings)

    # Access the collection and verify each document
    collection = db.collection("realtime_sensor_data")
    for sensor_id, reading in latest_readings.items():
        doc = collection.document(sensor_id).get()
        # Assert the document exists and fields match
        assert doc.exists is True
        data = doc.to_dict()
        assert data.get("sensorID") == sensor_id
        last_reading = data.get("lastReading")
        assert last_reading is not None
        assert last_reading.get("value") == reading["value"]
        # Allow some slack in timestamp conversion check by comparing types and date equality
        doc_timestamp = last_reading.get("timestamp")
        assert isinstance(doc_timestamp, datetime)
    # Cleanup: delete created documents
    for sensor_id in latest_readings.keys():
        collection.document(sensor_id).delete()


@pytest.mark.asyncio
async def test_update_empty_realtime_sensor_data():
    # Call update with empty dictionary
    await RealtimeSensorData.update_realtime_sensor_data({})
    # Nothing to verify and no cleanup needed


@pytest.mark.asyncio
async def test_update_invalid_realtime_sensor_data():
    # Create a sensor reading missing the "timestamp"
    sensor_invalid = "test_sensor_invalid"
    latest_readings = {sensor_invalid: {"value": 99}}  # Missing timestamp

    # Call update function; errors should be logged and the document not created
    await RealtimeSensorData.update_realtime_sensor_data(latest_readings)

    # Verify that the document was not created
    collection = db.collection("realtime_sensor_data")
    doc = collection.document(sensor_invalid).get()
    assert doc.exists is False
    # Cleanup if needed (should not exist, but delete as a safety measure)
    collection.document(sensor_invalid).delete()
