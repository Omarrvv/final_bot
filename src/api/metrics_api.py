"""
Metrics API for the Egypt Tourism Chatbot.
Provides endpoints for accessing performance metrics, including entity recognition stats.
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from src.utils.auth import token_required, admin_required
import logging

logger = logging.getLogger(__name__)

# Create blueprint
metrics_api = Blueprint('metrics', __name__)

@metrics_api.route('/entity-recognition', methods=['GET'])
@token_required
@admin_required
def get_entity_recognition_metrics():
    """
    Get entity recognition performance metrics.
    
    Returns:
        JSON response with entity recognition metrics
    """
    try:
        # Get NLU engine from app context
        nlu_engine = current_app.chatbot.nlu_engine
        
        # Get enhanced entity extractor metrics
        metrics = {}
        
        for language, extractor in nlu_engine.entity_extractors.items():
            if hasattr(extractor, 'get_metrics'):
                metrics[language] = extractor.get_metrics()
            
        return jsonify({
            "entity_recognition": metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting entity recognition metrics: {str(e)}")
        return jsonify({"error": "Failed to retrieve entity recognition metrics"}), 500

@metrics_api.route('/learning', methods=['GET'])
@token_required
@admin_required
def get_learning_metrics():
    """
    Get continuous learning performance metrics.
    
    Returns:
        JSON response with continuous learning metrics
    """
    try:
        # Get NLU engine from app context
        nlu_engine = current_app.chatbot.nlu_engine
        
        # Get learning stats
        learning_stats = nlu_engine.get_learning_stats()
        
        return jsonify(learning_stats), 200
        
    except Exception as e:
        logger.error(f"Error getting learning metrics: {str(e)}")
        return jsonify({"error": "Failed to retrieve learning metrics"}), 500

@metrics_api.route('/entity-feedback', methods=['GET'])
@token_required
@admin_required
def get_entity_feedback_metrics():
    """
    Get entity feedback metrics.
    
    Query parameters:
        days (int): Number of days to include (default: 30)
    
    Returns:
        JSON response with entity feedback metrics
    """
    try:
        # Get database manager from app context
        db_manager = current_app.db_manager
        
        # Get number of days from query params
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get entity feedback events
        events = db_manager.get_analytics_events(
            filters={
                "event_type": "entity_feedback",
                "timestamp_gte": start_date.isoformat(),
                "timestamp_lt": end_date.isoformat()
            },
            limit=1000
        )
        
        # Calculate metrics
        total_feedback = len(events)
        entity_types = {}
        corrections_by_day = {}
        
        for event in events:
            # Count by entity type
            data = event.get("event_data", {})
            for entity_type in data.get("entity_types", []):
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1
                
            # Group by day
            day = event.get("timestamp", "").split("T")[0]  # YYYY-MM-DD
            if day not in corrections_by_day:
                corrections_by_day[day] = 0
            corrections_by_day[day] += 1
        
        return jsonify({
            "total_feedback": total_feedback,
            "entity_types": entity_types,
            "corrections_by_day": corrections_by_day,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting entity feedback metrics: {str(e)}")
        return jsonify({"error": "Failed to retrieve entity feedback metrics"}), 500

@metrics_api.route('/reset-learning', methods=['POST'])
@token_required
@admin_required
def reset_learning():
    """
    Reset continuous learning data.
    
    Request body:
        entity_type (str, optional): Entity type to reset, or null for all
    
    Returns:
        JSON response confirming reset
    """
    try:
        # Get request data
        data = request.get_json() or {}
        entity_type = data.get('entity_type')
        
        # Get NLU engine from app context
        nlu_engine = current_app.chatbot.nlu_engine
        
        # Reset learning data
        nlu_engine.entity_learner.reset(entity_type)
        
        return jsonify({
            "success": True,
            "message": f"Successfully reset learning data for {entity_type or 'all entity types'}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting learning data: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to reset learning data: {str(e)}"
        }), 500 