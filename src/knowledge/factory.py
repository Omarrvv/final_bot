"""
Knowledge Base Factory for Phase 3 Facade Implementation.

This factory provides seamless switching between legacy implementations
and new facade implementations based on feature flags. It enables
gradual migration and easy rollback capabilities.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Union

# Import the service classes instead of facades
from .database_service import DatabaseManagerService
from .knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

class DatabaseManagerFactory:
    """
    Factory for creating DatabaseManager instances.
    
    PERFORMANCE OPTIMIZED: Now returns shared DatabaseManager instances
    to prevent connection pool proliferation.
    """
    
    @staticmethod
    def create(database_uri: str = None, vector_dimension: int = 768) -> DatabaseManagerService:
        """
        Get or create a DatabaseManagerService instance (PHASE 2B OPTIMIZATION).
        
        Args:
            database_uri: Database connection URI
            vector_dimension: Vector embedding dimension
            
        Returns:
            DatabaseManagerService instance (connection pool optimized)
        """
        try:
            logger.info("🔄 Creating DatabaseManagerService (Phase 2B - checking for shared pool reuse)")
            
            # Check if we're in an app context with shared database manager
            try:
                # Try to get shared database manager from app context
                from src.utils.factory import component_factory
                if hasattr(component_factory, '_shared_db_manager') and component_factory._shared_db_manager:
                    logger.info("✅ Using shared database connection pool (Phase 2B optimization)")
                    # Return the shared instance if available
                    return component_factory._shared_db_manager
            except (ImportError, AttributeError):
                logger.debug("No shared database manager available in current context")
            
            # Create new instance if no shared manager is available
            logger.info("📊 Creating new DatabaseManagerService (new connection pool)")
            return DatabaseManagerService(database_uri, vector_dimension)
                
        except Exception as e:
            logger.error(f"Error creating DatabaseManagerService: {str(e)}")
            raise
    
    @staticmethod
    def get_implementation_type() -> str:
        """Get the current implementation type being used."""
        return "service"
    
    @staticmethod
    def is_facade_enabled() -> bool:
        """Check if facade architecture is enabled."""
        return True  # Service layer is the main implementation

class KnowledgeBaseFactory:
    """
    Factory for creating KnowledgeBase instances.
    
    This factory creates KnowledgeBaseService instances which provide
    the full implementation with service layer architecture.
    """
    
    @staticmethod
    def create(db_manager: Any, vector_db_uri: Optional[str] = None, 
              content_path: Optional[str] = None) -> KnowledgeBaseService:
        """
        Create a KnowledgeBaseService instance.
        
        Args:
            db_manager: DatabaseManagerService instance
            vector_db_uri: Vector database URI
            content_path: Content path for additional data
            
        Returns:
            KnowledgeBaseService instance
        """
        try:
            logger.info("Creating KnowledgeBaseService")
            return KnowledgeBaseService(db_manager, vector_db_uri, content_path)
                
        except Exception as e:
            logger.error(f"Error creating KnowledgeBaseService: {str(e)}")
            raise
    
    @staticmethod
    def get_implementation_type() -> str:
        """Get the current implementation type being used."""
        return "service"
    
    @staticmethod
    def is_facade_enabled() -> bool:
        """Check if service architecture is enabled."""
        return True  # Service layer is the main implementation

class ComponentFactory:
    """
    Unified factory for creating all knowledge base components.
    
    This factory creates a complete knowledge base stack with proper
    dependency injection and service layer architecture.
    """
    
    @staticmethod
    def create_knowledge_base_stack(database_uri: str = None, 
                                   vector_db_uri: Optional[str] = None,
                                   content_path: Optional[str] = None,
                                   vector_dimension: int = 768) -> Dict[str, Any]:
        """
        Create a complete knowledge base stack.
        
        Returns:
            Dictionary containing all components:
            - 'db_manager': DatabaseManager instance
            - 'knowledge_base': KnowledgeBase instance
            - 'implementation_info': Information about implementations used
        """
        logger.info("Creating knowledge base stack with service layer architecture")
        
        # Create database manager service
        db_manager = DatabaseManagerFactory.create(database_uri, vector_dimension)
        
        # Create knowledge base service
        knowledge_base = KnowledgeBaseFactory.create(db_manager, vector_db_uri, content_path)
        
        # Gather implementation information
        implementation_info = {
            'database_manager': {
                'type': DatabaseManagerFactory.get_implementation_type(),
                'service_enabled': DatabaseManagerFactory.is_facade_enabled(),
                'class_name': type(db_manager).__name__
            },
            'knowledge_base': {
                'type': KnowledgeBaseFactory.get_implementation_type(),
                'service_enabled': KnowledgeBaseFactory.is_facade_enabled(),
                'class_name': type(knowledge_base).__name__
            },
            'feature_flags': ComponentFactory.get_all_feature_flags(),
            'phase': ComponentFactory.get_current_phase()
        }
        
        logger.info(f"Knowledge base stack created: "
                   f"DB={implementation_info['database_manager']['type']}, "
                   f"KB={implementation_info['knowledge_base']['type']}")
        
        return {
            'db_manager': db_manager,
            'knowledge_base': knowledge_base,
            'implementation_info': implementation_info
        }
    
    @staticmethod
    def get_all_feature_flags() -> Dict[str, bool]:
        """Get all feature flags related to the knowledge base architecture."""
        flags = {
            # Service Layer Flags (renamed from facade flags)
            'USE_DATABASE_SERVICE': os.getenv('USE_DATABASE_SERVICE', 'true').lower() == 'true',
            'USE_KNOWLEDGE_BASE_SERVICE': os.getenv('USE_KNOWLEDGE_BASE_SERVICE', 'true').lower() == 'true',
            'USE_SERVICE_ARCHITECTURE': os.getenv('USE_SERVICE_ARCHITECTURE', 'true').lower() == 'true',
            'ENABLE_SERVICE_LOGGING': os.getenv('ENABLE_SERVICE_LOGGING', 'true').lower() == 'true',
            'ENABLE_LEGACY_FALLBACK': os.getenv('ENABLE_LEGACY_FALLBACK', 'true').lower() == 'true',
            
            # Repository Architecture Flags
            'USE_NEW_REPOSITORIES': os.getenv('USE_NEW_REPOSITORIES', 'true').lower() == 'true',
            'USE_REPOSITORY_FACTORY': os.getenv('USE_REPOSITORY_FACTORY', 'true').lower() == 'true',
            
            # Service Layer Components
            'USE_NEW_EXTENSION_MANAGER': os.getenv('USE_NEW_EXTENSION_MANAGER', 'true').lower() == 'true',
            'USE_NEW_SCHEMA_MANAGER': os.getenv('USE_NEW_SCHEMA_MANAGER', 'true').lower() == 'true',
            'USE_NEW_CACHE_MANAGER': os.getenv('USE_NEW_CACHE_MANAGER', 'true').lower() == 'true',
            'USE_NEW_ANALYTICS_SERVICE': os.getenv('USE_NEW_ANALYTICS_SERVICE', 'true').lower() == 'true',
            'USE_NEW_BATCH_SERVICE': os.getenv('USE_NEW_BATCH_SERVICE', 'true').lower() == 'true',
            'USE_NEW_EMBEDDING_SERVICE': os.getenv('USE_NEW_EMBEDDING_SERVICE', 'true').lower() == 'true',
            'USE_UNIFIED_SEARCH_SERVICE': os.getenv('USE_UNIFIED_SEARCH_SERVICE', 'true').lower() == 'true',
            
            # Clean Architecture Flags
            'USE_CLEAN_DATABASE_MANAGER': os.getenv('USE_CLEAN_DATABASE_MANAGER', 'true').lower() == 'true',
            'USE_CLEAN_KNOWLEDGE_BASE': os.getenv('USE_CLEAN_KNOWLEDGE_BASE', 'true').lower() == 'true',
            'ENABLE_CLEANUP_LOGGING': os.getenv('ENABLE_CLEANUP_LOGGING', 'true').lower() == 'true'
        }
        
        return flags
    
    @staticmethod
    def get_current_phase() -> str:
        """Determine the current refactoring phase."""
        return "Phase 5 (Clean Architecture - Service Layer Default)"
    
    @staticmethod
    def get_migration_status() -> Dict[str, Any]:
        """Get detailed migration status and recommendations."""
        flags = ComponentFactory.get_all_feature_flags()
        current_phase = ComponentFactory.get_current_phase()
        
        # Count enabled flags by category
        service_flags = ['USE_DATABASE_SERVICE', 'USE_KNOWLEDGE_BASE_SERVICE']
        component_flags = [
            'USE_NEW_EXTENSION_MANAGER', 'USE_NEW_SCHEMA_MANAGER', 
            'USE_NEW_CACHE_MANAGER', 'USE_NEW_ANALYTICS_SERVICE',
            'USE_NEW_BATCH_SERVICE', 'USE_NEW_EMBEDDING_SERVICE'
        ]
        repo_flags = ['USE_NEW_REPOSITORIES', 'USE_REPOSITORY_FACTORY']
        
        service_enabled = sum(1 for flag in service_flags if flags[flag])
        component_enabled = sum(1 for flag in component_flags if flags[flag])
        repo_enabled = sum(1 for flag in repo_flags if flags[flag])
        
        # Calculate overall migration progress
        total_flags = len(service_flags) + len(component_flags) + len(repo_flags)
        enabled_flags = service_enabled + component_enabled + repo_enabled
        overall_progress = (enabled_flags / total_flags) * 100
        
        # Determine if ready for production
        ready_for_production = (
            service_enabled >= 2 and  # Both services enabled
            component_enabled >= 4 and  # Most components enabled
            repo_enabled >= 1  # Repository layer enabled
        )
        
        status = {
            'current_phase': current_phase,
            'overall_progress': overall_progress,
            'ready_for_production': ready_for_production,
            'enabled_flags': {
                'service_layer': service_enabled,
                'components': component_enabled,
                'repositories': repo_enabled,
                'total': enabled_flags
            },
            'total_flags': total_flags,
            'recommendations': ComponentFactory._get_migration_recommendations(flags),
            'feature_breakdown': flags
        }
        
        return status
    
    @staticmethod
    def _get_migration_recommendations(flags: Dict[str, bool]) -> List[str]:
        """Generate migration recommendations based on current flag status."""
        recommendations = []
        
        # Check service layer
        if not flags.get('USE_DATABASE_SERVICE', False):
            recommendations.append("Enable USE_DATABASE_SERVICE for modern database management")
        if not flags.get('USE_KNOWLEDGE_BASE_SERVICE', False):
            recommendations.append("Enable USE_KNOWLEDGE_BASE_SERVICE for improved knowledge base architecture")
        
        # Check repository layer
        if not flags.get('USE_NEW_REPOSITORIES', False):
            recommendations.append("Enable USE_NEW_REPOSITORIES for better data access patterns")
        if not flags.get('USE_REPOSITORY_FACTORY', False):
            recommendations.append("Enable USE_REPOSITORY_FACTORY for dependency injection")
        
        # Check advanced services
        if not flags.get('USE_NEW_CACHE_MANAGER', False):
            recommendations.append("Enable USE_NEW_CACHE_MANAGER for better performance")
        if not flags.get('USE_NEW_ANALYTICS_SERVICE', False):
            recommendations.append("Enable USE_NEW_ANALYTICS_SERVICE for monitoring")
        if not flags.get('USE_UNIFIED_SEARCH_SERVICE', False):
            recommendations.append("Enable USE_UNIFIED_SEARCH_SERVICE for consolidated search")
        
        if not recommendations:
            recommendations.append("System is fully migrated to service layer architecture")
        
        return recommendations 