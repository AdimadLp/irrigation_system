from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db


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
