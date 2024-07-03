from mongoengine import Document, StringField, IntField
import socket


def get_highest_id():
    # Sort the controllers by controllerID in descending order and get the first one
    last_controller = IrrigationControllers.objects.order_by("-controllerID").first()
    if last_controller is None:
        return 0
    else:
        return last_controller.controllerID


def get_device_name():
    # return socket.gethostname()
    return "pop-os"


def get_ip_address():
    return socket.gethostbyname(socket.gethostname())


class IrrigationControllers(Document):
    controllerID = IntField(required=True, unique=True)
    deviceName = StringField(required=True, unique=True)
    deviceType = StringField(required=True)
    ipAddress = StringField(required=True)
    status = StringField(required=True)
    meta = {"indexes": [{"fields": ["controllerID"], "unique": True}]}

    # Assuming there's a method in IrrigationControllers to find by ID
    def check_and_save_controller(
        deviceName=get_device_name(),
        deviceType="",
        ipAddress=get_ip_address(),
        status="Active",
    ):
        # Check if a controller with the same ID already exists
        existing_controller = IrrigationControllers.objects(
            deviceName=deviceName
        ).first()

        if existing_controller:
            print(f"Controller with Name {deviceName} already exists.")
            return existing_controller.controllerID
        else:
            # Create a new controller instance
            new_controller = IrrigationControllers(
                controllerID=get_highest_id() + 1,
                deviceName=deviceName,
                deviceType=deviceType,
                ipAddress=ipAddress,
                status=status,
            )

            # Save the new controller to the database
            new_controller.save()
            print("New controller added to the database.")
            return new_controller.controllerID
