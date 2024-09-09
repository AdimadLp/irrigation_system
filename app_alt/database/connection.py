from mongoengine import connect
from dotenv import load_dotenv
import os

load_dotenv()

_ATLAS_URI = os.getenv("ATLAS_URI")

# Establish a connection to the MongoDB database
connect(host=_ATLAS_URI, db='irrigation_system')