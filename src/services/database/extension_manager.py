"""
Extension Management Service for the Egypt Tourism Chatbot.

This service handles PostgreSQL extension management including PostGIS and pgvector.
Extracted from DatabaseManager god object as part of Phase 2.5 refactoring.
"""
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ExtensionStatus(Enum):
    """Extension status enumeration."""
    AVAILABLE = "available"
    MISSING = "missing"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ExtensionInfo:
    """Information about a database extension."""
    name: str
    status: ExtensionStatus
    version: Optional[str] = None
    requires_superuser: bool = False
    error_message: Optional[str] = None

class ExtensionManagementService:
    """
    Service for managing PostgreSQL extensions.
    
    This service provides centralized management of database extensions
    including PostGIS for geospatial features and pgvector for vector operations.
    
    Responsibilities:
    - Extension availability checking
    - Extension installation validation
    - Version compatibility checking
    - Feature detection based on extensions
    """
    
    # Known extensions and their requirements
    KNOWN_EXTENSIONS = {
        'postgis': {
            'requires_superuser': True,
            'description': 'PostGIS spatial and geographic objects',
            'minimum_version': '2.5'
        },
        'vector': {
            'requires_superuser': True,
            'description': 'pgvector for vector similarity search',
            'minimum_version': '0.4.0'
        },
        'pg_trgm': {
            'requires_superuser': False,
            'description': 'Trigram matching for text search',
            'minimum_version': '1.0'
        },
        'unaccent': {
            'requires_superuser': False,
            'description': 'Text search dictionary for unaccented matching',
            'minimum_version': '1.0'
        }
    }
    
    def __init__(self, db_manager=None):
        """
        Initialize the extension management service.
        
        Args:
            db_manager: Database manager instance for executing queries
        """
        self.db_manager = db_manager
        self._extension_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = 0
        
        # Feature flags from environment
        self.enabled = os.getenv('USE_NEW_EXTENSION_MANAGER', 'false').lower() == 'true'
        
    def check_postgis_available(self) -> bool:
        """
        Check if PostGIS extension is available and enabled.
        
        Returns:
            bool: True if PostGIS is available, False otherwise
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager._check_postgis_enabled()
                
            extension_info = self.get_extension_info('postgis')
            return extension_info.status == ExtensionStatus.AVAILABLE
            
        except Exception as e:
            logger.error(f"Error checking PostGIS availability: {str(e)}")
            return False
    
    def check_pgvector_available(self) -> bool:
        """
        Check if pgvector extension is available and enabled.
        
        Returns:
            bool: True if pgvector is available, False otherwise
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager._check_vector_enabled()
                
            extension_info = self.get_extension_info('vector')
            return extension_info.status == ExtensionStatus.AVAILABLE
            
        except Exception as e:
            logger.error(f"Error checking pgvector availability: {str(e)}")
            return False
    
    def get_extension_info(self, extension_name: str) -> ExtensionInfo:
        """
        Get detailed information about a specific extension.
        
        Args:
            extension_name: Name of the extension to check
            
        Returns:
            ExtensionInfo: Detailed extension information
        """
        if not self.db_manager:
            return ExtensionInfo(
                name=extension_name,
                status=ExtensionStatus.ERROR,
                error_message="No database manager available"
            )
        
        try:
            # Check if extension is installed and enabled
            query = """
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = %s
            """
            result = self.db_manager.execute_postgres_query(query, (extension_name,))
            
            if result and len(result) > 0:
                version = result[0].get('extversion')
                return ExtensionInfo(
                    name=extension_name,
                    status=ExtensionStatus.AVAILABLE,
                    version=version,
                    requires_superuser=self.KNOWN_EXTENSIONS.get(extension_name, {}).get('requires_superuser', True)
                )
            else:
                # Extension not installed, check if it's available to install
                available_query = """
                    SELECT name, default_version 
                    FROM pg_available_extensions 
                    WHERE name = %s
                """
                available_result = self.db_manager.execute_postgres_query(available_query, (extension_name,))
                
                if available_result and len(available_result) > 0:
                    return ExtensionInfo(
                        name=extension_name,
                        status=ExtensionStatus.MISSING,
                        version=available_result[0].get('default_version'),
                        requires_superuser=self.KNOWN_EXTENSIONS.get(extension_name, {}).get('requires_superuser', True),
                        error_message="Extension available but not installed"
                    )
                else:
                    return ExtensionInfo(
                        name=extension_name,
                        status=ExtensionStatus.MISSING,
                        requires_superuser=self.KNOWN_EXTENSIONS.get(extension_name, {}).get('requires_superuser', True),
                        error_message="Extension not available in this PostgreSQL installation"
                    )
                    
        except Exception as e:
            logger.error(f"Error getting extension info for {extension_name}: {str(e)}")
            return ExtensionInfo(
                name=extension_name,
                status=ExtensionStatus.ERROR,
                error_message=str(e)
            )
    
    def validate_extension_compatibility(self) -> Dict[str, bool]:
        """
        Validate compatibility of all known extensions.
        
        Returns:
            Dict[str, bool]: Extension name to compatibility status mapping
        """
        compatibility = {}
        
        for ext_name in self.KNOWN_EXTENSIONS.keys():
            try:
                info = self.get_extension_info(ext_name)
                compatibility[ext_name] = info.status == ExtensionStatus.AVAILABLE
                
            except Exception as e:
                logger.error(f"Error validating {ext_name}: {str(e)}")
                compatibility[ext_name] = False
                
        return compatibility
    
    def enable_extension(self, extension_name: str, require_superuser: bool = True) -> bool:
        """
        Enable a PostgreSQL extension.
        
        Args:
            extension_name: Name of the extension to enable
            require_superuser: Whether to require superuser privileges
            
        Returns:
            bool: True if successfully enabled, False otherwise
        """
        if not self.db_manager:
            logger.error("No database manager available")
            return False
            
        try:
            # Check if extension is already enabled
            if self.get_extension_info(extension_name).status == ExtensionStatus.AVAILABLE:
                logger.info(f"Extension {extension_name} is already enabled")
                return True
            
            # Check if we have superuser privileges if required
            if require_superuser:
                superuser_query = "SELECT current_setting('is_superuser') as is_superuser"
                result = self.db_manager.execute_postgres_query(superuser_query)
                
                if not result or result[0].get('is_superuser') != 'on':
                    logger.warning(f"Superuser privileges required to enable {extension_name}")
                    return False
            
            # Try to enable the extension
            conn = self.db_manager._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
                
            try:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {extension_name}")
                    
                logger.info(f"Successfully enabled extension: {extension_name}")
                
                # Clear cache to force refresh
                self._extension_cache.clear()
                return True
                
            finally:
                conn.autocommit = False
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error enabling extension {extension_name}: {str(e)}")
            return False
    
    def get_extension_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all known extensions.
        
        Returns:
            Dict[str, Any]: Comprehensive extension status report
        """
        status = {
            'timestamp': self._get_current_timestamp(),
            'database_connected': self.db_manager is not None,
            'extensions': {},
            'summary': {
                'total': len(self.KNOWN_EXTENSIONS),
                'available': 0,
                'missing': 0,
                'errors': 0
            }
        }
        
        for ext_name, ext_config in self.KNOWN_EXTENSIONS.items():
            info = self.get_extension_info(ext_name)
            
            status['extensions'][ext_name] = {
                'status': info.status.value,
                'version': info.version,
                'requires_superuser': info.requires_superuser,
                'description': ext_config.get('description', 'No description available'),
                'minimum_version': ext_config.get('minimum_version'),
                'error_message': info.error_message
            }
            
            # Update summary counts
            if info.status == ExtensionStatus.AVAILABLE:
                status['summary']['available'] += 1
            elif info.status == ExtensionStatus.MISSING:
                status['summary']['missing'] += 1
            else:
                status['summary']['errors'] += 1
        
        return status
    
    def get_feature_availability(self) -> Dict[str, bool]:
        """
        Get availability of features based on enabled extensions.
        
        Returns:
            Dict[str, bool]: Feature name to availability mapping
        """
        features = {
            'geospatial_search': self.check_postgis_available(),
            'vector_search': self.check_pgvector_available(),
            'fuzzy_text_search': self.get_extension_info('pg_trgm').status == ExtensionStatus.AVAILABLE,
            'accent_insensitive_search': self.get_extension_info('unaccent').status == ExtensionStatus.AVAILABLE
        }
        
        return features
    
    def get_recommendations(self) -> List[str]:
        """
        Get recommendations for extension configuration.
        
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        # Check PostGIS
        if not self.check_postgis_available():
            recommendations.append(
                "Install PostGIS extension for geospatial search features: "
                "CREATE EXTENSION IF NOT EXISTS postgis;"
            )
        
        # Check pgvector
        if not self.check_pgvector_available():
            recommendations.append(
                "Install pgvector extension for vector similarity search: "
                "CREATE EXTENSION IF NOT EXISTS vector;"
            )
        
        # Check text search extensions
        if self.get_extension_info('pg_trgm').status != ExtensionStatus.AVAILABLE:
            recommendations.append(
                "Install pg_trgm extension for fuzzy text search: "
                "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
            )
        
        if self.get_extension_info('unaccent').status != ExtensionStatus.AVAILABLE:
            recommendations.append(
                "Install unaccent extension for accent-insensitive search: "
                "CREATE EXTENSION IF NOT EXISTS unaccent;"
            )
        
        return recommendations
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time() 