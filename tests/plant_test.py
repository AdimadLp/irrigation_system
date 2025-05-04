import pytest

import time
from app.database.models.plants import Plants
from app.database.firebase import db
from google.cloud.firestore_v1.base_query import FieldFilter


@pytest.mark.asyncio
async def test_create_and_get_plant():
    # Create a new plant entry
    plant_data = {"name": "Test Plant", "controllerID": 999}
    new_plant_id = await Plants.create(plant_data)
    assert isinstance(new_plant_id, str)

    # Retrieve the plant by its id
    plant = await Plants.get_by_id(new_plant_id)
    assert plant is not None
    assert plant.get("plantID") == new_plant_id
    assert plant.get("name") == "Test Plant"

    # Cleanup: delete the test entry from the database
    collection = db.collection("plants")
    docs = collection.where(filter=FieldFilter("plantID", "==", new_plant_id)).stream()
    for doc in docs:
        doc.reference.delete()


@pytest.mark.asyncio
async def test_update_plant():
    # Create a new plant entry
    plant_data = {"name": "Plant To Update", "controllerID": 888}
    new_plant_id = await Plants.create(plant_data)

    # Update the plant's name
    update_count = await Plants.update(new_plant_id, {"name": "Updated Plant Name"})
    assert update_count == 1

    # Retrieve the updated plant and confirm the update
    updated_plant = await Plants.get_by_id(new_plant_id)
    assert updated_plant.get("name") == "Updated Plant Name"

    # Cleanup: delete the test entry
    collection = db.collection("plants")
    docs = collection.where(filter=FieldFilter("plantID", "==", new_plant_id)).stream()
    for doc in docs:
        doc.reference.delete()


@pytest.mark.asyncio
async def test_bulk_update_watering_history():
    # Create two plant entries
    plant_data1 = {"name": "Plant 1", "controllerID": 777}
    plant_data2 = {"name": "Plant 2", "controllerID": 777}
    id1 = await Plants.create(plant_data1)
    id2 = await Plants.create(plant_data2)

    # Prepare watering history update data as list of tuples
    current_timestamp = int(time.time())
    watering_data = [(id1, current_timestamp), (id2, current_timestamp)]

    # Perform bulk update
    updated_count = await Plants.bulk_update_watering_history(watering_data)
    assert updated_count >= 2

    # Retrieve updated plants and confirm wateringHistory contains timestamp
    plant1 = await Plants.get_by_id(id1)
    plant2 = await Plants.get_by_id(id2)
    assert plant1.get("wateringHistory") is not None
    assert plant2.get("wateringHistory") is not None
    assert any(
        entry.get("timestamp") == current_timestamp
        for entry in plant1["wateringHistory"]
    )
    assert any(
        entry.get("timestamp") == current_timestamp
        for entry in plant2["wateringHistory"]
    )

    # Cleanup: delete the test entries
    for plant_id in [id1, id2]:
        collection = db.collection("plants")
        docs = collection.where(filter=FieldFilter("plantID", "==", plant_id)).stream()
        for doc in docs:
            doc.reference.delete()
