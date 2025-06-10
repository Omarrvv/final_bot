"""
FAQ Repository Module for the Egypt Tourism Chatbot.

This module provides a repository class for handling database operations related to tourism FAQs.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.repositories.base_repository import BaseRepository
from src.knowledge.core.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FaqRepository(BaseRepository):
    """
    Repository class for FAQ-related database operations.

    This class extends the BaseRepository class to provide FAQ-specific database operations.
    """

    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the FAQ repository.

        Args:
            db_core: Database core instance with connection pool
        """
        super().__init__(
            db_core=db_core,
            table_name="tourism_faqs",
            jsonb_fields=['question', 'answer', 'data']
        )

    def find_by_category(self, category_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find FAQs by category.

        Args:
            category_id: Category ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of FAQs in the category
        """
        logger.info(f"Finding FAQs by category: {category_id}")
        return self.find(filters={"category_id": category_id}, limit=limit, offset=offset)

    def search_faqs(self, query: Optional[str] = None,
                   category_id: Optional[str] = None,
                   limit: int = 10,
                   offset: int = 0,
                   language: str = "en") -> List[Dict[str, Any]]:
        """
        Search FAQs based on various criteria.

        Args:
            query: Text query to search for in question and answer
            category_id: Category ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns:
            list: List of FAQs matching the criteria
        """
        logger.info(f"Searching FAQs with query={query}, category_id={category_id}")

        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = f"SELECT * FROM {self.table_name} WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += f" AND (question->>'{language}' ILIKE %s OR answer->>'{language}' ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if category_id:
                base_query += " AND category_id = %s"
                params.append(category_id)

            # Add ordering and pagination
            base_query += " ORDER BY question->>%s LIMIT %s OFFSET %s"
            params.extend([language, limit, offset])

            # Execute the query
            results = self.db.execute_query(base_query, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("search_faqs", e, return_empty_list=True) 