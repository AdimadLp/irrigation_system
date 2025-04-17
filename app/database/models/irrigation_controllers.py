from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import db_connection
import socket
import asyncio


def get_device_name():
    return socket.gethostname()


# return "pop-os"


def get_ip_address():
    return socket.gethostbyname(socket.gethostname())


class IrrigationControllers:
    @classmethod
    async def get_collection(cls):
        if not db_connection.is_connected():
            return None
        return db_connection.db.irrigation_controllers

    @classmethod
    async def get_highest_id(cls):
        collection = await cls.get_collection()
        if collection is None:
            return None
        # Sort the controllers by controllerID in descending order and get the first one
        last_controller = await collection.find_one(sort=[("controllerID", -1)])
        if last_controller is None:
            return 0
        else:
            return last_controller["controllerID"]

    @classmethod
    async def check_and_save_controller(
        cls,
        deviceName=get_device_name(),
        deviceType="",
        ipAddress=get_ip_address(),
        status="Active",
    ):
        collection = await cls.get_collection()
        if collection is None:
            return None
        # Check if a controller with the same name already exists
        existing_controller = await collection.find_one({"deviceName": deviceName})

        if existing_controller:
            print(f"Controller with Name {deviceName} already exists.")
            return existing_controller["controllerID"]
        else:
            # Create a new controller instance
            new_controller_id = await cls.get_highest_id() + 1
            new_controller = {
                "controllerID": new_controller_id,
                "deviceName": deviceName,
                "deviceType": deviceType,
                "ipAddress": ipAddress,
                "status": status,
            }

            # Save the new controller to the database
            await collection.insert_one(new_controller)
            print("New controller added to the database.")
            return new_controller_id


# Example of how to use the async function
async def main():
    controller_id = await IrrigationControllers.check_and_save_controller()
    print(f"Controller ID: {controller_id}")


if __name__ == "__main__":
    asyncio.run(main())
