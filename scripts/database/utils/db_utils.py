"""
Database Utilities

Common utilities for database operations, type handling, and schema management.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from psycopg2.extras import Json

def parse_timestamp(value: str, formats: Optional[List[str]] = None) -> Optional[datetime]:
    """Parse a timestamp string using multiple formats."""
    if not formats:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d'
        ]
    
    if not value or value.strip() == '':
        return None
        
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None

def parse_json(value: Union[str, dict, list]) -> Optional[Json]:
    """Parse a JSON value into PostgreSQL JSONB format."""
    if not value:
        return None
    try:
        if isinstance(value, str):
            return Json(json.loads(value))
        return Json(value)
    except:
        return None

def parse_numeric(value: Any) -> Optional[float]:
    """Parse a numeric value, handling various formats."""
    if not value:
        return None
    try:
        if isinstance(value, str):
            # Remove currency symbols and other non-numeric chars
            clean = ''.join(c for c in value if c.isdigit() or c in '.-')
            return float(clean)
        return float(value)
    except:
        return None

def get_table_columns(schema: Dict) -> List[str]:
    """Get list of columns from schema definition."""
    return list(schema.keys())

def get_common_columns(sqlite_schema: Dict, pg_schema: Dict) -> List[str]:
    """Get columns that exist in both schemas."""
    sqlite_cols = set(get_table_columns(sqlite_schema))
    pg_cols = set(get_table_columns(pg_schema))
    return list(sqlite_cols.intersection(pg_cols))

def generate_upsert_sql(table: str, columns: List[str]) -> str:
    """Generate SQL for INSERT ... ON CONFLICT UPDATE."""
    placeholders = ', '.join(['%s'] * len(columns))
    update_cols = [f"{col} = EXCLUDED.{col}" for col in columns if col != 'id']
    
    return f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE SET
        {', '.join(update_cols)}
    """

def generate_spatial_update_sql(table: str) -> str:
    """Generate SQL to update spatial geometry column."""
    return f"""
        UPDATE {table}
        SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE latitude IS NOT NULL 
          AND longitude IS NOT NULL
          AND geom IS NULL
    """

def check_postgis_extension(cursor) -> bool:
    """Check if PostGIS extension is available."""
    cursor.execute("""
        SELECT 1 FROM pg_extension WHERE extname = 'postgis'
    """)
    return cursor.fetchone() is not None

def check_pgvector_extension(cursor) -> bool:
    """Check if pgvector extension is available."""
    cursor.execute("""
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    """)
    return cursor.fetchone() is not None