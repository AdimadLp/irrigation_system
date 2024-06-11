import RPi.GPIO as GPIO
import time
import schedule
import logging
import datetime
import os
import pickle
from plant import Plant
import subprocess
import post
import threading

PLANTS = [ Plant("Efeu", 0.05, 2),
           Plant("Einblatt", 0.1, 3),
           Plant("Aloe Vera", 0.05, 4) ]

LAST_IRRIGATION_FILE = "last_irrigation.pkl"
LAST_IRRIGATED_PLANT_FILE = "last_irrigated_plant.pkl"

logging.basicConfig(filename='irrigation.log', level=logging.INFO)

def start_update_repo():
    subprocess.run(["python3", "update_repo.py"])

def get_last_irrigation_time():
    if os.path.exists(LAST_IRRIGATION_FILE):
        with open(LAST_IRRIGATION_FILE, 'rb') as f:
            return pickle.load(f)
    else:
        return None

def save_last_irrigation_time():
    with open(LAST_IRRIGATION_FILE, 'wb') as f:
        pickle.dump(datetime.datetime.now(), f)

def get_last_irrigated_plant():
    if os.path.exists(LAST_IRRIGATED_PLANT_FILE):
        with open(LAST_IRRIGATED_PLANT_FILE, 'rb') as f:
            return pickle.load(f)
    else:
        return None

def save_last_irrigated_plant(plant):
    with open(LAST_IRRIGATED_PLANT_FILE, 'wb') as f:
        pickle.dump(plant, f)

def irrigate_plants():
    last_irrigation_time = get_last_irrigation_time()
    if last_irrigation_time is None or last_irrigation_time.date() != datetime.datetime.now().date():
        
        last_irrigated_plant = get_last_irrigated_plant()
        if last_irrigated_plant is None:
            start_index = 0
        else:
            start_index = PLANTS.index(last_irrigated_plant) + 1

        for plant in PLANTS[start_index:]:
            logging.info(f'Irrigating {plant.name} at {datetime.datetime.now()}')
            plant.irrigate()
            logging.info(f'Irrigated {plant.name} at {datetime.datetime.now()}')
            save_last_irrigated_plant(plant)

        save_last_irrigation_time()

if __name__ == "__main__":
    '''
    GPIO.setmode(GPIO.BCM)

    for i in range(2, 10):
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i, GPIO.HIGH)
           
    schedule.every().day.at("21:35").do(irrigate_plants)

    while True:
        schedule.run_pending()
        time.sleep(1)
    '''
 

    # Start the repository update task in a separate thread
    repo_update_thread = threading.Thread(target=start_update_repo)
    repo_update_thread.start()

    post_thread = threading.Thread(target=post.post_data)
    post_thread.start()
    logging.info(f'Started post thread at {datetime.datetime.now()}')