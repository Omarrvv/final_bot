#!/bin/bash
# Simple script to run the Egypt Tourism Chatbot

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the PYTHONPATH to include the project directory
export PYTHONPATH=$DIR

echo "Starting Egypt Tourism Chatbot..."
echo "PYTHONPATH set to: $PYTHONPATH"

# Run the application using the proper module path
cd $DIR
python -m src.main

# Exit with the same status as the Python command
exit $?
