#!/usr/bin/env python3
"""
Database Utilities

Provides utilities for database schema management, type mapping, and validation
between SQLite and PostgreSQL databases.
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Type mapping from SQLite to PostgreSQL
SQLITE_TO_PG_TYPE_MAP = {
    'INTEGER': 'integer',
    'REAL': 'double precision',
    'TEXT': 'text',
    'BLOB': 'bytea',
    'BOOLEAN': 'boolean',
    'DATETIME': 'timestamp with time zone',
    'VARCHAR': 'varchar',
    'JSON': 'jsonb',
    'JSONB': 'jsonb'
}

# PostgreSQL types that need special handling during migration
SPECIAL_TYPES = {
    'jsonb': lambda v: json.loads(v) if isinstance(v, str) else v,
    'boolean': lambda v: bool(v) if v is not None else None,
    'timestamp with time zone': lambda v: datetime.fromisoformat(v.replace('Z', '+00:00')) if isinstance(v, str) else v,
}

def get_sqlite_column_types(cursor, table: str) -> Dict[str, Dict[str, Any]]:
    """Get detailed column information from SQLite table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = {}
    for col in cursor.fetchall():
        name, type_name, notnull, dflt_value, pk = col[1:6]
        columns[name] = {
            'type': type_name.upper(),
            'nullable': not notnull,
            'default': dflt_value,
            'primary_key': bool(pk)
        }
    return columns

def get_postgres_column_types(cursor, table: str) -> Dict[str, Dict[str, Any]]:
    """Get detailed column information from PostgreSQL table"""
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            pg_get_serial_sequence(quote_ident(%s), column_name) IS NOT NULL as is_serial
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table, table))
    
    columns = {}
    for col in cursor.fetchall():
        name, type_name, nullable, default, is_serial = col
        columns[name] = {
            'type': type_name,
            'nullable': nullable == 'YES',
            'default': default,
            'is_serial': is_serial
        }
    return columns

def map_sqlite_to_pg_type(sqlite_type: str) -> str:
    """Map SQLite type to PostgreSQL type"""
    base_type = sqlite_type.split('(')[0].upper()
    return SQLITE_TO_PG_TYPE_MAP.get(base_type, 'text')

def get_schema_differences(
    sqlite_schema: Dict[str, Dict[str, Any]],
    postgres_schema: Dict[str, Dict[str, Any]]
) -> Dict[str, List[str]]:
    """
    Compare SQLite and PostgreSQL schemas and return differences
    """
    differences = {
        'missing_columns': [],
        'type_mismatches': [],
        'constraint_differences': []
    }
    
    for col_name, sqlite_info in sqlite_schema.items():
        if col_name not in postgres_schema:
            differences['missing_columns'].append(col_name)
            continue
            
        pg_info = postgres_schema[col_name]
        expected_pg_type = map_sqlite_to_pg_type(sqlite_info['type'])
        
        if expected_pg_type != pg_info['type']:
            differences['type_mismatches'].append(
                f"{col_name}: SQLite({sqlite_info['type']}) -> PG({pg_info['type']})"
            )
            
        if sqlite_info['nullable'] != pg_info['nullable']:
            differences['constraint_differences'].append(
                f"{col_name}: nullable mismatch"
            )
            
    return differences

def create_migration_ddl(
    table: str,
    sqlite_schema: Dict[str, Dict[str, Any]]
) -> List[str]:
    """
    Generate PostgreSQL DDL statements for table migration
    """
    ddl = []
    columns = []
    
    for col_name, info in sqlite_schema.items():
        pg_type = map_sqlite_to_pg_type(info['type'])
        nullable = "" if info['nullable'] else "NOT NULL"
        default = f"DEFAULT {info['default']}" if info['default'] else ""
        
        if info.get('primary_key'):
            if pg_type == 'integer':
                columns.append(f"{col_name} SERIAL PRIMARY KEY")
            else:
                columns.append(f"{col_name} {pg_type} PRIMARY KEY {default}")
        else:
            columns.append(f"{col_name} {pg_type} {nullable} {default}".strip())
    
    create_table = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        {','.join(columns)}
    );
    """
    ddl.append(create_table)
    
    # Add indexes for foreign keys and common query patterns
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    for fk in cursor.fetchall():
        from_col = fk['from']
        ddl.append(f"CREATE INDEX IF NOT EXISTS idx_{table}_{from_col} ON {table}({from_col});")
    
    return ddl

def convert_value(value: Any, target_type: str) -> Any:
    """Convert a value to the appropriate PostgreSQL type"""
    if value is None:
        return None
        
    converter = SPECIAL_TYPES.get(target_type)
    if converter:
        try:
            return converter(value)
        except Exception as e:
            logger.warning(f"Failed to convert value {value} to {target_type}: {e}")
            return value
            
    return value