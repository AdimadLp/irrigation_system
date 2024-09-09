import motor.motor_asyncio
from dotenv import load_dotenv
import os
from pymongo.errors import ConfigurationError
from logging_config import setup_logger
import socket
import asyncio

logger = setup_logger(__name__)

load_dotenv()

_ATLAS_URI = os.getenv("ATLAS_URI")

def check_internet_connection(host="8.8.8.8", port=53, timeout=5):
    """
    Check if there is an internet connection by trying to connect to
    Google's DNS server.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

class DatabaseConnection:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self, retry_interval=5):
        while not check_internet_connection():
            logger.warning("No internet connection available. Retrying in {} seconds...".format(retry_interval))
            await asyncio.sleep(retry_interval)

        while self.client is None or self.db is None:
            try:
                self.client = motor.motor_asyncio.AsyncIOMotorClient(_ATLAS_URI)
                self.db = self.client.irrigation_system
                logger.info("Connected to MongoDB successfully.")
            except ConfigurationError as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}. Retrying in {retry_interval} seconds...")
                self.client = None
                self.db = None
                await asyncio.sleep(retry_interval)

    def is_connected(self):
        return self.client is not None and self.db is not None

# Create a global instance of the database connection
db_connection = DatabaseConnection()

# This allows other modules to import db_connection directly
__all__ = ['db_connection']