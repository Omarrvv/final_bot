#!/bin/bash

# Run the Egypt Tourism Chatbot in development mode
# This script starts both the React frontend and the FastAPI backend

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export REACT_APP_API_URL=http://localhost:5050/api

# Function to kill processes on exit
cleanup() {
    echo "Shutting down..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Killing backend process $BACKEND_PID"
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Killing frontend process $FRONTEND_PID"
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup INT TERM

# Start the backend
echo "Starting FastAPI backend..."
cd "$(dirname "$0")"
python -m src.main &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Wait a bit for the backend to start
sleep 2

# Start the frontend
echo "Starting React frontend..."
cd react-frontend
npm start &
FRONTEND_PID=$!
echo "Frontend started with PID $FRONTEND_PID"

echo "Development environment is running!"
echo "Backend: http://localhost:5050"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
