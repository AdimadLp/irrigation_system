from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import json
import uuid
import time
import socket
import board
import adafruit_dht


# Define the sensor type and the pin it's connected to
dhtDevice = adafruit_dht.DHT11(board.D22)

credential = DefaultAzureCredential()
key_vault_uri = "https://cosmo-key-vault.vault.azure.net/"
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

cosmos_url = secret_client.get_secret("cosmos-endpoint").value
cosmos_credential = secret_client.get_secret("cosmos-readwrite-key").value

client = CosmosClient(cosmos_url, credential=cosmos_credential)

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