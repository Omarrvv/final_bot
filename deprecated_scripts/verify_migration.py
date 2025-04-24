#!/usr/bin/env python3
"""
Verify SQLite to PostgreSQL Migration

This script verifies that data has been correctly migrated from SQLite to PostgreSQL
by comparing record counts, sampling records, and validating field integrity.

Usage:
    python verify_migration.py [--verbose]

Options:
    --verbose     Show detailed comparison information, including field-by-field checks
"""

import os
import sys
import json
import sqlite3
import psycopg2
import argparse
import logging
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from tabulate import tabulate
import random
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    # Get database URIs
    sqlite_uri = os.environ.get("DATABASE_URI", "sqlite:///./data/egypt_chatbot.db")
    postgres_uri = os.environ.get("POSTGRES_URI", 
                                  "postgresql://postgres:password@localhost:5432/egyptchatbot")
    
    # Extract SQLite path
    if sqlite_uri.startswith("sqlite:///"):
        sqlite_path = sqlite_uri.replace("sqlite:///", "")
    else:
        sqlite_path = sqlite_uri
    
    return {
        "sqlite_path": sqlite_path,
        "postgres_uri": postgres_uri
    }

def connect_to_sqlite(sqlite_path):
    """
    Connect to SQLite database.
    
    Args:
        sqlite_path: Path to SQLite database
        
    Returns:
        tuple: (connection, cursor)
    """
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        logger.info(f"Connected to SQLite database: {sqlite_path}")
        return conn, cursor
    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        sys.exit(1)

def connect_to_postgres(postgres_uri):
    """
    Connect to PostgreSQL database.
    
    Args:
        postgres_uri: PostgreSQL connection URI
        
    Returns:
        tuple: (connection, cursor)
    """
    try:
        conn = psycopg2.connect(postgres_uri, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        logger.info(f"Connected to PostgreSQL database")
        return conn, cursor
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        sys.exit(1)

def get_tables(sqlite_cursor, postgres_cursor):
    """
    Get the list of tables from both databases.
    
    Args:
        sqlite_cursor: SQLite cursor
        postgres_cursor: PostgreSQL cursor
        
    Returns:
        tuple: (sqlite_tables, postgres_tables)
    """
    # Get SQLite tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    # Get PostgreSQL tables
    postgres_cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        AND table_type='BASE TABLE'
    """)
    postgres_tables = [row['table_name'] for row in postgres_cursor.fetchall()]
    
    return sqlite_tables, postgres_tables

def compare_record_counts(sqlite_cursor, postgres_cursor, tables):
    """
    Compare record counts between SQLite and PostgreSQL tables.
    
    Args:
        sqlite_cursor: SQLite cursor
        postgres_cursor: PostgreSQL cursor
        tables: List of tables to compare
        
    Returns:
        list: Comparison results
    """
    results = []
    
    for table in tables:
        # Get SQLite count
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        # Get PostgreSQL count
        postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        postgres_count = postgres_cursor.fetchone()['count']
        
        # Determine match status
        status = "✅" if sqlite_count == postgres_count else "❌"
        
        results.append({
            "table": table,
            "sqlite_count": sqlite_count,
            "postgres_count": postgres_count,
            "status": status
        })
    
    return results

def get_sqlite_columns(sqlite_cursor, table):
    """Get column information for SQLite table."""
    sqlite_cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in sqlite_cursor.fetchall()]

def get_postgres_columns(postgres_cursor, table):
    """Get column information for PostgreSQL table."""
    postgres_cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='{table}'
    """)
    return [row['column_name'] for row in postgres_cursor.fetchall()]

def compare_sample_records(sqlite_cursor, postgres_cursor, table, verbose=False):
    """
    Compare sample records between SQLite and PostgreSQL.
    
    Args:
        sqlite_cursor: SQLite cursor
        postgres_cursor: PostgreSQL cursor
        table: Table to compare
        verbose: Whether to show detailed field comparison
        
    Returns:
        dict: Comparison results
    """
    # Get primary key column (assume 'id' is primary key if not found)
    sqlite_cursor.execute(f"PRAGMA table_info({table})")
    pk_column = next((row[1] for row in sqlite_cursor.fetchall() if row[5] == 1), 'id')
    
    # Get columns for both databases
    sqlite_columns = get_sqlite_columns(sqlite_cursor, table)
    postgres_columns = get_postgres_columns(postgres_cursor, table)
    
    # Find common columns for comparison
    common_columns = list(set(sqlite_columns) & set(postgres_columns))
    
    # Get all IDs from SQLite
    sqlite_cursor.execute(f"SELECT {pk_column} FROM {table}")
    all_ids = [row[0] for row in sqlite_cursor.fetchall()]
    
    # Skip if no records
    if not all_ids:
        return {
            "table": table,
            "sampled": 0,
            "matches": 0,
            "mismatches": 0,
            "details": []
        }
    
    # Sample records (max 5 or 10% of records, whichever is smaller)
    sample_size = min(5, max(1, int(len(all_ids) * 0.1)))
    sample_ids = random.sample(all_ids, min(sample_size, len(all_ids)))
    
    matches = 0
    mismatches = 0
    details = []
    
    for record_id in sample_ids:
        # Create a placeholder string with the correct number of placeholders
        sqlite_cursor.execute(
            f"SELECT {', '.join(common_columns)} FROM {table} WHERE {pk_column} = ?", 
            (record_id,)
        )
        sqlite_record = sqlite_cursor.fetchone()
        
        postgres_cursor.execute(
            f"SELECT {', '.join(common_columns)} FROM {table} WHERE {pk_column} = %s",
            (record_id,)
        )
        postgres_record = postgres_cursor.fetchone()
        
        if not sqlite_record or not postgres_record:
            mismatches += 1
            details.append({
                "id": record_id,
                "status": "❌ Not found in one database",
                "fields": {}
            })
            continue
        
        # Convert SQLite record to dict for comparison
        sqlite_dict = dict(sqlite_record)
        
        # Compare fields
        field_matches = []
        record_match = True
        
        for col in common_columns:
            sqlite_value = sqlite_dict[col]
            postgres_value = postgres_record[col]
            
            # Handle JSON data (stored as string in SQLite, JSONB in PostgreSQL)
            if col == 'data' and sqlite_value:
                try:
                    if isinstance(sqlite_value, str):
                        sqlite_value = json.loads(sqlite_value)
                    if isinstance(postgres_value, str):
                        postgres_value = json.loads(postgres_value)
                except:
                    pass
            
            # Compare values, handling special cases
            values_match = sqlite_value == postgres_value
            
            # For numeric values, allow small differences
            if not values_match and isinstance(sqlite_value, (int, float)) and isinstance(postgres_value, (int, float)):
                if abs(sqlite_value - postgres_value) < 0.001:
                    values_match = True
                    
            field_status = "✅" if values_match else "❌"
            
            if not values_match:
                record_match = False
            
            if verbose:
                field_matches.append({
                    "column": col,
                    "sqlite_value": sqlite_value,
                    "postgres_value": postgres_value,
                    "status": field_status
                })
        
        if record_match:
            matches += 1
        else:
            mismatches += 1
        
        details.append({
            "id": record_id,
            "status": "✅" if record_match else "❌",
            "fields": field_matches if verbose else {}
        })
    
    return {
        "table": table,
        "sampled": len(sample_ids),
        "matches": matches,
        "mismatches": mismatches,
        "details": details
    }

def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(description="Verify SQLite to PostgreSQL migration")
    parser.add_argument("--verbose", action="store_true", help="Show detailed comparison")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Connect to databases
    sqlite_conn, sqlite_cursor = connect_to_sqlite(config["sqlite_path"])
    postgres_conn, postgres_cursor = connect_to_postgres(config["postgres_uri"])
    
    try:
        # Get tables from both databases
        sqlite_tables, postgres_tables = get_tables(sqlite_cursor, postgres_cursor)
        common_tables = list(set(sqlite_tables) & set(postgres_tables))
        
        logger.info(f"Found {len(common_tables)} common tables: {', '.join(common_tables)}")
        
        # Compare record counts
        count_results = compare_record_counts(sqlite_cursor, postgres_cursor, common_tables)
        
        # Display record count comparison
        print("\n=== Table Record Count Comparison ===")
        table_data = [[r["table"], r["sqlite_count"], r["postgres_count"], r["status"]] for r in count_results]
        print(tabulate(table_data, headers=["Table", "SQLite Count", "PostgreSQL Count", "Match"]))
        
        # Sample records for detailed comparison
        all_matches = 0
        all_mismatches = 0
        
        print("\n=== Record Sampling Results ===")
        sample_data = []
        
        for table in common_tables:
            sample_result = compare_sample_records(
                sqlite_cursor, postgres_cursor, table, verbose=args.verbose
            )
            all_matches += sample_result["matches"]
            all_mismatches += sample_result["mismatches"]
            
            sample_data.append([
                sample_result["table"],
                sample_result["sampled"],
                sample_result["matches"],
                sample_result["mismatches"],
                "✅" if sample_result["mismatches"] == 0 else "❌"
            ])
            
            # Print detailed field comparisons if verbose
            if args.verbose and sample_result["details"]:
                print(f"\n--- Detailed Comparison for {table} ---")
                for record in sample_result["details"]:
                    print(f"Record ID: {record['id']} - {record['status']}")
                    
                    if record["fields"]:
                        field_data = [
                            [f["column"], f["sqlite_value"], f["postgres_value"], f["status"]]
                            for f in record["fields"]
                        ]
                        print(tabulate(field_data, headers=["Field", "SQLite Value", "PostgreSQL Value", "Match"]))
                    print()
        
        print(tabulate(sample_data, headers=["Table", "Sampled Records", "Matches", "Mismatches", "Status"]))
        
        # Print summary
        total_tables = len(common_tables)
        matching_tables = sum(1 for r in count_results if r["status"] == "✅")
        
        print("\n=== Migration Verification Summary ===")
        print(f"Tables with matching record counts: {matching_tables}/{total_tables}")
        print(f"Sample record comparison: {all_matches} matches, {all_mismatches} mismatches")
        
        if matching_tables == total_tables and all_mismatches == 0:
            print("\n✅ Migration verification PASSED. All checks successful.")
            return 0
        else:
            print("\n❌ Migration verification FAILED. Discrepancies detected.")
            return 1
    
    finally:
        # Close connections
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    sys.exit(main()) 