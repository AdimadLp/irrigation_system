import socket
from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.firebase import db


def get_device_name():
    # return socket.gethostname()
    return "pop-os"


def get_ip_address():
    return socket.gethostbyname(socket.gethostname())


class IrrigationControllers:
    @classmethod
    async def check_and_save_controller(
        cls,
        deviceName=get_device_name(),
        deviceType="",
        ipAddress=get_ip_address(),
        status="Active",
    ):
        collection_name = "irrigation_controllers"
        collection = db.collection(collection_name)

        # Check if a controller with the same deviceName already exists
        query = collection.where(filter=FieldFilter("deviceName", "==", deviceName))
        docs = query.stream()
        existing_controller = None
        for doc in docs:
            existing_controller = doc.to_dict()
            break

        if existing_controller:
            print(f"Controller with Name {deviceName} already exists.")
            return existing_controller["controllerID"]
        else:
            # Generate a document reference with an auto-generated ID
            new_doc_ref = collection.document()  # auto-generates a document ID
            new_controller_id = new_doc_ref.id
            new_controller = {
                "controllerID": new_controller_id,
                "deviceName": deviceName,
                "deviceType": deviceType,
                "ipAddress": ipAddress,
                "status": status,
            }

            # Save the new controller to the database using set()
            new_doc_ref.set(new_controller)
            print("New controller added to the database.")
            return new_controller_id
