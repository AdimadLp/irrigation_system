from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db


class Schedules:
    collection: AsyncIOMotorCollection = db.schedules

    @classmethod
    async def create(cls, schedule_data):
        result = await cls.collection.insert_one(schedule_data)
        return result.inserted_id

    @classmethod
    async def get_schedules_by_controller(cls, controller_id):
        cursor = cls.collection.find({"controllerID": controller_id})
        return await cursor.to_list(length=None)
