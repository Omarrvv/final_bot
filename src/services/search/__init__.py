"""
Search Services Package for the Egypt Tourism Chatbot.

This package consolidates all search functionality into unified services,
replacing the scattered search operations across DatabaseManager and VectorSearchService.
"""

from .unified_search_service import (
    UnifiedSearchService,
    SearchFilter,
    SearchResult,
    SearchError
)

__all__ = [
    'UnifiedSearchService',
    'SearchFilter', 
    'SearchResult',
    'SearchError'
] 