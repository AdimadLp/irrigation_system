# Use an official Python runtime as a parent image
FROM ghcr.io/astral-sh/uv:debian-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
# Install system dependencies for RPi.GPIO and adafruit-circuitpython-dht if needed,
# though these might not work as expected inside a generic container without hardware access.
# For now, we'll assume they are handled or not strictly needed for the containerized version,
# or that this container is intended for an ARM-based host with GPIO access.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application directory into the container at /usr/src/app
COPY ./app ./app

# Copy the .env file, or manage configuration through environment variables
# For security, it's often better to pass sensitive data via environment variables at runtime
# COPY .env .

# Make port 6379 available if Redis is run within the same pod or for debugging
# This application acts as a client, so it doesn't expose ports itself.

# Define environment variables if needed (e.g., for .env settings)
# ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "./app/main.py"]