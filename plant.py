import time
import RPi.GPIO as GPIO

LPM = 0.1 # liters per minute

class Plant:
    def __init__(self, name, water_needed, port):
        self.name = name
        self.water_needed = water_needed
        self.port = port
    
    def irrigate(self):
        GPIO.output(self.port, GPIO.LOW)
        time.sleep(60 * self.water_needed / LPM)
        GPIO.output(self.port, GPIO.HIGH)
