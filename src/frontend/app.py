from flask import Blueprint, render_template, jsonify

frontend = Blueprint('frontend', __name__,
                    template_folder='templates',
                    static_folder='static',
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

def init_app(app):
    """Initialize frontend routes with the Flask app."""
    app.register_blueprint(frontend)