"""
Main application module for the Egypt Tourism Chatbot.
Orchestrates components and manages application lifecycle.
"""
import os
import logging
import json
import importlib
import time
import functools
from datetime import datetime
# Import core components here to avoid circular imports
from src.nlu.engine import NLUEngine
from src.knowledge.knowledge_base import KnowledgeBase
from src.dialog.manager import DialogManager
from src.response.generator import ResponseGenerator
from src.integration.service_hub import ServiceHub
from src.utils.session import SessionManager
# Fix duplicate dotenv import
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from src.utils.security import SecurityMiddleware
from src.utils.error_handler import error_handler
from src.utils.exceptions import ChatbotError, AuthenticationError, ResourceNotFoundError
from src.chatbot import Chatbot
from src.api.metrics_api import metrics_api
from src.api.analytics_api import analytics_api
from flask_wtf.csrf import generate_csrf

# Load environment variables early
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create necessary directories for configs
os.makedirs('./configs', exist_ok=True)
os.makedirs('./data', exist_ok=True)
os.makedirs('./configs/response_templates', exist_ok=True)

# Performance tracking decorator
def track_performance(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Log performance data
        logger.info(f"PERF: {func.__name__} took {duration:.4f}s")
        
        # Alert on slow operations
        if duration > 0.5:  # 500ms threshold
            logger.warning(f"SLOW OPERATION: {func.__name__} took {duration:.4f}s")
            
        return result
    return wrapper

# Cache for frequently accessed data
class SimpleCache:
    def __init__(self, max_size=100, ttl=300):  # 5 minute TTL by default
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['value']
            else:
                # Expired
                del self.cache[key]
        return None
        
    def set(self, key, value):
        # Evict oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
            
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }

# Create global cache instance
response_cache = SimpleCache()
knowledge_cache = SimpleCache()

# Define create_app function
def create_app(config=None):
    # Initialize factory and chatbot INSIDE create_app
    chatbot = None # Default to None
    try:
        # Need to import factory here if moved from global
        from src.utils.factory import component_factory 
        component_factory.initialize()
        # Import Chatbot here if moved from global
        from src.chatbot import Chatbot 
        chatbot_instance = Chatbot(initialize_components=False) 
        chatbot_instance.initialize() 
        chatbot = chatbot_instance # Assign to variable accessible by routes
        logger.info("Chatbot instance created and initialized via factory inside create_app.")
    except Exception as e:
        logger.critical(f"Failed to initialize component factory or chatbot inside create_app: {e}", exc_info=True)
        # Keep chatbot as None

    app = Flask(__name__)

    # Add Secret Key for CSRF protection
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-secure-default-secret-key-for-dev')
    app.config['WTF_CSRF_ENABLED'] = False # Keep disabled for now as per Phase 1 plan, but key is needed

    # ... existing app configurations (CORS, Limiter, etc.) ...
    CORS(app, resources={
        r"/api/*": {"origins": os.getenv("FRONTEND_URL", "*")}, 
        # TODO: Restrict origins properly in Phase 1
        r"/socket.io/*": {"origins": "*"},
        r"/static/*": {"origins": "*"}
    }, supports_credentials=True)
    
    # Rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.getenv("LIMITER_STORAGE_URI", "memory://")
    )

    # Swagger UI setup
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json' # Path to your OpenAPI specification
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Egypt Tourism Chatbot API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Serve static files (like swagger.json)
    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)

    # --- API Routes (To be adapted) ---
    @app.route('/api/health', methods=['GET'])
    def health_check():
        if chatbot is None:
             return jsonify({"status": "error", "message": "Chatbot initialization failed"}), 500
        return jsonify({"status": "ok"})

    @app.route('/api/chat', methods=['POST'])
    @limiter.limit("10 per minute")
    def handle_chat():
        if chatbot is None:
             return jsonify({"error": "Chatbot is not available"}), 503
             
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing message in request body"}), 400
            
        user_message = data['message']
        session_id = data.get('session_id')
        language = data.get('language')
        
        try:
            # Use the single chatbot instance
            response = chatbot.process_message(
                user_message=user_message,
                session_id=session_id,
                language=language
            )
            return jsonify(response)
        except Exception as e:
            logger.error(f"Error handling chat request: {str(e)}", exc_info=True)
            return jsonify({"error": "An internal error occurred"}), 500

    # TODO: Adapt other routes (/api/reset, /api/feedback, /api/suggestions, etc.)
    # to use methods from the `chatbot` instance.
    # Example for reset:
    @app.route('/api/reset', methods=['POST'])
    def reset_session_route():
        if chatbot is None:
             return jsonify({"error": "Chatbot is not available"}), 503
             
        # Handle potential None for request.json
        session_id = None
        if request.is_json and request.json is not None:
            session_id = request.json.get('session_id')
            
        try:
             result = chatbot.reset_session(session_id)
             return jsonify(result)
        except Exception as e:
            logger.error(f"Error resetting session: {e}", exc_info=True)
            return jsonify({"error": "Failed to reset session"}), 500

    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        token = generate_csrf()
        return jsonify({'csrf_token': token})

    # Placeholder for other routes - adapt similarly
    @app.route('/api/feedback', methods=['POST'])
    def handle_feedback():
         if chatbot is None:
              return jsonify({"error": "Chatbot is not available"}), 503
         # TODO: Implement feedback handling via chatbot instance or db_manager directly
         logger.warning("/api/feedback endpoint needs implementation using chatbot instance.")
         # Example: chatbot.log_feedback(data...)
         data = request.get_json()
         if not data:
             return jsonify({"error": "Missing feedback data"}), 400
         # For now, return dummy success
         return jsonify({"success": True, "message": "Feedback received (placeholder."})

    @app.route('/api/suggestions', methods=['GET'])
    def get_suggestions_route():
         if chatbot is None:
              return jsonify({"error": "Chatbot is not available"}), 503
         session_id = request.args.get('session_id')
         language = request.args.get('language', 'en')
         try:
            suggestions = chatbot.get_suggestions(session_id=session_id, language=language)
            return jsonify({"suggestions": suggestions})
         except Exception as e:
             logger.error(f"Error getting suggestions: {e}", exc_info=True)
             return jsonify({"error": "Failed to get suggestions"}), 500

    @app.route('/api/languages', methods=['GET'])
    def get_languages():
        # This might eventually come from NLU engine config or similar
        # For now, keep it simple
        supported_languages = [
            {"code": "en", "name": "English"},
            {"code": "ar", "name": "العربية"}
        ]
        return jsonify({"languages": supported_languages})

    # Serve React App (ensure static folder is correct)
    # Assumes build is in react-frontend/build
    static_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'react-frontend', 'build'))
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            # Serve index.html for any path not matching static files (for client-side routing)
            return send_from_directory(static_folder_path, 'index.html')
            
    return app

# Main entry point (for direct execution, e.g., python src/app.py)
if __name__ == '__main__':
    # Load .env for direct execution
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
    load_dotenv(dotenv_path=dotenv_path)
    
    # Create and run the app
    app = create_app()
    if app:
        # Use environment variables for host/port if available
        host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_RUN_PORT', '5001'))
        debug = os.getenv('FLASK_ENV', 'production') == 'development'
        app.run(host=host, port=port, debug=debug)
    else:
        logger.critical("Application could not be created due to initialization errors.")