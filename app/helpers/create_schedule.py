from app.database.models import Schedules
import app.database.connection
from datetime import datetime

# Create a new plant instance
new_schedule = Schedules(
    scheduleID=3,
    weekdays=["Monday", "Wednesday", "Friday", "Sunday"],
    startTime=datetime.strptime("17:00", "%H:%M"),
    endTime=datetime.strptime("23:59", "%H:%M"),
    type="Interval",
    plantID=1,
    threshold=40,
)

# Save the new plant to the database
new_schedule.save()

print("New schedule added to the database.")
