from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db_connection


class Schedules:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.schedules

    @classmethod
    async def create(cls, schedule_data):
        collection = await cls.get_collection()
        if collection is None:
            return None
        result = await collection.insert_one(schedule_data)
        return result.inserted_id

    @classmethod
    async def get_schedules_by_controller(cls, controller_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        cursor = collection.find({"controllerID": controller_id})
        return await cursor.to_list(length=None)
