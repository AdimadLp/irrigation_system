from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db_connection
import json
from pymongo import InsertOne


class Logs:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.logs

    @classmethod
    async def process_logs(cls, logs):
        collection = await cls.get_collection()
        if collection is None:
            return None
        bulk_operations = []
        for log in logs:
            try:
                log_json = json.loads(log)

                if not isinstance(log_json, dict):
                    raise ValueError("Parsed data is not a dictionary")

                data = {
                    "asctime": log_json["asctime"],
                    "scriptname": log_json["scriptname"],
                    "custom_funcname": log_json["custom_funcname"],
                    "levelname": log_json["levelname"],
                    "message": log_json["message"],
                }
                bulk_operations.append(InsertOne(data))

            except json.JSONDecodeError:
                raise ValueError("Invalid JSON data")
            except KeyError as e:
                raise ValueError(f"Missing required key in log data: {e}")

        if bulk_operations:
            result = await collection.bulk_write(bulk_operations)
            return result.inserted_count
        return 0
