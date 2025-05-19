# Irrigation System

This project uses various microcontrollers with sensors and actuators to manage and control an irrigation system.

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
|   │   │   ├── logs.py
|   │   │   ├── plants.py
|   │   │   ├── pumps.py
|   │   │   ├── realtime_sensor_data.py
|   │   │   ├── schedules.py
|   │   │   └── sensors.py
|   |   |
│   │   └── database.py
│   │
│   ├── helpers/
|   |   ├── __init__.py
|   |   ├── create_plant.py
|   |   ├── create_pump.py
|   |   ├── create_schedule.py
│   │   └── create_sensors.py
|   |
│   ├── services/
│   │   ├── __init__.py
|   |   ├── database_service.py
│   │   ├── irrigation_service.py
│   │   └── sensor_service.py
│   │
|   ├── __init__.py
|   ├── logging_config.py
|   ├── create_documents.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_irrigation_service.py
│   └── test_sensor_service
│
├── .env
├── app.log
├── error.log
├── README.md
└── pyproject.toml
```
