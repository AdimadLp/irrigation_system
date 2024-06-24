# Irrigation System

This project is an irrigation system that uses various sensors and services to manage and control an irrigation system.

## Project Structure
```bash
irrigation_system/
|
|
├── app/
│   ├── database/
|   |   ├── models
|   │   │   ├── __init__.py
|   │   │   ├── irrigation_controller.py
|   │   │   ├── plant.py
|   │   │   ├── pump.py
|   │   │   ├── realtime_sensor_data.py
|   │   │   ├── schedule.py
|   │   │   ├── sensor.py
|   │   │   └── watering_log.py
|   |   |
│   │   ├── __init__.py
│   │   └── connection.py
│   │
│   ├── helpers/
|   |   ├── __init__.py
│   │   └── create_plant.py
|   |
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