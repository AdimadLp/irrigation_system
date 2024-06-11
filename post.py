from dotenv import load_dotenv
import os
import json
import uuid
import time
import socket
import board
import adafruit_dht
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging

logging.basicConfig(filename='database_upload.log', level=logging.INFO)
# Load environment variables from .env file
load_dotenv()

ATLAS_KEY = os.getenv("ATLAS_KEY")
ATLAS_USERNAME = os.getenv("ATLAS_USERNAME")
DEVICE_ID = os.getenv("DEVICE_ID")

# Define the sensor type and the pin it's connected to
dhtDevice = adafruit_dht.DHT11(board.D23)

try:
    uri = f"mongodb+srv://{ATLAS_USERNAME}:{ATLAS_KEY}@cluster0.pdaqcm3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri, server_api=ServerApi('1'))
except Exception as e:
    logging.error(f"An error occurred while trying to connect to the database: {e}")

def update_ip_address():
    # Get the local network IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip_address = s.getsockname()[0]
    s.close()

    database = client["DeviceList"]
    collection = database["DeviceIPAddresses"]

    query_filter = { "deviceid" : DEVICE_ID }
    result = collection.update_one(query_filter, { "$set": { "ip_address": local_ip_address } })

    if result.modified_count == 0:
        data = {
            "deviceid": DEVICE_ID,
            "ip_address": local_ip_address,
            "timestamp": datetime.now().isoformat(),
        }

        result = collection.insert_one(data)
        logging.info(f'IP address upload acknowledged: {result.acknowledged}')
    
    logging.info(f'IP address updated to {local_ip_address}')



def post_humidity_temperature(temperature, humidity):
    data = {
        "temperature": temperature,
        "humidity": humidity,
        
        "timestamp": datetime.now().isoformat(),
    }

    try:
        database = client["SensorData"]
        collection = database["TemperatureHumiditySensor"]

        result = collection.insert_one(data)
        logging.info(f'Data upload acknowledged: {result.acknowledged}')

    except Exception as e:
        logging.error(f"An error occurred while trying to post the humidity and temperature data to the database: {e}")

def post_data():
    update_ip_address()
    while True:
        try:
            # Read the temperature and humidity from the DHT11 sensor
            temperature = dhtDevice.temperature
            humidity = dhtDevice.humidity

            if humidity is not None and temperature is not None:
                # Define the data you want to send in the POST request
                post_humidity_temperature(temperature, humidity)
            else:
                print("Failed to retrieve data from humidity and temperature sensor")

            # Wait for 5 seconds before the next upload
            time.sleep(5)
        except RuntimeError as error:
            # If a RuntimeError is raised, print the error message and continue with the next iteration
            logging.error(f"An error occurred while trying to read the humidity and temperature data: {error}")
            continue
