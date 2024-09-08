from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db


class WateringLogs:
    collection: AsyncIOMotorCollection = db.watering_logs

    @classmethod
    async def create(cls, log_data):
        result = await cls.collection.insert_one(log_data)
        return result.inserted_id

    @classmethod
    async def get_by_plant_id(cls, plant_id):
        cursor = cls.collection.find({"plantID": plant_id})
        return await cursor.to_list(length=None)
