#!/bin/bash

# Build and Run Script for Egypt Tourism Chatbot Frontend
# This script builds the React frontend and copies it to the Flask static directory

echo "=== Egypt Tourism Chatbot Frontend Build Script ==="
echo "Building React frontend..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Build the React app
echo "Building React app..."
npm run build

# Check if build was successful
if [ $? -ne 0 ]; then
  echo "Build failed. Please check the errors above."
  exit 1
fi

# Create static directory in Flask app if it doesn't exist
if [ ! -d "../src/static" ]; then
  echo "Creating static directory in Flask app..."
  mkdir -p ../src/static
fi

# Copy build files to Flask static directory
echo "Copying build files to Flask static directory..."
cp -r build/* ../src/static/

echo "Build and copy completed successfully!"
echo "You can now run the Flask app to serve the frontend."
echo "The chatbot should be accessible at http://localhost:5000"
