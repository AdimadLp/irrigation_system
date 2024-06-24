from app.database.models import Sensors
import app.database.connection
from datetime import datetime

# Create a new plant instance
new_sensor = Sensors(
    sensorID = 3,
    sensorName = "Room Temperature Sensor",
    controllerID = 1,
    gpioPort = 5,
    type = "Temperature"
    )

# Save the new plant to the database
new_sensor.save()

print("New sensor added to the database.")