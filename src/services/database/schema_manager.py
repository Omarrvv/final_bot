"""
Schema Management Service for the Egypt Tourism Chatbot.

This service handles database schema operations including table creation,
column management, and index operations. Extracted from DatabaseManager
and database_init.py as part of Phase 2.5 refactoring.
"""
import logging
import os
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Import table definitions from database_init
from src.knowledge.database_init import TABLE_DEFINITIONS, topological_sort

logger = logging.getLogger(__name__)

class SchemaStatus(Enum):
    """Schema object status enumeration."""
    EXISTS = "exists"
    MISSING = "missing"
    ERROR = "error"
    INVALID = "invalid"

@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    status: SchemaStatus
    columns: List[str]
    indexes: List[str]
    constraints: List[str]
    row_count: Optional[int] = None
    error_message: Optional[str] = None

@dataclass
class ColumnInfo:
    """Information about a table column."""
    name: str
    table: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    character_maximum_length: Optional[int] = None

class SchemaManagementService:
    """
    Service for managing database schema operations.
    
    This service provides centralized management of database schema
    including tables, columns, indexes, and constraints.
    
    Responsibilities:
    - Table existence checking and creation
    - Column management and validation
    - Index creation and management
    - Schema validation and reporting
    - Foreign key constraint management
    """
    
    def __init__(self, db_manager=None, extension_manager=None):
        """
        Initialize the schema management service.
        
        Args:
            db_manager: Database manager instance for executing queries
            extension_manager: Extension manager for checking capabilities
        """
        self.db_manager = db_manager
        self.extension_manager = extension_manager
        self._schema_cache = {}
        self._cache_ttl = 600  # 10 minutes
        self._last_cache_update = 0
        
        # Feature flags from environment
        self.enabled = os.getenv('USE_NEW_SCHEMA_MANAGER', 'false').lower() == 'true'
        
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager._table_exists(table_name)
                
            if not self.db_manager:
                logger.error("No database manager available")
                return False
                
            query = """
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = %s AND table_schema = 'public'
                ) AS exists
            """
            result = self.db_manager.execute_postgres_query(query, (table_name,))
            
            if result and len(result) > 0:
                return result[0].get('exists', False)
            return False
            
        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {str(e)}")
            return False
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a table.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to check
            
        Returns:
            bool: True if column exists, False otherwise
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager._postgres_column_exists(table_name, column_name)
                
            if not self.db_manager:
                logger.error("No database manager available")
                return False
                
            query = """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s AND table_schema = 'public'
                ) AS exists
            """
            result = self.db_manager.execute_postgres_query(query, (table_name, column_name))
            
            if result and len(result) > 0:
                return result[0].get('exists', False)
            return False
            
        except Exception as e:
            logger.error(f"Error checking if column {column_name} exists in {table_name}: {str(e)}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Get list of columns for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[str]: List of column names
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager._get_table_columns(table_name)
                
            if not self.db_manager:
                logger.error("No database manager available")
                return []
                
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            result = self.db_manager.execute_postgres_query(query, (table_name,))
            
            if result:
                return [row['column_name'] for row in result]
            return []
            
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {str(e)}")
            return []
    
    def get_column_info(self, table_name: str, column_name: str) -> Optional[ColumnInfo]:
        """
        Get detailed information about a column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            Optional[ColumnInfo]: Column information or None if not found
        """
        try:
            if not self.db_manager:
                logger.error("No database manager available")
                return None
                
            query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s AND table_schema = 'public'
            """
            result = self.db_manager.execute_postgres_query(query, (table_name, column_name))
            
            if result and len(result) > 0:
                row = result[0]
                return ColumnInfo(
                    name=row['column_name'],
                    table=table_name,
                    data_type=row['data_type'],
                    is_nullable=row['is_nullable'] == 'YES',
                    default_value=row.get('column_default'),
                    character_maximum_length=row.get('character_maximum_length')
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting column info for {table_name}.{column_name}: {str(e)}")
            return None
    
    def create_table(self, table_name: str, table_definition: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a table using the provided definition or from TABLE_DEFINITIONS.
        
        Args:
            table_name: Name of the table to create
            table_definition: Optional custom table definition
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db_manager:
                logger.error("No database manager available")
                return False
            
            # Check if table already exists
            if self.table_exists(table_name):
                logger.info(f"Table {table_name} already exists")
                return True
            
            # Get table definition
            if table_definition:
                definition = table_definition
            elif table_name in TABLE_DEFINITIONS:
                definition = TABLE_DEFINITIONS[table_name]
            else:
                logger.error(f"No table definition found for {table_name}")
                return False
            
            # Execute table creation SQL
            conn = self.db_manager._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
                
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(definition["sql"])
                        
                logger.info(f"Successfully created table: {table_name}")
                return True
                
            finally:
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {str(e)}")
            return False
    
    def create_indexes(self, table_name: str, indexes: Optional[List[Tuple]] = None) -> bool:
        """
        Create indexes for a table.
        
        Args:
            table_name: Name of the table
            indexes: Optional list of index definitions, defaults to TABLE_DEFINITIONS
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db_manager:
                logger.error("No database manager available")
                return False
            
            # Get index definitions
            if indexes:
                index_definitions = indexes
            elif table_name in TABLE_DEFINITIONS:
                index_definitions = TABLE_DEFINITIONS[table_name].get("indexes", [])
            else:
                logger.warning(f"No index definitions found for {table_name}")
                return True  # Not an error if no indexes defined
            
            conn = self.db_manager._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
                
            try:
                with conn:
                    with conn.cursor() as cursor:
                        for index_def in index_definitions:
                            try:
                                if len(index_def) == 2:
                                    # Regular index: (name, columns)
                                    index_name, index_columns = index_def
                                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({index_columns})"
                                elif len(index_def) == 3:
                                    # Special index with method: (name, columns, method)
                                    index_name, index_columns, index_method = index_def
                                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING {index_method} ({index_columns})"
                                else:
                                    logger.warning(f"Invalid index definition: {index_def}")
                                    continue
                                
                                cursor.execute(sql)
                                logger.info(f"Created index: {index_def[0]}")
                                
                            except Exception as e:
                                logger.warning(f"Error creating index {index_def[0]}: {str(e)}")
                                # Continue with other indexes
                
                return True
                
            finally:
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error creating indexes for {table_name}: {str(e)}")
            return False
    
    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """
        Get comprehensive information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Optional[TableInfo]: Table information or None if not found
        """
        try:
            if not self.table_exists(table_name):
                return TableInfo(
                    name=table_name,
                    status=SchemaStatus.MISSING,
                    columns=[],
                    indexes=[],
                    constraints=[],
                    error_message="Table does not exist"
                )
            
            # Get columns
            columns = self.get_table_columns(table_name)
            
            # Get indexes
            indexes = self._get_table_indexes(table_name)
            
            # Get constraints
            constraints = self._get_table_constraints(table_name)
            
            # Get row count
            row_count = self._get_table_row_count(table_name)
            
            return TableInfo(
                name=table_name,
                status=SchemaStatus.EXISTS,
                columns=columns,
                indexes=indexes,
                constraints=constraints,
                row_count=row_count
            )
            
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {str(e)}")
            return TableInfo(
                name=table_name,
                status=SchemaStatus.ERROR,
                columns=[],
                indexes=[],
                constraints=[],
                error_message=str(e)
            )
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the entire database schema against TABLE_DEFINITIONS.
        
        Returns:
            Dict[str, Any]: Comprehensive schema validation report
        """
        validation_report = {
            'timestamp': time.time(),
            'overall_status': 'valid',
            'tables': {},
            'summary': {
                'total_tables': len(TABLE_DEFINITIONS),
                'existing_tables': 0,
                'missing_tables': 0,
                'invalid_tables': 0
            },
            'recommendations': []
        }
        
        # Check each table in TABLE_DEFINITIONS
        for table_name in TABLE_DEFINITIONS.keys():
            table_info = self.get_table_info(table_name)
            
            if table_info:
                validation_report['tables'][table_name] = {
                    'status': table_info.status.value,
                    'columns': table_info.columns,
                    'indexes': table_info.indexes,
                    'constraints': table_info.constraints,
                    'row_count': table_info.row_count,
                    'error_message': table_info.error_message
                }
                
                # Update summary
                if table_info.status == SchemaStatus.EXISTS:
                    validation_report['summary']['existing_tables'] += 1
                elif table_info.status == SchemaStatus.MISSING:
                    validation_report['summary']['missing_tables'] += 1
                    validation_report['recommendations'].append(f"Create missing table: {table_name}")
                else:
                    validation_report['summary']['invalid_tables'] += 1
                    validation_report['overall_status'] = 'invalid'
        
        # Check for extension-dependent features
        if self.extension_manager:
            features = self.extension_manager.get_feature_availability()
            validation_report['features'] = features
            
            # Add recommendations based on available extensions
            validation_report['recommendations'].extend(
                self.extension_manager.get_recommendations()
            )
        
        return validation_report
    
    def create_all_tables(self, vector_dimension: int = 1536) -> bool:
        """
        Create all tables defined in TABLE_DEFINITIONS in proper order.
        
        Args:
            vector_dimension: Dimension for vector columns
            
        Returns:
            bool: True if all tables created successfully, False otherwise
        """
        try:
            if not self.db_manager:
                logger.error("No database manager available")
                return False
            
            # Get tables in topological order (respecting dependencies)
            ordered_tables = topological_sort(TABLE_DEFINITIONS)
            logger.info(f"Creating tables in order: {ordered_tables}")
            
            success = True
            
            # Create each table
            for table_name in ordered_tables:
                if not self.create_table(table_name):
                    logger.error(f"Failed to create table: {table_name}")
                    success = False
                    continue
                
                # Create indexes for the table
                if not self.create_indexes(table_name):
                    logger.warning(f"Failed to create some indexes for: {table_name}")
                    # Don't fail completely for index issues
            
            # Add extension-dependent columns if extensions are available
            if self.extension_manager:
                self._add_extension_columns(vector_dimension)
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating all tables: {str(e)}")
            return False
    
    def _get_table_indexes(self, table_name: str) -> List[str]:
        """Get list of indexes for a table."""
        try:
            query = """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = %s AND schemaname = 'public'
            """
            result = self.db_manager.execute_postgres_query(query, (table_name,))
            
            if result:
                return [row['indexname'] for row in result]
            return []
            
        except Exception as e:
            logger.error(f"Error getting indexes for {table_name}: {str(e)}")
            return []
    
    def _get_table_constraints(self, table_name: str) -> List[str]:
        """Get list of constraints for a table."""
        try:
            query = """
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = %s AND table_schema = 'public'
            """
            result = self.db_manager.execute_postgres_query(query, (table_name,))
            
            if result:
                return [f"{row['constraint_name']} ({row['constraint_type']})" for row in result]
            return []
            
        except Exception as e:
            logger.error(f"Error getting constraints for {table_name}: {str(e)}")
            return []
    
    def _get_table_row_count(self, table_name: str) -> Optional[int]:
        """Get approximate row count for a table."""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.db_manager.execute_postgres_query(query)
            
            if result and len(result) > 0:
                return result[0].get('count', 0)
            return None
            
        except Exception as e:
            logger.warning(f"Error getting row count for {table_name}: {str(e)}")
            return None
    
    def _add_extension_columns(self, vector_dimension: int = 1536) -> None:
        """Add extension-dependent columns like geometry and vector columns."""
        try:
            # Add PostGIS geometry columns
            if self.extension_manager.check_postgis_available():
                self._add_geometry_columns()
            
            # Add pgvector embedding columns
            if self.extension_manager.check_pgvector_available():
                self._add_vector_columns(vector_dimension)
                
        except Exception as e:
            logger.error(f"Error adding extension columns: {str(e)}")
    
    def _add_geometry_columns(self) -> None:
        """Add PostGIS geometry columns to relevant tables."""
        tables_with_geo = ["attractions", "restaurants", "accommodations", "cities", "regions"]
        
        conn = self.db_manager._get_pg_connection()
        if not conn:
            return
            
        try:
            with conn:
                with conn.cursor() as cursor:
                    for table in tables_with_geo:
                        if self.table_exists(table):
                            try:
                                # Add geometry column
                                cursor.execute(f"""
                                    ALTER TABLE {table} ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
                                """)
                                
                                # Create spatial index
                                cursor.execute(f"""
                                    CREATE INDEX IF NOT EXISTS idx_{table}_geom ON {table} USING GIST (geom);
                                """)
                                
                                logger.info(f"Added geometry column and index to {table}")
                                
                            except Exception as e:
                                logger.warning(f"Error adding geometry to {table}: {str(e)}")
        finally:
            self.db_manager._return_pg_connection(conn)
    
    def _add_vector_columns(self, dimension: int = 1536) -> None:
        """Add pgvector embedding columns to relevant tables."""
        tables_with_vector = ["attractions", "restaurants", "accommodations", "cities"]
        
        conn = self.db_manager._get_pg_connection()
        if not conn:
            return
            
        try:
            with conn:
                with conn.cursor() as cursor:
                    for table in tables_with_vector:
                        if self.table_exists(table):
                            try:
                                # Add vector column
                                cursor.execute(f"""
                                    ALTER TABLE {table} ADD COLUMN IF NOT EXISTS embedding vector({dimension});
                                """)
                                
                                # Create vector index
                                cursor.execute(f"""
                                    CREATE INDEX IF NOT EXISTS idx_{table}_embedding
                                    ON {table} USING ivfflat (embedding vector_cosine_ops);
                                """)
                                
                                logger.info(f"Added vector column and index to {table}")
                                
                            except Exception as e:
                                logger.warning(f"Error adding vector column to {table}: {str(e)}")
        finally:
            self.db_manager._return_pg_connection(conn) 