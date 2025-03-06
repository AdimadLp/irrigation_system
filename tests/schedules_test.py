import pytest
import time
from datetime import datetime, timezone  # updated to include timezone
from app.database.models.schedules import Schedules, create_new_schedule

# language: python


@pytest.mark.asyncio
async def test_create_new_schedule():
    # Create unique schedule data
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    schedule_data = {
        "controllerID": unique_controller_id,
        "name": "Test Schedule Create",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    # Create schedule using class method
    schedule_id = await Schedules.create(schedule_data)
    assert isinstance(schedule_id, str)

    # Retrieve schedule and assert its data matches
    schedule = await Schedules.get_by_id(schedule_id)
    assert schedule is not None
    assert schedule.get("controllerID") == unique_controller_id
    assert schedule.get("name") == "Test Schedule Create"
    assert schedule.get("scheduleID") == schedule_id

    # Cleanup: delete the created schedule
    delete_result = await Schedules.delete(schedule_id)
    assert delete_result == 1


@pytest.mark.asyncio
async def test_get_schedules_by_controller():
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    schedule_data = {
        "controllerID": unique_controller_id,
        "name": "Test Schedule By Controller",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    # Create schedule
    schedule_id = await Schedules.create(schedule_data)
    assert isinstance(schedule_id, str)

    # Retrieve schedules for the controller
    schedules = await Schedules.get_schedules_by_controller(unique_controller_id)
    found = any(s.get("scheduleID") == schedule_id for s in schedules)
    assert found is True

    # Cleanup: delete the schedule
    delete_result = await Schedules.delete(schedule_id)
    assert delete_result == 1


@pytest.mark.asyncio
async def test_update_schedule():
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    schedule_data = {
        "controllerID": unique_controller_id,
        "name": "Test Schedule Update",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    # Create schedule
    schedule_id = await Schedules.create(schedule_data)
    assert isinstance(schedule_id, str)

    # Update schedule's name
    new_name = "Updated Schedule Name"
    update_result = await Schedules.update(schedule_id, {"name": new_name})
    assert update_result == 1

    # Retrieve schedule and verify the update
    schedule = await Schedules.get_by_id(schedule_id)
    assert schedule is not None
    assert schedule.get("name") == new_name

    # Cleanup: delete the schedule
    delete_result = await Schedules.delete(schedule_id)
    assert delete_result == 1


@pytest.mark.asyncio
async def test_delete_schedule():
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    schedule_data = {
        "controllerID": unique_controller_id,
        "name": "Test Schedule Delete",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    # Create schedule
    schedule_id = await Schedules.create(schedule_data)
    assert isinstance(schedule_id, str)

    # Delete schedule and check result
    delete_result = await Schedules.delete(schedule_id)
    assert delete_result == 1

    # Verify schedule has been removed
    schedule = await Schedules.get_by_id(schedule_id)
    assert schedule is None


@pytest.mark.asyncio
async def test_create_new_schedule_function():
    # Test the standalone function create_new_schedule
    unique_controller_id = f"test_controller_{int(time.time() * 1000)}"
    schedule_data = {
        "controllerID": unique_controller_id,
        "name": "Test Schedule Function",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    schedule_id = await create_new_schedule(schedule_data)
    assert isinstance(schedule_id, str)

    schedule = await Schedules.get_by_id(schedule_id)
    assert schedule is not None
    assert schedule.get("controllerID") == unique_controller_id
    assert schedule.get("name") == "Test Schedule Function"
    assert schedule.get("scheduleID") == schedule_id

    # Cleanup: delete the schedule
    delete_result = await Schedules.delete(schedule_id)
    assert delete_result == 1
