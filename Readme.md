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
|   │   │   ├── plants.py
|   │   │   ├── pumps.py
|   │   │   ├── realtime_sensor_data.py
|   │   │   ├── schedules.py
|   │   │   ├── sensors.py
|   │   │   └── watering_logs.py
|   |   |
│   │   ├── __init__.py
│   │   └── connection.py
│   │
│   ├── helpers/
|   |   ├── __init__.py
|   |   ├── create_plant.py
|   |   ├── create_schedule.py
│   │   └── create_sensors.py
|   |
│   ├── services/
│   │   ├── __init__.py
|   |   ├── database_monitoring_service.py
│   │   ├── irrigation_service.py
│   │   └── sensor_service.py
│   │
|   ├── __init__.py
|   ├── logging_config.py
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
├── Readme.md
├── requirements.txt
└── update_repo.sh
```