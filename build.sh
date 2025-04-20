#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create static directory if it doesn't exist
mkdir -p static

# Copy static files
cp -r app/static/* static/

# Start the application
python -m hypercorn app.main:app --bind 0.0.0.0:8000 