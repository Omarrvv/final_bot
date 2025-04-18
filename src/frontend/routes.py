from flask import Blueprint, render_template, jsonify, current_app
import os

# Get the absolute path to the static folder
current_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(current_dir, 'static')

frontend = Blueprint('frontend', __name__,
                    template_folder='templates',
                    static_folder=static_folder,
                    static_url_path='/static')

@frontend.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')

@frontend.route('/api/languages')
def get_languages():
    """Return supported languages."""
    return jsonify({
        "languages": [
            {"code": "en", "name": "English", "flag": "us", "direction": "ltr"},
            {"code": "ar", "name": "العربية", "flag": "eg", "direction": "rtl"}
        ]
    })

@frontend.route('/api/suggestions')
def get_suggestions():
    """Return suggested messages."""
    return jsonify({
        "suggestions": [
            {"text": "Tell me about the pyramids", "action": "query"},
            {"text": "Best time to visit Egypt", "action": "query"},
            {"text": "Hotels in Cairo", "action": "query"}
        ]
    })

# Add a debug route to check paths
@frontend.route('/debug-static')
def debug_static():
    """Debug route to check static file paths."""
    return jsonify({
        "static_folder": static_folder,
        "static_exists": os.path.exists(static_folder),
        "css_path": os.path.join(static_folder, 'css/style.css'),
        "css_exists": os.path.exists(os.path.join(static_folder, 'css/style.css')),
        "js_path": os.path.join(static_folder, 'js/script.js'),
        "js_exists": os.path.exists(os.path.join(static_folder, 'js/script.js')),
        "img_path": os.path.join(static_folder, 'img/logo.png'),
        "img_exists": os.path.exists(os.path.join(static_folder, 'img/logo.png'))
    })

def init_app(app):
    """Initialize frontend routes with the Flask app."""
    # Set the static folder explicitly for the app as well
    app.static_folder = static_folder
    app.static_url_path = '/static'
    app.register_blueprint(frontend)