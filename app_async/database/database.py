import motor.motor_asyncio
from dotenv import load_dotenv
import os
from pymongo.errors import ConfigurationError

load_dotenv()

_ATLAS_URI = os.getenv("ATLAS_URI")

try:
    # Create a new client and connect to the server
    client = motor.motor_asyncio.AsyncIOMotorClient(_ATLAS_URI)
except ConfigurationError as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    exit(1)
# Get the database
db = client.irrigation_system
