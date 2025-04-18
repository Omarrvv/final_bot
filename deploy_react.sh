#!/bin/bash

# Deploy script for Egypt Tourism Chatbot React Frontend
echo "Deploying React Frontend to Flask Backend..."

# Navigate to the React frontend directory
cd "$(dirname "$0")/react-frontend"

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the React app
echo "Building React app..."
npm run build

# Create the destination directory if it doesn't exist
mkdir -p ../src/static

# Copy the build to the Flask static folder
echo "Copying build files to Flask static folder..."
cp -r build/* ../src/static/

echo "Deployment complete! You can now run the Flask app to serve the React frontend."
echo "Run 'flask run' from the root directory to start the server." 