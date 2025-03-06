import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from database.firebase import db

# Define the collection name
collection_name = "plants"

# Define the document data
document_data = {
    "plantID": 2,
    "plantName": "Aloe Vera",
    "plantType": "Succulent",
    "location": "Schreibtisch",
    "controllerID": 1,
    "sensorIDs": [],
    "pumpIDs": [2],
    "waterRequirement": 100,
    "imagePath": "https://www.123zimmerpflanzen.de/media/catalog/product/cache/7e47a816da2f8f1d082e569b4e2be5e7/s/p/spathiphyllum_sweet_rocco.jpg",
}

# Add the document to the collection
db.collection(collection_name).add(document_data)

# Print a success message
print("Document added to collection.")
