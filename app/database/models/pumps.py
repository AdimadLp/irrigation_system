from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db_connection


class Pumps:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.pumps
    
    @classmethod
    async def create(cls, pump_data):
        collection = await cls.get_collection()
        if collection is None:
            return None
        result = await collection.insert_one(pump_data)
        return result.inserted_id
    
    @classmethod
    async def get_pumps_by_controller(cls, controller_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        cursor = collection.find(
            {"controllerID": controller_id},
            {"plantID": 1, "gpioPort": 1, "type": 1, "status": 1, "flowRate": 1, "_id": 0}
        )
        return await cursor.to_list(length=None)

    @classmethod
    async def get_by_id(cls, pump_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        return await collection.find_one({"pumpID": pump_id})

    @classmethod
    async def update(cls, pump_id, update_data):
        collection = await cls.get_collection()
        if collection is None:
            return None
        result = await collection.update_one(
            {"pumpID": pump_id}, {"$set": update_data}
        )
        return result.modified_count

    @classmethod
    async def delete(cls, pump_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        result = await collection.delete_one({"pumpID": pump_id})
        return result.deleted_count
async def create_new_pump(plant_data):
    return await Pumps.create(plant_data)