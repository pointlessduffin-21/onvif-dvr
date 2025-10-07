#!/bin/bash

# Start ONVIF Viewer Application

echo "Starting ONVIF Viewer..."

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using default configuration."
fi

# Start the Flask application
python app.py
