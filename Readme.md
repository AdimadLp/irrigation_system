# Irrigation System

This project uses various sensors and services to manage and control an irrigation system.

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
├── Readme.md
├── requirements.txt
└── update_repo.sh
```

## Running the Project

```bash
# Create a virtual environment
python3 -m venv .venv
# Activate the virtual environment
source .venv/bin/activate
# Install the required packages
pip install -r requirements.txt
# Run the main application
python -m app.main
```

## Testing

```bash
# Run main application in test mode
python -m app.main -test
# Run all tests
pytest tests/
# Run a specific test
pytest tests/test_irrigation_service.py
# Run a specific test function
pytest tests/test_irrigation_service.py::test_function_name
```

## Logging

The application uses the `logging` module to log messages. The log files are stored in the root directory of the project. The main log file is `app.log`, and error logs are stored in `error.log`. The logging configuration is set up in `app/logging_config.py`.

## Environment Variables

The application uses environment variables for configuration. The `.env` file contains the following variables:

- `DATABASE_URL`: The URL of the database.
- `LOG_LEVEL`: The logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
