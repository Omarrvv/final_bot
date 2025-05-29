# Egypt Tourism Chatbot: Database Backup and Restore Procedures

This document outlines the procedures for backing up and restoring the PostgreSQL database for the Egypt Tourism Chatbot.

## Backup Procedure

### Automated Backup

The automated backup process uses the `backup_database.sh` script, which wraps the Python script `backup_database.py`. This script:

1. Creates a timestamped backup of the PostgreSQL database
2. Stores it in the `backups` directory
3. Verifies the backup was created successfully
4. Cleans up old backups (older than 7 days by default)

#### Running the Automated Backup

```bash
./backup_database.sh
```

#### Environment Variables

The backup script uses the following environment variables, which can be modified in the `backup_database.sh` script:

- `DB_NAME`: Database name (default: "egypt_chatbot")
- `DB_USER`: Database user (default: "postgres")
- `DB_PASSWORD`: Database password (default: "postgres")
- `DB_HOST`: Database host (default: "localhost")
- `DB_PORT`: Database port (default: "5432")
- `BACKUP_DIR`: Directory to store backups (default: "./backups")
- `BACKUP_RETENTION_DAYS`: Number of days to keep backups (default: "7")

### Manual Backup

If you need to create a manual backup, you can use the `pg_dump` command directly:

```bash
# Set the PGPASSWORD environment variable
export PGPASSWORD=postgres

# Create a backup
pg_dump -h localhost -p 5432 -U postgres -F c -b -v -f backups/egypt_chatbot_manual.sql egypt_chatbot

# Unset the PGPASSWORD environment variable
unset PGPASSWORD
```

## Restore Procedure

### Automated Restore

To restore a database from a backup, use the following procedure:

1. Ensure the target database exists (create it if necessary)
2. Use the `pg_restore` command to restore the backup

```bash
# Create the database if it doesn't exist
createdb -h localhost -p 5432 -U postgres egypt_chatbot

# Restore the database
pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot -c -v backups/egypt_chatbot_20250504_062903.sql
```

### Manual Restore

For a manual restore with more control:

```bash
# Set the PGPASSWORD environment variable
export PGPASSWORD=postgres

# Drop the existing database (if necessary)
dropdb -h localhost -p 5432 -U postgres egypt_chatbot

# Create a new database
createdb -h localhost -p 5432 -U postgres egypt_chatbot

# Restore the database
pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot -v backups/egypt_chatbot_20250504_062903.sql

# Unset the PGPASSWORD environment variable
unset PGPASSWORD
```

## Backup Verification

To verify a backup is valid and can be restored:

```bash
# Create a test database
createdb -h localhost -p 5432 -U postgres egypt_chatbot_test

# Restore the backup to the test database
pg_restore -h localhost -p 5432 -U postgres -d egypt_chatbot_test -v backups/egypt_chatbot_20250504_062903.sql

# Connect to the test database and verify the data
psql -h localhost -p 5432 -U postgres -d egypt_chatbot_test -c "SELECT COUNT(*) FROM attractions;"

# Drop the test database when done
dropdb -h localhost -p 5432 -U postgres egypt_chatbot_test
```

## Backup Storage

Backups are stored in the `backups` directory by default. For production environments, consider:

1. Copying backups to a remote server
2. Uploading backups to cloud storage (AWS S3, Google Cloud Storage, etc.)
3. Implementing encryption for sensitive data

Example script to copy backups to a remote server:

```bash
# Copy the latest backup to a remote server
scp backups/egypt_chatbot_*.sql user@remote-server:/path/to/backup/storage/
```

## Backup Schedule

For production environments, implement a regular backup schedule:

1. Daily backups: Run the backup script daily via cron
2. Weekly full backups: Create a complete backup once a week
3. Monthly archives: Archive monthly backups for long-term storage

Example cron entry for daily backups:

```
# Run backup daily at 2:00 AM
0 2 * * * /path/to/egypt-chatbot/backup_database.sh >> /path/to/egypt-chatbot/logs/backup.log 2>&1
```

## Emergency Recovery Procedure

In case of database corruption or data loss:

1. Stop the application to prevent further data changes
2. Identify the most recent valid backup
3. Restore the database using the procedure above
4. Verify the restored data
5. Restart the application

## Conclusion

Regular backups are essential for data protection. Test the backup and restore procedures regularly to ensure they work correctly when needed.
