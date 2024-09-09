from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db
from pymongo import UpdateOne


class Plants:
    collection: AsyncIOMotorCollection = db.plants

    @classmethod
    async def create(cls, plant_data):
        result = await cls.collection.insert_one(plant_data)
        return result.inserted_id

    @classmethod
    async def get_by_id(cls, plant_id):
        return await cls.collection.find_one({"plantID": plant_id})

    @classmethod
    async def get_plants_by_controller_id(cls, controller_id):
        cursor = cls.collection.find({"controllerID": controller_id})
        return await cursor.to_list(length=None)

    @classmethod
    async def get_sensors_by_plant_id(cls, plant_id):
        plant = await cls.get_by_id(plant_id)
        return plant["sensorIDs"] if plant else []

    @classmethod
    async def update(cls, plant_id, update_data):
        result = await cls.collection.update_one(
            {"plantID": plant_id}, {"$set": update_data}
        )
        return result.modified_count

    @classmethod
    async def bulk_update_watering_history(cls, watering_data):
        bulk_operations = []
        for plant_id, timestamp in watering_data:
            bulk_operations.append(
                UpdateOne(
                    {"plantID": plant_id},
                    {
                        "$push": {
                            "wateringHistory": {
                                "$each": [{"timestamp": timestamp}],
                                "$sort": {"timestamp": -1},
                            }
                        }
                    },
                )
            )

        if bulk_operations:
            result = await cls.collection.bulk_write(bulk_operations)
            return result.modified_count
        return 0

    @classmethod
    async def get_last_watering_time(cls, plant_id):
        plant = await cls.get_by_id(plant_id)
        if plant and plant.get("wateringHistory"):
            return plant["wateringHistory"][0]["timestamp"]
        return None
