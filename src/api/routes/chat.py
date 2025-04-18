"""
Chat-related API endpoints.
"""
from flask import Blueprint, request, jsonify, g
from ...services.chat import ChatService
from ...core.exceptions import ChatbotException

chat_bp = Blueprint('chat', __name__)
chat_service = ChatService()

@chat_bp.route('/chat', methods=['POST'])
def chat_endpoint():
    """Process chat messages and return responses."""
    try:
        data = request.get_json()
        message = data.get('message')
        session_id = data.get('session_id')
        language = data.get('language', 'en')
        
        if not message or not session_id:
            return jsonify({'error': 'Missing required fields'}), 400
            
        response = chat_service.process_message(
            message=message,
            session_id=session_id,
            language=language
        )
        
        return jsonify(response)
    except ChatbotException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        g.log.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """Get suggested queries for the chatbot."""
    try:
        language = request.args.get('language', 'en')
        suggestions = chat_service.get_suggestions(language)
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        g.log.error(f"Error getting suggestions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
