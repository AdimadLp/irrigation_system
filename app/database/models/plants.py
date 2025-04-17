from ..database import db_connection
from pymongo import UpdateOne


class Plants:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.plants

    @staticmethod
    async def create(plant_data):
        collection = await Plants.get_collection()
        if collection is None:
            return None
        result = await collection.insert_one(plant_data)
        return str(result.inserted_id)

    @classmethod
    async def get_by_id(cls, plant_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        return await collection.find_one({"plantID": plant_id})

    @classmethod
    async def get_highest_id(cls):
        collection = await cls.get_collection()
        if collection is None:
            return None
        # Sort the plants by plantID in descending order and get the first one
        last_plant = await collection.find_one(sort=[("plantID", -1)])
        if last_plant is None:
            return 0
        else:
            return last_plant["plantID"]

    @classmethod
    async def get_plants_by_controller_id(cls, controller_id):
        collection = await cls.get_collection()
        if collection is None:
            return None
        cursor = collection.find(
            {"controllerID": controller_id},
            {
                "plantID": 1,
                "sensorIDs": 1,
                "pumpIDs": 1,
                "waterRequirement": 1,
                "_id": 0,
            },
        )
        return await cursor.to_list(length=None)

    @classmethod
    async def get_sensors_by_plant_id(cls, plant_id):
        plant = await cls.get_by_id(plant_id)
        return plant["sensorIDs"] if plant else []

    @classmethod
    async def update(cls, plant_id, update_data):
        collection = await cls.get_collection()
        if collection is None:
            return None
        result = await collection.update_one(
            {"plantID": plant_id}, {"$set": update_data}
        )
        return result.modified_count

    @classmethod
    async def bulk_update_watering_history(cls, watering_data):
        collection = await cls.get_collection()
        if collection is None:
            return None
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
            result = await collection.bulk_write(bulk_operations)
            return result.modified_count
        return 0

    @classmethod
    async def get_last_watering_times(cls, plant_ids):
        collection = await cls.get_collection()
        if collection is None:
            return None
        cursor = collection.find(
            {"plantID": {"$in": plant_ids}},
            {"plantID": 1, "wateringHistory": {"$slice": 1}},
        )
        results = await cursor.to_list(length=None)
        return {
            plant["plantID"]: (
                plant["wateringHistory"][0]["timestamp"]
                if plant.get("wateringHistory")
                else None
            )
            for plant in results
        }


async def create_new_plant(plant_data):
    return await Plants.create(plant_data)


async def get_highest_id():
    return await Plants.get_highest_id()
