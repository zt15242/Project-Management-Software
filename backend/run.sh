#!/bin/bash

echo "Starting Project Management System Backend..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""

# Create uploads directory
if [ ! -d "uploads" ]; then
    mkdir uploads
fi

# Run the application
echo "Starting server at http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
python main.py

