#!/bin/bash

# Run the Egypt Tourism Chatbot in production mode
# This script builds the React frontend and starts the FastAPI backend

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Change to project root directory
cd "$(dirname "$0")"

# Build the React frontend
echo "Building React frontend..."
cd react-frontend

# Update .env file for production
echo "REACT_APP_API_URL=/api" > .env

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build the frontend
npm run build
if [ $? -ne 0 ]; then
    echo "Failed to build React frontend"
    exit 1
fi

echo "React frontend built successfully"
cd ..

# Start the backend
echo "Starting FastAPI backend in production mode..."
python -m src.main

# Note: In a real production environment, you would use a proper WSGI server like uvicorn or gunicorn
# Example: uvicorn src.main:app --host 0.0.0.0 --port 5050 --workers 4
