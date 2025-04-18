"""
Security utilities and middleware for the Egypt Tourism Chatbot.
Provides various security protections including input validation, CSRF protection, and more.
"""
import re
import json
import logging
import hashlib
import secrets
import time
import random
from functools import wraps
from typing import Dict, List, Any, Optional, Callable, Union
from flask import request, jsonify, session, abort, current_app, Response
import html

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware providing various protections."""
    
    def __init__(self, app=None):
        """
        Initialize the security middleware.
        
        Args:
            app: Flask application instance
        """
        self.csrf_tokens = {}
        self.token_expiry = 3600  # 1 hour
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask application.
        
        Args:
            app: Flask application instance
        """
        app.config.setdefault('CSRF_ENABLED', True)
        app.config.setdefault('CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])
        app.config.setdefault('CSRF_EXEMPT_ROUTES', ['/api/csrf-token'])
        
        @app.after_request
        def set_secure_headers(response):
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' data:; font-src 'self' cdnjs.cloudflare.com"
            
            return response
        
        @app.before_request
        def csrf_protect():
            """Protect against CSRF attacks by validating tokens."""
            if not app.config['CSRF_ENABLED']:
                return
                
            # Skip CSRF check for exempt routes
            for route in app.config['CSRF_EXEMPT_ROUTES']:
                if request.path.startswith(route):
                    return
                    
            # Only check CSRF for specified methods
            if request.method not in app.config['CSRF_METHODS']:
                return
                
            # Check CSRF token
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not token or not self.validate_csrf_token(token):
                logger.warning(f"CSRF validation failed for {request.path}")
                return jsonify({
                    "status": "error",
                    "message": "CSRF validation failed. Please refresh the page and try again."
                }), 403
        
        # Log suspicious activities
        @app.before_request
        def log_suspicious_activity():
            # Check for SQL injection attempts
            if self._contains_sql_injection(request):
                logger.warning(f"Possible SQL injection attempt: {request.path}, IP: {request.remote_addr}")
            
            # Check for XSS attempts
            if self._contains_xss(request):
                logger.warning(f"Possible XSS attempt: {request.path}, IP: {request.remote_addr}")
            
            # Rate limiting check (basic implementation)
            if not self._check_rate_limit(request):
                logger.warning(f"Rate limit exceeded: {request.path}, IP: {request.remote_addr}")
                return jsonify({"error": "Rate limit exceeded"}), 429
        
        # Generate CSRF token route
        @app.route('/api/csrf-token', methods=['GET'])
        def get_csrf_token():
            token = self.generate_csrf_token()
            return jsonify({"csrf_token": token})
    
    def generate_csrf_token(self) -> str:
        """
        Generate a new CSRF token.
        
        Returns:
            str: CSRF token
        """
        # Generate a random token
        token = secrets.token_hex(32)
        
        # Store the token with expiry time
        self.csrf_tokens[token] = {
            'expires': time.time() + self.token_expiry
        }
        
        # Clean up expired tokens periodically
        if random.random() < 0.1:  # 10% chance to clean up
            self._cleanup_expired_tokens()
            
        return token
    
    def validate_csrf_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token (str): CSRF token to validate
            
        Returns:
            bool: True if the token is valid, False otherwise
        """
        # Check if token exists and has not expired
        if token in self.csrf_tokens:
            token_data = self.csrf_tokens[token]
            if token_data['expires'] > time.time():
                return True
                
            # Token expired, remove it
            del self.csrf_tokens[token]
            
        return False
    
    def _cleanup_expired_tokens(self):
        """Remove expired CSRF tokens."""
        current_time = time.time()
        expired_tokens = []
        
        for token, data in self.csrf_tokens.items():
            if data['expires'] <= current_time:
                expired_tokens.append(token)
                
        for token in expired_tokens:
            del self.csrf_tokens[token]
    
    def _contains_sql_injection(self, req: request) -> bool:
        """
        Check if request might contain SQL injection attempt.
        
        Args:
            req: Flask request object
            
        Returns:
            bool: True if suspicious, False otherwise
        """
        # Simple SQL injection detection (not comprehensive)
        sql_patterns = [
            r'\bSELECT\b.*\bFROM\b',
            r'\bUNION\b.*\bSELECT\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bDROP\b.*\bTABLE\b',
            r"'.*;--",
            r'--\s*$'
        ]
        
        # Check URL parameters
        for param in req.args.values():
            for pattern in sql_patterns:
                if re.search(pattern, param, re.IGNORECASE):
                    return True
        
        # Check JSON body
        if req.is_json:
            try:
                data = req.get_json()
                if data:
                    # Convert to string for checking
                    data_str = json.dumps(data)
                    for pattern in sql_patterns:
                        if re.search(pattern, data_str, re.IGNORECASE):
                            return True
            except Exception:
                pass
        
        # Check form data
        for value in req.form.values():
            for pattern in sql_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return True
        
        return False
    
    def _contains_xss(self, req: request) -> bool:
        """
        Check if request might contain XSS attempt.
        
        Args:
            req: Flask request object
            
        Returns:
            bool: True if suspicious, False otherwise
        """
        # Simple XSS detection (not comprehensive)
        xss_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'onmouseover=',
            r'<img[^>]*src=[^>]*>'
        ]
        
        # Check URL parameters
        for param in req.args.values():
            for pattern in xss_patterns:
                if re.search(pattern, param, re.IGNORECASE):
                    return True
        
        # Check JSON body
        if req.is_json:
            try:
                data = req.get_json()
                if data:
                    # Convert to string for checking
                    data_str = json.dumps(data)
                    for pattern in xss_patterns:
                        if re.search(pattern, data_str, re.IGNORECASE):
                            return True
            except Exception:
                pass
        
        # Check form data
        for value in req.form.values():
            for pattern in xss_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return True
        
        return False
    
    def _check_rate_limit(self, req: request) -> bool:
        """
        Check if request exceeds rate limits.
        This is a basic implementation. For production,
        use a more robust solution like Flask-Limiter.
        
        Args:
            req: Flask request object
            
        Returns:
            bool: True if within limits, False if exceeded
        """
        # This is just a placeholder - real implementation would use Redis or similar
        # for tracking request rates
        return True

def sanitize_input(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """
    Sanitize input data to prevent XSS and injection attacks.
    
    Args:
        data: Input data to sanitize
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Sanitize string
        return html.escape(data)
    elif isinstance(data, dict):
        # Sanitize dictionary
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Sanitize list
        return [sanitize_input(item) for item in data]
    else:
        # Return as is for other types
        return data

def validate_json_schema(schema: Dict) -> Callable:
    """
    Decorator to validate JSON request data against a schema.
    
    Args:
        schema (dict): JSON schema to validate against
        
    Returns:
        Function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON data
            if not request.is_json:
                return jsonify({"error": "Expected JSON data"}), 400
            
            try:
                data = request.get_json()
                
                # Basic schema validation (in production, use a library like jsonschema)
                for field, field_schema in schema.items():
                    # Check required fields
                    if field_schema.get("required", False) and field not in data:
                        return jsonify({"error": f"Missing required field: {field}"}), 400
                    
                    # Skip validation if field not present and not required
                    if field not in data:
                        continue
                    
                    # Validate field type
                    field_type = field_schema.get("type")
                    if field_type:
                        if field_type == "string" and not isinstance(data[field], str):
                            return jsonify({"error": f"Field {field} must be a string"}), 400
                        elif field_type == "integer" and not isinstance(data[field], int):
                            return jsonify({"error": f"Field {field} must be an integer"}), 400
                        elif field_type == "number" and not isinstance(data[field], (int, float)):
                            return jsonify({"error": f"Field {field} must be a number"}), 400
                        elif field_type == "boolean" and not isinstance(data[field], bool):
                            return jsonify({"error": f"Field {field} must be a boolean"}), 400
                        elif field_type == "array" and not isinstance(data[field], list):
                            return jsonify({"error": f"Field {field} must be an array"}), 400
                        elif field_type == "object" and not isinstance(data[field], dict):
                            return jsonify({"error": f"Field {field} must be an object"}), 400
                    
                    # Validate string pattern
                    if field_type == "string" and "pattern" in field_schema:
                        pattern = field_schema["pattern"]
                        if not re.match(pattern, data[field]):
                            return jsonify({"error": f"Field {field} does not match required pattern"}), 400
                    
                    # Validate min/max length for strings
                    if field_type == "string":
                        if "minLength" in field_schema and len(data[field]) < field_schema["minLength"]:
                            return jsonify({"error": f"Field {field} must be at least {field_schema['minLength']} characters"}), 400
                        if "maxLength" in field_schema and len(data[field]) > field_schema["maxLength"]:
                            return jsonify({"error": f"Field {field} must be at most {field_schema['maxLength']} characters"}), 400
                    
                    # Validate min/max for numbers
                    if field_type in ["integer", "number"]:
                        if "minimum" in field_schema and data[field] < field_schema["minimum"]:
                            return jsonify({"error": f"Field {field} must be at least {field_schema['minimum']}"}), 400
                        if "maximum" in field_schema and data[field] > field_schema["maximum"]:
                            return jsonify({"error": f"Field {field} must be at most {field_schema['maximum']}"}), 400
                    
                    # Validate array length
                    if field_type == "array":
                        if "minItems" in field_schema and len(data[field]) < field_schema["minItems"]:
                            return jsonify({"error": f"Field {field} must have at least {field_schema['minItems']} items"}), 400
                        if "maxItems" in field_schema and len(data[field]) > field_schema["maxItems"]:
                            return jsonify({"error": f"Field {field} must have at most {field_schema['maxItems']} items"}), 400
                
                # Sanitize input data
                sanitized_data = sanitize_input(data)
                
                # Replace request data with sanitized version
                request.data = json.dumps(sanitized_data).encode()
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Schema validation error: {str(e)}")
                return jsonify({"error": "Invalid JSON data"}), 400
                
        return decorated_function
    return decorator

# Do not attempt to modify current_app here - it causes "Working outside of application context" error