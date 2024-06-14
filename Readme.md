# Irrigation System

This project is an irrigation system that uses various sensors and services to manage and control an irrigation system.

## Project Structure
```bash
irrigation_system/
|
|
├── app/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── queries.py
│   │
│   ├── models
│   │   ├── __init__.py
│   │   ├── environment_sensor.py
│   │   ├── irrigation_controller.py
│   │   ├── plant_sensor.py
│   │   ├── plant.py
│   │   ├── pump.py
│   │   └── schedule.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── irrigation_service.py
│   │   └── sensor_service.py
│   │
|   ├── __init__.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_irrigation_service.py
│   └── test_sensor_service
│
└── .env
```