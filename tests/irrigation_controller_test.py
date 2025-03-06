import pytest

import time
from app.database.models.irrigation_controllers import IrrigationControllers
from app.database.firebase import db
from google.cloud.firestore_v1.base_query import FieldFilter


# language: python

# Import the function from the module using a relative import

# Ensure the module's global db is set
IrrigationControllers.db = db


@pytest.mark.asyncio
async def test_check_and_save_controller_new_and_existing():
    # Generate a unique deviceName using current timestamp
    unique_device_name = f"test-device-{int(time.time() * 1000)}"

    # Call the function for a new controller
    new_id = await IrrigationControllers.check_and_save_controller(
        deviceName=unique_device_name
    )
    assert isinstance(new_id, str)

    # Call the function again with the same deviceName to simulate duplicate entry
    existing_id = await IrrigationControllers.check_and_save_controller(
        deviceName=unique_device_name
    )
    assert new_id == existing_id

    # Clean up: remove the created document(s) from Firestore
    collection = db.collection("irrigation_controllers")
    docs = collection.where(
        filter=FieldFilter("deviceName", "==", unique_device_name)
    ).stream()
    for doc in docs:
        doc.reference.delete()
