from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

_ATLAS_URI = os.getenv("ATLAS_URI")

class MongoDB:
    def __init__(self):
        self.db_name = "mydatabase"
        self.client = MongoClient(_ATLAS_URI)
        self.db = self.client[self.db_name]

    def __enter__(self):
        return self.db

    def __exit__(self):
        self.client.close()