#!/usr/bin/env python3
"""
Database Maintenance and Schema Validation

Handles database maintenance tasks including:
- Schema validation and synchronization
- Database vacuuming and optimization
- Index maintenance and statistics updates
- Health checks and monitoring
"""

import os
import sys
import logging
import psycopg2
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_maintenance')

class DatabaseMaintenance:
    def __init__(self, sqlite_path: str, postgres_uri: str):
        self.sqlite_path = sqlite_path
        self.postgres_uri = postgres_uri
        self.sqlite_conn = None
        self.postgres_conn = None

    def connect(self) -> None:
        """Establish database connections"""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.postgres_conn = psycopg2.connect(self.postgres_uri)
            logger.info("Database connections established")
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

    def validate_schema(self, table: str) -> List[Dict[str, Any]]:
        """Compare schema between SQLite and PostgreSQL for a table"""
        differences = []
        
        # Get schemas
        sqlite_schema = self._get_sqlite_schema(table)
        postgres_schema = self._get_postgres_schema(table)
        
        # Compare column presence
        all_columns = set(sqlite_schema.keys()) | set(postgres_schema.keys())
        
        for column in all_columns:
            if column not in sqlite_schema:
                differences.append({
                    'type': 'missing_column',
                    'database': 'sqlite',
                    'table': table,
                    'column': column
                })
            elif column not in postgres_schema:
                differences.append({
                    'type': 'missing_column',
                    'database': 'postgres',
                    'table': table,
                    'column': column
                })
            elif sqlite_schema[column] != postgres_schema[column]:
                differences.append({
                    'type': 'type_mismatch',
                    'table': table,
                    'column': column,
                    'sqlite_type': sqlite_schema[column],
                    'postgres_type': postgres_schema[column]
                })
        
        return differences

    def _get_sqlite_schema(self, table: str) -> Dict[str, str]:
        """Get SQLite table schema"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return {row[1]: row[2].upper() for row in cursor.fetchall()}

    def _get_postgres_schema(self, table: str) -> Dict[str, str]:
        """Get PostgreSQL table schema"""
        cursor = self.postgres_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
        """, (table,))
        return {row[0]: row[1].upper() for row in cursor.fetchall()}

    def vacuum_database(self) -> None:
        """Perform VACUUM on both databases"""
        try:
            # SQLite VACUUM
            logger.info("Running VACUUM on SQLite database...")
            self.sqlite_conn.execute("VACUUM")
            logger.info("SQLite VACUUM completed")

            # PostgreSQL VACUUM ANALYZE
            logger.info("Running VACUUM ANALYZE on PostgreSQL database...")
            old_isolation_level = self.postgres_conn.isolation_level
            self.postgres_conn.set_isolation_level(0)
            cursor = self.postgres_conn.cursor()
            cursor.execute("VACUUM ANALYZE")
            self.postgres_conn.set_isolation_level(old_isolation_level)
            logger.info("PostgreSQL VACUUM completed")

        except Exception as e:
            logger.error(f"Error during VACUUM: {e}")
            raise

    def maintain_indexes(self) -> None:
        """Maintain database indexes"""
        try:
            # PostgreSQL index maintenance
            cursor = self.postgres_conn.cursor()
            
            # Get list of indexes
            cursor.execute("""
                SELECT schemaname, tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
            """)
            
            for schema, table, index in cursor.fetchall():
                logger.info(f"Reindexing {schema}.{table}.{index}")
                cursor.execute(f"REINDEX INDEX {schema}.{index}")
            
            # Update statistics
            cursor.execute("ANALYZE VERBOSE")
            logger.info("PostgreSQL index maintenance completed")

        except Exception as e:
            logger.error(f"Error during index maintenance: {e}")
            raise

    def check_database_health(self) -> Dict[str, Any]:
        """Perform health checks on both databases"""
        health_status = {
            'sqlite': self._check_sqlite_health(),
            'postgres': self._check_postgres_health(),
            'timestamp': datetime.now().isoformat()
        }
        return health_status

    def _check_sqlite_health(self) -> Dict[str, Any]:
        """Check SQLite database health"""
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            size_bytes = page_count * page_size
            
            return {
                'status': 'healthy' if integrity == 'ok' else 'unhealthy',
                'integrity_check': integrity,
                'size_bytes': size_bytes,
                'errors': None
            }

        except Exception as e:
            return {
                'status': 'error',
                'integrity_check': None,
                'size_bytes': None,
                'errors': str(e)
            }

    def _check_postgres_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database health"""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Check connection status
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("""
                SELECT pg_database_size(current_database())
            """)
            size_bytes = cursor.fetchone()[0]
            
            # Check for long-running queries
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE state = 'active' 
                AND now() - query_start > interval '5 minutes'
            """)
            long_running_queries = cursor.fetchone()[0]
            
            return {
                'status': 'healthy',
                'version': version,
                'size_bytes': size_bytes,
                'long_running_queries': long_running_queries,
                'errors': None
            }

        except Exception as e:
            return {
                'status': 'error',
                'version': None,
                'size_bytes': None,
                'long_running_queries': None,
                'errors': str(e)
            }

def main():
    """CLI entry point for database maintenance tasks"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database maintenance tools")
    parser.add_argument(
        "--sqlite-path",
        default=os.getenv("SQLITE_PATH", "./data/egypt_chatbot.db"),
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--postgres-uri",
        default=os.getenv("POSTGRES_URI", "postgresql://localhost:5432/egypt_chatbot"),
        help="PostgreSQL connection URI"
    )
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate schema between databases"
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Perform VACUUM operation"
    )
    parser.add_argument(
        "--maintain-indexes",
        action="store_true",
        help="Maintain database indexes"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform database health check"
    )
    
    args = parser.parse_args()
    
    maintenance = DatabaseMaintenance(args.sqlite_path, args.postgres_uri)
    
    try:
        maintenance.connect()
        
        if args.validate_schema:
            # Get all tables
            cursor = maintenance.sqlite_conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                differences = maintenance.validate_schema(table)
                if differences:
                    logger.warning(f"Schema differences found in table {table}:")
                    for diff in differences:
                        logger.warning(f"  {diff}")
                else:
                    logger.info(f"No schema differences found in table {table}")
        
        if args.vacuum:
            maintenance.vacuum_database()
        
        if args.maintain_indexes:
            maintenance.maintain_indexes()
        
        if args.health_check:
            health = maintenance.check_database_health()
            logger.info("Health check results:")
            logger.info(f"SQLite: {health['sqlite']['status']}")
            logger.info(f"PostgreSQL: {health['postgres']['status']}")
            
            if health['sqlite'].get('errors'):
                logger.error(f"SQLite errors: {health['sqlite']['errors']}")
            if health['postgres'].get('errors'):
                logger.error(f"PostgreSQL errors: {health['postgres']['errors']}")
    
    except Exception as e:
        logger.error(f"Maintenance failed: {e}")
        sys.exit(1)
    
    finally:
        maintenance.cleanup()

if __name__ == "__main__":
    main()