from app.database.models import Plants
import app.database.connection
from datetime import datetime

# Create a new plant instance
new_plant = Plants(
    plantID=1,  # Unique identifier for the plant
    plantName="Einblatt",
    plantType="Spathiphyllum",
    location="Schuhschrank",
    controllerID=1,  # Assuming you have a controller with ID 1
    sensorIDs=[],  # List of associated sensor IDs
    pumpIDs=[1],  # List of associated pump IDs
    waterRequirement=100,  # Water requirement in milliliters
    lastWatered=datetime.now(),  # Last watered timestamp
    imagePath="https://www.123zimmerpflanzen.de/media/catalog/product/cache/7e47a816da2f8f1d082e569b4e2be5e7/s/p/spathiphyllum_sweet_rocco.jpg"
)

# Save the new plant to the database
new_plant.save()

print("New plant added to the database.")