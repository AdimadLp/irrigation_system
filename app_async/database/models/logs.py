from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db
import json
from pymongo import InsertOne


class WateringHistory:
    collection: AsyncIOMotorCollection = db.watering_logs

    @classmethod
    async def process_watering_logs(cls, watering_log_list):
        bulk_operations = []
        for log in watering_log_list:
            try:
                log_json = json.loads(log)

                if not isinstance(log_json, dict):
                    raise ValueError("Parsed data is not a dictionary")

                data = {
                    "plantID": log_json["plantID"],
                    "timestamp": log_json["timestamp"],
                }
                bulk_operations.append(InsertOne(data))

            except json.JSONDecodeError:
                raise ValueError("Invalid JSON data")
            except KeyError as e:
                raise ValueError(f"Missing required key in log data: {e}")

        if bulk_operations:
            result = await cls.collection.bulk_write(bulk_operations)
            return result.inserted_count
        return 0

    @classmethod
    async def get_by_plant_id(cls, plant_id):
        cursor = cls.collection.find({"plantID": plant_id})
        return await cursor.to_list(length=None)
