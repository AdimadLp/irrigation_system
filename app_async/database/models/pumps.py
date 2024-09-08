from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db


class Pumps:
    collection: AsyncIOMotorCollection = db.pumps

    @classmethod
    async def create(cls, pump_data):
        result = await cls.collection.insert_one(pump_data)
        return result.inserted_id

    @classmethod
    async def get_by_id(cls, pump_id):
        return await cls.collection.find_one({"pumpID": pump_id})

    @classmethod
    async def update(cls, pump_id, update_data):
        result = await cls.collection.update_one(
            {"pumpID": pump_id}, {"$set": update_data}
        )
        return result.modified_count

    @classmethod
    async def delete(cls, pump_id):
        result = await cls.collection.delete_one({"pumpID": pump_id})
        return result.deleted_count
