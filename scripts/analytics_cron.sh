#!/bin/bash
# Cron script to run analytics cleanup tasks

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Go to the project root directory
cd "$SCRIPT_DIR/.."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run analytics cleanup task
echo "$(date): Running analytics cleanup task" >> logs/cron.log
python -m src.tasks.analytics_cleanup >> logs/cron.log 2>&1

# Exit with the status of the cleanup task
exit $? 