#!/bin/bash
# Script to fix tourism data issues

# Set up error handling
set -e

# Load environment variables
if [ -f .env ]; then
  source .env
fi

echo "Starting tourism data fix process..."

# Make the Python script executable
chmod +x scripts/run_fix_tourism_data.py

# Run the Python script
python3 scripts/run_fix_tourism_data.py

# Check if the script executed successfully
if [ $? -eq 0 ]; then
  echo "Tourism data fix completed successfully!"
else
  echo "Tourism data fix failed. Check the logs for details."
  exit 1
fi

# Run the verification script instead of direct psql queries
echo "Running validation script..."
python3 scripts/verify_tourism_data.py

echo "Tourism data fix process completed."
