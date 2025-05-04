import asyncio
from app.database.database import db_connection
from app.database.models.pumps import create_new_pump  # Import the function

async def main():
    # Pump data dictionary
    await db_connection.connect()
    pump_data = {
        "name": "Pump 3",
        "controllerID": 1,  # Example ObjectId
        "plantID": 3,  # Example ObjectId
        "gpioPort": 4,
        "type": "Water",
        "status": "Active",
        "flowRate": 100  # Flow rate in milliliters per minute
    }

    # Create and save the new pump to the database
    pump_id = await create_new_pump(pump_data)

    print(f"New pump added to the database with id: {pump_id}.")

# Run the main function
asyncio.run(main())