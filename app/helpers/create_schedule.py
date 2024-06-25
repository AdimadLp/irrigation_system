from app.database.models import Schedules
import app.database.connection
from datetime import datetime

# Create a new plant instance
new_schedule = Schedules(
    scheduleID = 1,
    weekdays = ["Monday", "Wednesday", "Friday"],
    startTime = datetime.strptime("08:00", "%H:%M"),
    endTime = datetime.strptime("10:00", "%H:%M"),
    type = "Interval",
    plantID = 1,
    threshold = 40,
    )

# Save the new plant to the database
new_schedule.save()

print("New schedule added to the database.")