"""
User Repository Module for the Egypt Tourism Chatbot.

This module provides a repository class for handling database operations related to users.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.repositories.base_repository import BaseRepository
from src.knowledge.core.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class UserRepository(BaseRepository):
    """
    Repository class for user-related database operations.

    This class extends the BaseRepository class to provide user-specific database operations.
    """

    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the user repository.

        Args:
            db_core: Database core instance with connection pool
        """
        super().__init__(
            db_core=db_core,
            table_name="users",
            jsonb_fields=['preferences']
        )

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by username.

        Args:
            username: Username to search for

        Returns:
            dict: User data or None if not found
        """
        logger.info(f"Finding user by username: {username}")
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE username = %s"
            result = self.db.execute_query(sql, (username,), fetchall=False)

            if result:
                # Parse JSON fields
                for field in self.jsonb_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"find_by_username_{username}", e)

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by email.

        Args:
            email: Email to search for

        Returns:
            dict: User data or None if not found
        """
        logger.info(f"Finding user by email: {email}")
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE email = %s"
            result = self.db.execute_query(sql, (email,), fetchall=False)

            if result:
                # Parse JSON fields
                for field in self.jsonb_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"find_by_email_{email}", e)

    def find_by_role(self, role: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find users by role.

        Args:
            role: Role to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of users with the specified role
        """
        logger.info(f"Finding users by role: {role}")
        return self.find(filters={"role": role}, limit=limit, offset=offset)

    def update_last_login(self, user_id: str) -> bool:
        """
        Update the last login timestamp for a user.

        Args:
            user_id: ID of the user

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating last login for user: {user_id}")
        try:
            sql = f"""
                UPDATE {self.table_name} 
                SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            """
            result = self.db.execute_query(sql, (user_id,), fetchall=False)
            return result is not None
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
            return False

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences.

        Args:
            user_id: ID of the user
            preferences: Dictionary of preferences to update

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating preferences for user: {user_id}")
        return self.update(user_id, {"preferences": preferences})

    def search_users(self, query: Optional[str] = None,
                    role: Optional[str] = None,
                    limit: int = 10,
                    offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search users based on various criteria.

        Args:
            query: Text query to search for in username or email
            role: Role to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of users matching the criteria
        """
        logger.info(f"Searching users with query={query}, role={role}")

        try:
            # Build the base query
            base_query = f"SELECT * FROM {self.table_name} WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += " AND (username ILIKE %s OR email ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if role:
                base_query += " AND role = %s"
                params.append(role)

            # Add ordering and pagination
            base_query += " ORDER BY username LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.db.execute_query(base_query, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("search_users", e, return_empty_list=True) 