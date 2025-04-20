#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create static directory if it doesn't exist
mkdir -p static

# Copy static files
if [ -d "app/static" ]; then
  cp -r app/static/* static/
fi

# Copy templates
if [ -d "app/templates" ]; then
  cp -r app/templates static/
fi 