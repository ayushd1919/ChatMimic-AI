#!/bin/bash

echo "===================================="
echo "  Personal ChatBot - Quick Start"
echo "===================================="
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo

# Start the application
echo "===================================="
echo "  Starting Personal ChatBot..."
echo "  Open http://localhost:5000 in your browser"
echo "===================================="
echo
python app.py
