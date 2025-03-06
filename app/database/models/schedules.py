from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.firebase import db


class Schedules:
    @classmethod
    async def get_collection(cls):
        collection_name = "schedules"
        return db.collection(collection_name)

    @classmethod
    async def create(cls, schedule_data):
        collection = await cls.get_collection()
        # Auto-generate document ID using Firestore's document() method
        doc_ref = collection.document()  # auto-generates an ID
        # Save the auto-generated ID in the document data (if needed)
        schedule_data["scheduleID"] = doc_ref.id
        doc_ref.set(schedule_data)
        return doc_ref.id

    @classmethod
    async def get_schedules_by_controller(cls, controller_id):
        collection = await cls.get_collection()
        query = collection.where(
            filter=FieldFilter("controllerID", "==", controller_id)
        )
        docs = query.stream()
        schedules = []
        for doc in docs:
            schedules.append(doc.to_dict())
        return schedules

    @classmethod
    async def get_by_id(cls, schedule_id):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("scheduleID", "==", schedule_id))
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None

    @classmethod
    async def update(cls, schedule_id, update_data):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("scheduleID", "==", schedule_id))
        docs = query.stream()
        for doc in docs:
            doc.reference.update(update_data)
            return 1
        return 0

    @classmethod
    async def delete(cls, schedule_id):
        collection = await cls.get_collection()
        query = collection.where(filter=FieldFilter("scheduleID", "==", schedule_id))
        docs = query.stream()
        for doc in docs:
            doc.reference.delete()
            return 1
        return 0


async def create_new_schedule(schedule_data):
    return await Schedules.create(schedule_data)
