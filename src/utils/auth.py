"""
Authentication utilities for the Egypt Tourism Chatbot.
Provides JWT token generation, validation, and user authentication.
(Adapted for FastAPI)
"""
import os
import bcrypt
import logging
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import functools

# FastAPI specific imports
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

# Assuming user model might be defined elsewhere, or using dict for now
# from src.models.user import User # Example if you have a User model

logger = logging.getLogger(__name__)

# --- JWT Configuration --- 
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Use a default secret for development environments ONLY
    logger.warning("JWT_SECRET environment variable not set! Using default secret for development only.")
    JWT_SECRET = "dev-jwt-secret-not-for-production"
        
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours

# --- FastAPI OAuth2 Scheme --- 
# The tokenUrl should point to your login endpoint (which we haven't created yet)
# Using a placeholder for now.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # Placeholder URL

# --- Token Generation/Validation (Framework Agnostic) --- 
def generate_token(user_id: str, extra_claims: Dict = None) -> str:
    """Generate a JWT token for a user."""
    if extra_claims is None:
        extra_claims = {}
    
    expire = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION_SECONDS)
    payload = {
        "sub": user_id, # Standard claim for subject (user ID)
        "iat": datetime.now(timezone.utc), # Standard claim for issued at
        "exp": expire, # Standard claim for expiration
    }
    payload.update(extra_claims) # Add custom claims like role, username
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def validate_token(token: str) -> Dict:
    """Validate a JWT token and return its payload."""
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e: # Catch any other decoding errors
        logger.error(f"Unexpected error validating token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- FastAPI Dependency Functions for Authentication --- 
async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    FastAPI dependency function to validate token and return payload.
    Use this in routes requiring authentication.
    """
    return validate_token(token)

async def get_current_active_user(payload: dict = Depends(get_current_user_payload)) -> dict:
    """
    Placeholder dependency to get the current user based on token payload.
    In a real app, this would fetch user details from the database.
    For now, it just returns the payload which contains user info like id, role.
    
    TODO: Replace with actual user fetching logic using db_manager if needed.
    """
    # Example: Fetch user from DB (assuming db_manager is available via Depends or context)
    # user_id = payload.get("sub")
    # db_manager = container.get("database_manager") # Assuming container is accessible
    # user = db_manager.get_user_by_id(user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user # Or a Pydantic User model
    
    # For now, just return the payload as it contains the essential claims
    # Ensure the payload includes necessary info like user_id and role
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload (missing sub)")
        
    # You might want to wrap the payload in a Pydantic model here for consistency
    return payload 

async def get_current_admin_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """
    FastAPI dependency function to ensure the user is an admin.
    Relies on the 'role' claim being present in the token payload.
    """
    user_role = current_user.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operation not permitted: Requires admin privileges"
        )
    return current_user

# --- Authentication Class (Needs Adaptation if used directly by API) ---
# The Auth class methods might need access to the db_manager. 
# If these methods (register/login) are exposed via API endpoints,
# those endpoints should get the db_manager via Depends or container.get.
class Auth:
    """
    Authentication service for user management.
    Handles user registration, login.
    (Database interaction logic might need adjustment for async or dependency injection)
    """
    def __init__(self):
        """Initialize Auth service. Get dependencies later or via method injection."""
        # Lazy load or inject db_manager when needed
        self._db_manager = None
        logger.info("Authentication service initialized (DB Manager will be retrieved on demand)")

    @property
    def db_manager(self):
        """Lazy load DatabaseManager.""" 
        if not self._db_manager:
            try:
                # Assumes container is globally accessible or passed differently
                from src.utils.container import container
                self._db_manager = container.get("database_manager")
                if not self._db_manager:
                     raise RuntimeError("DatabaseManager not found in container")
            except Exception as e:
                 logger.error(f"Failed to get DatabaseManager for Auth class: {e}", exc_info=True)
                 raise RuntimeError("Auth service cannot access database manager")
        return self._db_manager

    def register_user(self, username: str, password: str, email: str, role: str = "user") -> Dict:
        """Register a new user."""
        import uuid
        
        # Check if username already exists using db_manager
        existing_user = self.db_manager.get_user_by_username(username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        # Check email later if needed
        
        # Generate salt and hash password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        # Store hash and salt as bytes or hex strings depending on DB expectation
        hashed_password = bcrypt.hashpw(password_bytes, salt).hex() # Example: store as hex
        salt_hex = salt.hex() # Example: store as hex
        
        # Create user record
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "salt": salt_hex,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None,
            "data": {} # Add empty data field if schema expects it
        }
        
        # Store user via db_manager
        success = self.db_manager.save_user(user)
        if not success:
             raise HTTPException(status_code=500, detail="Failed to save user to database")
        
        # Generate token with role claim
        token = generate_token(
            user_id=user_id,
            extra_claims={
                "username": username,
                "role": role
            }
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "token": token
        }
    
    def login_user(self, username: str, password: str) -> Dict:
        """Authenticate a user."""
        # Get user from database
        user = self.db_manager.get_user_by_username(username)
        if not user:
             raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password
        try:
            password_bytes = password.encode('utf-8')
            stored_hash_hex = user.get("password_hash")
            stored_salt_hex = user.get("salt")
            
            if not stored_hash_hex or not stored_salt_hex:
                raise HTTPException(status_code=500, detail="User record is incomplete (missing hash/salt)")
            
            # Convert hex back to bytes for bcrypt
            stored_hash = bytes.fromhex(stored_hash_hex)
            stored_salt = bytes.fromhex(stored_salt_hex) # Not actually needed by checkpw
            
            # Verify with bcrypt
            if not bcrypt.checkpw(password_bytes, stored_hash):
                 raise HTTPException(status_code=401, detail="Invalid username or password")
                
            # Update last login time (optional, maybe do this after successful login)
            # Consider updating last_login via db_manager.save_user if needed
            
            # Generate token with role claim
            token = generate_token(
                user_id=user["id"],
                extra_claims={
                    "username": user["username"],
                    "role": user.get("role", "user")
                }
            )
            
            return {
                "success": True,
                "user_id": user["id"],
                "token": token,
                "token_type": "bearer",
                "expires_in": JWT_EXPIRATION_SECONDS
            }
            
        except Exception as e:
            logger.error(f"Error verifying password during login: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error during login process")
