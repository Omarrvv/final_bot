"""
User model for authentication and authorization.
"""
from typing import Dict, Any, Optional, List


class User:
    """
    User model for authentication and authorization.
    """
    
    def __init__(
        self,
        user_id: str,
        username: str,
        is_authenticated: bool = False,
        roles: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a User instance.
        
        Args:
            user_id: Unique user identifier
            username: User's username
            is_authenticated: Whether the user is authenticated
            roles: User roles for authorization
            data: Additional user data
        """
        self.user_id = user_id
        self.username = username
        self.is_authenticated = is_authenticated
        self.roles = roles or []
        self.data = data or {}
    
    @property
    def id(self) -> str:
        """
        Get user ID.
        
        Returns:
            User ID
        """
        return self.user_id
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary.
        
        Returns:
            User data as dictionary
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "is_authenticated": self.is_authenticated,
            "roles": self.roles,
            "data": self.data,
        } 