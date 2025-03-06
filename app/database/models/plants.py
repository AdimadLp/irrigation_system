from google.cloud.firestore_v1.base_query import FieldFilter
from ..firebase import db
from firebase_admin import firestore


class Plants:
    @classmethod
    async def get_collection(cls):
        """
        if not db_connection.is_connected():
            return None
        return db_connection.db.plants

        """
        collection_name = "plants"
        return db.collection(collection_name)

    @classmethod
    async def create(cls, plant_data):
        collection = await cls.get_collection()
        new_doc_ref = collection.document()  # auto-generates a document ID
        new_plant_id = new_doc_ref.id
        plant_data["plantID"] = new_plant_id
        new_doc_ref.set(plant_data)
        return new_plant_id

    @classmethod
    async def get_by_id(cls, plant_id):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("plantID", "==", plant_id))
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None

    @classmethod
    async def get_plants_by_controller_id(cls, controller_id):
        collection = await cls.get_collection()
        query = collection.where(
            filter=FieldFilter("controllerID", "==", controller_id)
        )
        docs = query.stream()
        plants = []
        for doc in docs:
            plants.append(doc.to_dict())
        return plants

    @classmethod
    async def get_sensors_by_plant_id(cls, plant_id):
        plant = await cls.get_by_id(plant_id)
        return plant.get("sensorIDs", []) if plant else []

    @classmethod
    async def update(cls, plant_id, update_data):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("plantID", "==", plant_id))
        docs = query.stream()
        for doc in docs:
            doc.reference.update(update_data)
            return 1
        return 0

    @classmethod
    async def bulk_update_watering_history(cls, watering_data):
        collection = await cls.get_collection()
        updated_count = 0
        for plant_id, timestamp in watering_data:
            query = collection.where(filter=FieldFilter("plantID", "==", plant_id))
            docs = query.stream()
            for doc in docs:
                doc.reference.update(
                    {
                        "wateringHistory": firestore.ArrayUnion(
                            [{"timestamp": timestamp}]
                        )
                    }
                )
                updated_count += 1
        return updated_count

    @classmethod
    async def get_last_watering_times(cls, plant_ids):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("plantID", "in", plant_ids))
        docs = query.stream()
        results = []
        for doc in docs:
            results.append(doc.to_dict())
        return {
            plant["plantID"]: (
                plant["wateringHistory"][-1]["timestamp"]
                if plant.get("wateringHistory")
                else None
            )
            for plant in results
        }


async def create_new_plant(plant_data):
    return await Plants.create(plant_data)
