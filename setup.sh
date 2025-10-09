#!/bin/bash

# ONVIF Viewer Setup Script for macOS

echo "================================================"
echo "ONVIF Viewer Setup"
echo "================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file to configure your settings."
fi

# Initialize database
echo "Initializing database..."
python init_db.py

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "To start the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: python app.py"
echo "3. Open your browser to: http://localhost:5000"
echo ""
echo "Supported ONVIF Profiles:"
echo "  - Profile S: Video streaming"
echo "  - Profile G: Video recording and storage"
echo "  - Profile C: Physical access control"
echo "  - Profile A: Broader access control configuration"
echo "  - Profile T: Advanced video streaming"
echo "  - Profile M: Metadata and events for analytics"
echo "  - Profile D: Access control peripherals"
echo ""
