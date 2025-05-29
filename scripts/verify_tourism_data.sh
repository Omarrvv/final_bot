#!/bin/bash
# Script to verify tourism data quality

# Set up error handling
set -e

# Load environment variables
if [ -f .env ]; then
  source .env
fi

echo "Starting tourism data verification process..."

# Make the Python script executable
chmod +x scripts/verify_tourism_data.py

# Run the Python script
python3 scripts/verify_tourism_data.py

# Check if the script executed successfully
if [ $? -eq 0 ]; then
  echo "Tourism data verification completed successfully! All checks passed."
else
  echo "Tourism data verification failed. Some checks did not pass. Check the logs for details."
  exit 1
fi

echo "Tourism data verification process completed."
