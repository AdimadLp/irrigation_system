from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db_connection


class Schedules:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.schedules

    @classmethod
    async def get_highest_id(cls):
        collection = await cls.get_collection()
        if collection is None:
            return None
        # Sort the schedules by scheduleID in descending order and get the first one
        last_schedule = await collection.find_one(sort=[("scheduleID", -1)])
        if last_schedule is None:
            return 0
        else:
            return last_schedule["scheduleID"]

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


async def get_highest_id():
    return await Schedules.get_highest_id()


async def create_new_schedule(schedule_data: dict):
    inserted_id = await Schedules.create(schedule_data)
    return inserted_id
