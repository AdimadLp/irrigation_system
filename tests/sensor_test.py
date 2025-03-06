import json
import time
from datetime import datetime
import pytest
from app.database.models.sensors import Sensors, create_new_sensors
from app.database.firebase import db

# language: python


def delete_sensor_doc(doc_id_or_sensor_id, use_doc_id=True):
    # If use_doc_id True, then doc_id_or_sensor_id is the firestore generated document id.
    # Otherwise, it's the sensorID field used as document name.
    if use_doc_id:
        db.collection("sensors").document(doc_id_or_sensor_id).delete()
    else:
        db.collection("sensors").document(doc_id_or_sensor_id).delete()


def get_test_sensor_data(
    sensor_id, controller_id="test_controller", sensor_type="temperature"
):
    return {
        "sensorID": sensor_id,
        "controllerID": controller_id,
        "type": sensor_type,
        "readings": [],
    }


def get_current_timestamp():
    return int(time.time())


def test_create_sensor():
    # Generate unique sensor data
    sensor_id = f"test_sensor_{int(time.time() * 1000)}"
    sensor_data = get_test_sensor_data(sensor_id)

    # Create sensor using Sensors.create
    doc_id = Sensors.create(sensor_data)
    assert isinstance(doc_id, str)

    # Retrieve document using doc_id and verify content
    doc = db.collection("sensors").document(doc_id).get()
    assert doc.exists
    data = doc.to_dict()
    assert data.get("sensorID") == sensor_id
    assert data.get("controllerID") == "test_controller"
    assert data.get("type") == "temperature"

    # Cleanup
    delete_sensor_doc(doc_id)


def test_get_sensors_by_controller():
    # Generate unique controller id and two sensor docs with that uid
    controller_id = f"test_controller_{int(time.time() * 1000)}"
    sensor_id1 = f"test_sensor_{int(time.time() * 1000)}_1"
    sensor_id2 = f"test_sensor_{int(time.time() * 1000)}_2"

    sensor_data1 = get_test_sensor_data(sensor_id1, controller_id)
    sensor_data2 = get_test_sensor_data(
        sensor_id2, controller_id, sensor_type="humidity"
    )

    doc_id1 = Sensors.create(sensor_data1)
    doc_id2 = Sensors.create(sensor_data2)

    sensors_list = Sensors.get_sensors_by_controller(controller_id)
    # Check that both sensorID exist in results with proper type:
    sensor_ids = [sensor.get("sensorID") for sensor in sensors_list]
    sensor_types = {
        sensor.get("sensorID"): sensor.get("type") for sensor in sensors_list
    }

    assert sensor_id1 in sensor_ids
    assert sensor_id2 in sensor_ids
    assert sensor_types[sensor_id1] == "temperature"
    assert sensor_types[sensor_id2] == "humidity"

    # Cleanup
    delete_sensor_doc(doc_id1)
    delete_sensor_doc(doc_id2)


def test_process_sensor_data_batch():
    # Create sensor data batch for the same sensor_id with two readings (increasing timestamp)
    sensor_id = f"test_sensor_{int(time.time() * 1000)}"
    base_data = {
        "sensorID": sensor_id,
        "value": 20,
        "timestamp": get_current_timestamp(),
    }
    # Create a second reading 1 second later
    second_data = {
        "sensorID": sensor_id,
        "value": 25,
        "timestamp": get_current_timestamp() + 1,
    }
    # Build JSON string list
    sensor_batch = [json.dumps(base_data), json.dumps(second_data)]

    # Process batch
    success, latest_readings = Sensors.process_sensor_data_batch(sensor_batch)
    assert success is True
    assert sensor_id in latest_readings
    # The latest reading should be second_data
    assert latest_readings[sensor_id]["value"] == 25
    assert latest_readings[sensor_id]["timestamp"] == second_data["timestamp"]

    # Cleanup: delete sensor document retrieved by sensor_id
    delete_sensor_doc(sensor_id, use_doc_id=False)


def test_get_sensor_type():
    # Create sensor document manually where document id equals sensorID
    sensor_id = f"test_sensor_{int(time.time() * 1000)}"
    sensor_data = get_test_sensor_data(sensor_id, sensor_type="pressure")
    db.collection("sensors").document(sensor_id).set(sensor_data)

    sensor_type = Sensors.get_sensor_type(sensor_id)
    assert sensor_type == "pressure"

    # Cleanup
    delete_sensor_doc(sensor_id, use_doc_id=False)


def test_create_new_sensors_function():
    # Test the standalone function create_new_sensors
    sensor_id = f"test_sensor_{int(time.time() * 1000)}"
    sensor_data = get_test_sensor_data(sensor_id, sensor_type="moisture")
    doc_id = create_new_sensors(sensor_data)
    assert isinstance(doc_id, str)

    doc = db.collection("sensors").document(doc_id).get()
    assert doc.exists
    data = doc.to_dict()
    assert data.get("sensorID") == sensor_id
    assert data.get("type") == "moisture"

    # Cleanup
    delete_sensor_doc(doc_id)
