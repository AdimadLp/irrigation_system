import asyncio
from app.database.database import db_connection
from app.database.models.sensors import create_new_sensors  # Import the function


async def main():
    # Pump data dictionary
    await db_connection.connect()
    # Create a new plant instance
    sensor_data = {
        "sensorID": 6,
        "sensorName": "Room Humidity Sensor",
        "controllerID": 4,
        "gpioPort": 5,
        "type": "Humidity",
    }

    # Create and save the new pump to the database
    pump_id = await create_new_sensors(sensor_data)

    print(f"New pump added to the database with id: {pump_id}.")


# Run the main function
asyncio.run(main())
