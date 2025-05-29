#!/bin/bash

# Egypt Chatbot Schema Migration Script
# This script runs all migration files in the correct order

# Set variables
DB_NAME="egypt_chatbot"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
MIGRATIONS_DIR="./migrations"
BACKUP_DIR="./backups"
LOG_DIR="./logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" >> "$LOG_DIR/migration_$TIMESTAMP.log"
}

# Function to check if a command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        log "SUCCESS: $1"
    else
        log "ERROR: $1"
        log "Migration failed. Exiting."
        exit 1
    fi
}

# Start migration process
log "Starting Egypt Chatbot schema migration"

# Create database backup before migration
log "Creating database backup..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F c -b -v -f "$BACKUP_DIR/${DB_NAME}_backup_$TIMESTAMP.dump" "$DB_NAME"
check_success "Database backup created at $BACKUP_DIR/${DB_NAME}_backup_$TIMESTAMP.dump"

# Run each migration file in order
for migration_file in $(ls -1 "$MIGRATIONS_DIR" | sort); do
    log "Running migration: $migration_file"
    
    # Execute the migration
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATIONS_DIR/$migration_file" > "$LOG_DIR/${migration_file%.sql}_$TIMESTAMP.log" 2>&1
    
    # Check if migration succeeded
    if [ $? -eq 0 ]; then
        log "Migration $migration_file completed successfully"
    else
        log "Migration $migration_file failed. Check log at $LOG_DIR/${migration_file%.sql}_$TIMESTAMP.log"
        log "Attempting to restore from backup..."
        
        # Restore from backup
        pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$BACKUP_DIR/${DB_NAME}_backup_$TIMESTAMP.dump"
        
        if [ $? -eq 0 ]; then
            log "Database restored successfully from backup"
        else
            log "Failed to restore database from backup. Manual intervention required."
        fi
        
        exit 1
    fi
done

log "All migrations completed successfully"

# Create post-migration backup
log "Creating post-migration database backup..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F c -b -v -f "$BACKUP_DIR/${DB_NAME}_post_migration_$TIMESTAMP.dump" "$DB_NAME"
check_success "Post-migration database backup created at $BACKUP_DIR/${DB_NAME}_post_migration_$TIMESTAMP.dump"

log "Migration process completed"
exit 0
