import pytest
import time
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.models.logs import Logs

# language: python


@pytest.mark.asyncio
async def test_process_valid_logs():
    # Generate a unique scriptname to mark our logs for cleanup
    unique_scriptname = f"test_script_{int(time.time() * 1000)}"
    valid_log = {
        "asctime": datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f"),
        "scriptname": unique_scriptname,
        "custom_funcname": "test_valid_func",
        "levelname": "INFO",
        "message": "Test log message for valid log",
    }
    logs_to_process = [valid_log]
    inserted_count = await Logs.process_logs(logs_to_process)
    assert inserted_count == 1

    # Cleanup: find and delete logs created with our unique scriptname
    collection = await Logs.get_collection()
    docs = collection.where(
        filter=FieldFilter("scriptname", "==", unique_scriptname)
    ).stream()
    for doc in docs:
        doc.reference.delete()


@pytest.mark.asyncio
async def test_process_invalid_logs():
    # Create an invalid log entry (missing required field "asctime")
    invalid_log = {
        "scriptname": "invalid_script",
        "custom_funcname": "test_invalid_func",
        "levelname": "ERROR",
        "message": "Invalid log missing asctime",
    }
    logs_to_process = [invalid_log]
    inserted_count = await Logs.process_logs(logs_to_process)
    # No valid log entries should have been processed
    assert inserted_count == 0
