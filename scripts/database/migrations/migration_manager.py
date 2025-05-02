#!/usr/bin/env python3
"""
Database Migration Manager

Handles database migrations between SQLite and PostgreSQL, including:
- Schema validation and synchronization
- Data migration with type conversion
- Progress tracking and validation
- Error handling and rollback
"""

import os
import sys
import json
import logging
import sqlite3
import psycopg2
from datetime import datetime
from typing import Dict, List, Any, Optional
from psycopg2.extras import Json, RealDictCursor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("migration_manager")

class MigrationManager:
    def __init__(self, sqlite_path: str, postgres_uri: str):
        self.sqlite_path = sqlite_path
        self.postgres_uri = postgres_uri
        self.sqlite_conn = None
        self.postgres_conn = None

    def connect(self) -> None:
        """Establish connections to both databases"""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")

            self.postgres_conn = psycopg2.connect(self.postgres_uri)
            self.postgres_conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            self.cleanup()
            raise

    def cleanup(self) -> None:
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()
        logger.info("Database connections closed")

    def get_table_schema(self, table: str) -> Dict[str, Any]:
        """Get schema information for a table from both databases"""
        sqlite_schema = self._get_sqlite_schema(table)
        postgres_schema = self._get_postgres_schema(table)
        return {
            "sqlite": sqlite_schema,
            "postgres": postgres_schema
        }

    def _get_sqlite_schema(self, table: str) -> Dict[str, str]:
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return {row[1]: row[2] for row in cursor.fetchall()}

    def _get_postgres_schema(self, table: str) -> Dict[str, str]:
        cursor = self.postgres_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
        """, (table,))
        return {row[0]: row[1] for row in cursor.fetchall()}

    def migrate_table(self, table: str, batch_size: int = 1000) -> int:
        """Migrate data from SQLite to PostgreSQL for a single table"""
        try:
            # Get schema information
            schema = self.get_table_schema(table)
            
            # Get total count
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_rows = sqlite_cursor.fetchone()[0]
            
            if total_rows == 0:
                logger.info(f"Table {table} is empty - skipping")
                return 0

            migrated = 0
            for offset in range(0, total_rows, batch_size):
                rows = self._fetch_batch(table, offset, batch_size)
                if rows:
                    migrated += self._insert_batch(table, rows, schema["postgres"])
                    self.postgres_conn.commit()
                    logger.info(f"Migrated {migrated}/{total_rows} rows in {table}")

            return migrated

        except Exception as e:
            self.postgres_conn.rollback()
            logger.error(f"Error migrating table {table}: {e}")
            raise

    def _fetch_batch(self, table: str, offset: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch a batch of rows from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"SELECT * FROM {table} LIMIT {limit} OFFSET {offset}")
        return [dict(row) for row in cursor.fetchall()]

    def _insert_batch(self, table: str, rows: List[Dict[str, Any]], schema: Dict[str, str]) -> int:
        """Insert a batch of rows into PostgreSQL"""
        if not rows:
            return 0

        # Convert data types based on PostgreSQL schema
        converted_rows = []
        for row in rows:
            converted_row = {}
            for col, val in row.items():
                if col in schema:
                    converted_row[col] = self._convert_value(val, schema[col])
            converted_rows.append(converted_row)

        # Build and execute insert query
        columns = converted_rows[0].keys()
        placeholders = ["%s"] * len(columns)
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT DO NOTHING
        """

        cursor = self.postgres_conn.cursor()
        psycopg2.extras.execute_batch(
            cursor,
            query,
            [tuple(row[col] for col in columns) for row in converted_rows]
        )

        return len(converted_rows)

    def _convert_value(self, value: Any, target_type: str) -> Any:
        """Convert a value to the appropriate PostgreSQL type"""
        if value is None:
            return None

        try:
            if target_type == 'jsonb' and isinstance(value, str):
                return Json(json.loads(value))
            elif target_type == 'boolean':
                return bool(value)
            elif target_type == 'integer':
                return int(value)
            elif target_type == 'numeric':
                return float(value)
            elif target_type.startswith('timestamp'):
                # Handle timestamp conversion
                if isinstance(value, str):
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                return value
            else:
                return value

        except Exception as e:
            logger.warning(f"Error converting value {value} to {target_type}: {e}")
            return value

    def validate_migration(self, table: str) -> bool:
        """Validate migration results for a table"""
        try:
            # Compare row counts
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]

            pg_cursor = self.postgres_conn.cursor()
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]

            is_valid = sqlite_count == pg_count
            message = f"Validation for {table}: {sqlite_count} rows (SQLite) vs {pg_count} rows (PostgreSQL)"
            if is_valid:
                logger.info(f"✅ {message}")
            else:
                logger.warning(f"❌ {message}")

            return is_valid

        except Exception as e:
            logger.error(f"Error validating migration for {table}: {e}")
            return False