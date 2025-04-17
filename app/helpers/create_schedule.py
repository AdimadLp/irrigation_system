from app.database.models.schedules import (
    get_highest_id,
    create_new_schedule,
)  # Import the new function
from app.database.database import db_connection
from datetime import datetime
import asyncio


async def main():
    # Connect to the database
    await db_connection.connect()

    # Schedule data dictionary
    schedule_data = {
        "controllerID": 3,
        "scheduleID": await get_highest_id() + 1,  # Get the next available schedule ID
        "weekdays": ["Thursday"],  # List of weekdays
        "startTime": "21:15",  # Store as string
        "type": "interval",
        "plantID": 4,
        "threshold": 40,
    }

    # Create and save the new schedule to the database
    # The create_new_schedule function returns the inserted_id
    inserted_id = await create_new_schedule(schedule_data)

    # Fetch the document using the id or modify create_new_schedule to return the document
    # For now, just printing the ID
    if inserted_id:
        print(
            f"New schedule added to the database with id: {inserted_id}."
        )  # Print the returned ID
    else:
        print("Failed to add new schedule.")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
