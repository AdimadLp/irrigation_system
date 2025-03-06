from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.firebase import db


class Pumps:
    @classmethod
    async def get_collection(cls):
        collection_name = "pumps"
        return db.collection(collection_name)

    @classmethod
    async def create(cls, pump_data):
        collection = await cls.get_collection()
        new_doc_ref = collection.document()  # auto-generates a document ID
        new_pump_id = new_doc_ref.id
        pump_data["pumpID"] = new_pump_id
        new_doc_ref.set(pump_data)
        return new_pump_id

    @classmethod
    async def get_pumps_by_controller(cls, controller_id):
        collection = await cls.get_collection()
        query = collection.where(
            filter=FieldFilter("controllerID", "==", controller_id)
        )
        docs = query.stream()
        pumps = []
        for doc in docs:
            pumps.append(doc.to_dict())
        return pumps

    @classmethod
    async def get_by_id(cls, pump_id):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("pumpID", "==", pump_id))
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None

    @classmethod
    async def update(cls, pump_id, update_data):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("pumpID", "==", pump_id))
        docs = query.stream()
        for doc in docs:
            doc.reference.update(update_data)
            return 1
        return 0

    @classmethod
    async def delete(cls, pump_id):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("pumpID", "==", pump_id))
        docs = query.stream()
        for doc in docs:
            doc.reference.delete()
            return 1
        return 0


async def create_new_pump(pump_data):
    return await Pumps.create(pump_data)
