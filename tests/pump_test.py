import pytest
import time
import uuid
from app.database.models.pumps import Pumps, create_new_pump

# language: python


@pytest.mark.asyncio
async def test_create_new_pump():
    # Create unique pump data with a unique controllerID
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    pump_data = {"controllerID": unique_controller_id, "name": "Test Pump Create"}
    pump_id = await Pumps.create(pump_data)
    assert isinstance(pump_id, str)

    # Retrieve pump and assert its data matches
    pump = await Pumps.get_by_id(pump_id)
    assert pump is not None
    assert pump.get("controllerID") == unique_controller_id
    assert pump.get("name") == "Test Pump Create"

    # Cleanup: delete the created pump
    delete_result = await Pumps.delete(pump_id)
    assert delete_result == 1


@pytest.mark.asyncio
async def test_get_pumps_by_controller():
    # Create pump with known controllerID
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    pump_data = {
        "controllerID": unique_controller_id,
        "name": "Test Pump By Controller",
    }
    pump_id = await Pumps.create(pump_data)
    assert isinstance(pump_id, str)

    # Retrieve list of pumps by controllerID
    pumps = await Pumps.get_pumps_by_controller(unique_controller_id)
    found = any(p.get("pumpID") == pump_id for p in pumps)
    assert found is True

    # Cleanup: delete the created pump
    delete_result = await Pumps.delete(pump_id)
    assert delete_result == 1


@pytest.mark.asyncio
async def test_update_pump():
    # Create pump data
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    pump_data = {"controllerID": unique_controller_id, "name": "Test Pump Update"}
    pump_id = await Pumps.create(pump_data)
    assert isinstance(pump_id, str)

    # Update pump's name
    new_name = "Updated Pump Name"
    update_result = await Pumps.update(pump_id, {"name": new_name})
    assert update_result == 1

    # Retrieve pump and verify update
    pump = await Pumps.get_by_id(pump_id)
    assert pump is not None
    assert pump.get("name") == new_name

    # Cleanup: delete the pump
    delete_result = await Pumps.delete(pump_id)
    assert delete_result == 1


@pytest.mark.asyncio
async def test_delete_pump():
    # Create pump data
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    pump_data = {"controllerID": unique_controller_id, "name": "Test Pump Delete"}
    pump_id = await Pumps.create(pump_data)
    assert isinstance(pump_id, str)

    # Delete pump and check result
    delete_result = await Pumps.delete(pump_id)
    assert delete_result == 1

    # Verify pump has been removed
    pump = await Pumps.get_by_id(pump_id)
    assert pump is None


@pytest.mark.asyncio
async def test_create_new_pump_function():
    # Test the standalone function create_new_pump
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    pump_data = {"controllerID": unique_controller_id, "name": "Test Pump Function"}
    pump_id = await create_new_pump(pump_data)
    assert isinstance(pump_id, str)

    pump = await Pumps.get_by_id(pump_id)
    assert pump is not None
    assert pump.get("controllerID") == unique_controller_id
    assert pump.get("name") == "Test Pump Function"

    # Cleanup: delete the created pump
    delete_result = await Pumps.delete(pump_id)
    assert delete_result == 1
