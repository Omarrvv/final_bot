#!/bin/bash
# Database Backup Script for Egypt Tourism Chatbot
# This script creates a backup of the PostgreSQL database using the Python script

# Set environment variables
export DB_NAME="egypt_chatbot"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
export DB_HOST="localhost"
export DB_PORT="5432"
export BACKUP_DIR="./backups"
export BACKUP_RETENTION_DAYS="7"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run the Python backup script
echo "Starting database backup at $(date)"
python backup_database.py

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Database backup completed successfully at $(date)"
    exit 0
else
    echo "Database backup failed at $(date)"
    exit 1
fi
