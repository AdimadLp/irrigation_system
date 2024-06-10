from azure.cosmos import CosmosClient
from dotenv import load_dotenv
import os
import json
import uuid
import time
import socket
import board
import adafruit_dht

# Load environment variables from .env file
load_dotenv()

# Define the sensor type and the pin it's connected to
dhtDevice = adafruit_dht.DHT11(board.D16)

cosmos_connection_string = os.getenv("COSMOS_CONNECTION_STRING")

client = CosmosClient.from_connection_string(cosmos_connection_string)

# Get the container
database = client.get_database_client("PublicMonitorData")
container = database.get_container_client("PublicMonitorDataContainer")

# Get the local network IP address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip_address = s.getsockname()[0]
s.close()
def post_data():
    while True:
        # Read the temperature and humidity from the DHT11 sensor
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity

        print(f"Temperature: {temperature} C")
        print(f"Humidity: {humidity}%")

        if humidity is not None and temperature is not None:
            # Define the data you want to send in the POST request
            data = {
                "id": str(uuid.uuid4()),
                "temperature": temperature,
                "humidity": humidity,
                "ip_address": local_ip_address
            }

            # Convert the data to JSON format
            data_json = json.dumps(data)

            # Add the item to the container
            container.upsert_item(body=data)
        else:
            print("Failed to retrieve data from humidity and temperature sensor")

        # Wait for 5 seconds before the next upload
        time.sleep(5)