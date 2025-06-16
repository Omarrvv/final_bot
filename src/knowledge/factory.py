"""
Factory module for knowledge layer components.
This module provides factory functions for creating knowledge layer components.
"""

from typing import Optional

class KnowledgeFactory:
    """Factory for creating knowledge layer components."""
    
    @staticmethod
    def create_database_service(database_uri: str = None):
        """Create a database service."""
        from src.knowledge.database_service import DatabaseService
        return DatabaseService(database_uri)
    
    @staticmethod
    def create_knowledge_base_service(db_manager, vector_db_uri: Optional[str] = None, 
                                    content_path: Optional[str] = None):
        """Create a knowledge base service."""
        from src.knowledge.knowledge_base_service import KnowledgeBaseService
        return KnowledgeBaseService(db_manager, vector_db_uri, content_path)
    
    @staticmethod
    def create_database_manager(database_uri: str = None):
        """Create a database manager."""
        from src.knowledge.database import DatabaseManager
        return DatabaseManager(database_uri)
    
    @staticmethod
    def create_knowledge_base(db_manager, vector_db_uri: Optional[str] = None, 
                            content_path: Optional[str] = None):
        """Create a knowledge base."""
        from src.knowledge.knowledge_base import KnowledgeBase
        return KnowledgeBase(db_manager, vector_db_uri, content_path)

# Convenience functions for backward compatibility
def create_database_service(database_uri: str = None):
    """Create a database service."""
    return KnowledgeFactory.create_database_service(database_uri)

def create_knowledge_base_service(db_manager, vector_db_uri: Optional[str] = None, 
                                content_path: Optional[str] = None):
    """Create a knowledge base service."""
    return KnowledgeFactory.create_knowledge_base_service(db_manager, vector_db_uri, content_path)

def create_database_manager(database_uri: str = None):
    """Create a database manager."""
    return KnowledgeFactory.create_database_manager(database_uri)

def create_knowledge_base(db_manager, vector_db_uri: Optional[str] = None, 
                        content_path: Optional[str] = None):
    """Create a knowledge base."""
    return KnowledgeFactory.create_knowledge_base(db_manager, vector_db_uri, content_path) 