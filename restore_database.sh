#!/bin/bash
# Database Restore Script for Egypt Tourism Chatbot
# This script restores a PostgreSQL database from a backup

# Set environment variables
export DB_NAME="egypt_chatbot"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
export DB_HOST="localhost"
export DB_PORT="5432"
export BACKUP_DIR="./backups"

# Parse command line arguments
LATEST=false
CREATE_DB=false
LIST=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --latest)
            LATEST=true
            shift
            ;;
        --create-db)
            CREATE_DB=true
            shift
            ;;
        --list)
            LIST=true
            shift
            ;;
        --backup-file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build the command
CMD="python restore_database.py"

if $LIST; then
    CMD="$CMD --list"
elif $LATEST; then
    CMD="$CMD --latest"
elif [ -n "$BACKUP_FILE" ]; then
    CMD="$CMD --backup-file $BACKUP_FILE"
else
    echo "Error: No backup file specified. Use --latest or --backup-file"
    exit 1
fi

if $CREATE_DB; then
    CMD="$CMD --create-db"
fi

# Run the Python restore script
echo "Starting database restore at $(date)"
eval $CMD

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo "Database restore completed successfully at $(date)"
    exit 0
else
    echo "Database restore failed at $(date)"
    exit 1
fi
