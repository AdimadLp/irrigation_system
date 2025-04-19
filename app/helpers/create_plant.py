import asyncio
from datetime import datetime
from app.database.models.plants import create_new_plant  # Import the function
from app.database.models.plants import get_highest_id
from app.database.database import db_connection


async def main():
    # Plant data dictionary
    await db_connection.connect()
    plant_data = {
        "plantID": await get_highest_id() + 1,  # Get the next available plant ID
        "plantName": "Basilikum",
        "plantType": "",
        "location": "Fensterbrett Keller",
        "controllerID": 4,  # Assuming you have a controller with ID 1
        "sensorIDs": [],  # List of associated sensor IDs
        "waterRequirement": 100,  # Water requirement in milliliters
        "imagePath": "https://www.123zimmerpflanzen.de/media/catalog/product/cache/7e47a816da2f8f1d082e569b4e2be5e7/s/p/spathiphyllum_sweet_rocco.jpg",
    }

    # Create and save the new plant to the database
    plant_id = await create_new_plant(plant_data)

    print(f"New plant added to the database with id: {plant_id}.")


# Run the main function
asyncio.run(main())
