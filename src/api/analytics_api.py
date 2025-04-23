"""
REST API routes for accessing analytics data from the Egypt Tourism Chatbot.
Provides endpoints for retrieving statistics and insights.
(Adapted for FastAPI)
"""
# Replace Flask imports with FastAPI
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from datetime import datetime, timedelta
import logging
from collections import Counter, defaultdict # Import Counter/defaultdict for aggregation
from dateutil.parser import isoparse # For parsing ISO timestamps

# Import authentication dependencies and container/db_manager access method
from src.utils.auth import get_current_active_user, get_current_admin_user # Use FastAPI dependencies
from src.utils.container import container 
from src.knowledge.database import DatabaseManager # For type hinting
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Create FastAPI router instead of Flask Blueprint
analytics_router = APIRouter(
    prefix="/stats", # Prefix for all routes in this router
    tags=["Analytics"], # Tag for OpenAPI documentation
    # Define dependencies for all routes in this router if needed
    # dependencies=[Depends(get_current_admin_user)] # Example: Secure all routes
)

# Helper to get DB manager (could also be a FastAPI dependency)
def _get_db_manager() -> DatabaseManager:
    db_manager = container.get("database_manager")
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database manager is unavailable.")
    return db_manager

# --- Migrated Routes ---

@analytics_router.get("/overview", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
async def get_overview_stats():
    """
    Get basic usage statistics.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get all analytics events
        events = db_manager.get_analytics_events(
            limit=100000
        )
        
        # Process events to calculate basic statistics
        valid_events = []
        user_interactions = 0
        unique_users = set()
        unique_sessions = set()
        intents = {}
        
        for event in events:
            # Check if event_data was correctly parsed from JSON string by get_analytics_events
            event_data = event.get("event_data")
            if isinstance(event_data, dict):
                valid_events.append(event)
                
                # Count event types
                event_type = event.get("event_type")
                if event_type == "user_interaction":
                    user_interactions += 1
                
                # Track unique users and sessions
                user_id = event.get("user_id")
                session_id = event.get("session_id")
                
                if user_id:
                    unique_users.add(user_id)
                if session_id:
                    unique_sessions.add(session_id)
                
                # Count intents
                if event_type == "user_interaction" and event_data.get("intent"):
                    intent = event_data.get("intent")
                    if intent not in intents:
                        intents[intent] = 0
                    intents[intent] += 1
        
        # Warn if some events couldn't be processed
        if len(valid_events) < len(events):
            logger.warning(f"Some analytics events had invalid event_data format (expected dict). Found {len(valid_events)} valid out of {len(events)}.")
        
        # Calculate additional statistics
        top_intents = sorted(
            [{"intent": k, "count": v} for k, v in intents.items()],
            key=lambda x: x["count"], 
            reverse=True
        )[:10]  # Get top 10 intents
        
        return {
            "total_events": len(valid_events),
            "user_interactions": user_interactions,
            "unique_users": len(unique_users),
            "unique_sessions": len(unique_sessions),
            "top_intents": top_intents
        }
    except Exception as e:
        logger.error(f"Error getting overview stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve overview stats: {str(e)}")

@analytics_router.get("/daily", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_daily_stats(days: int = Query(7, ge=1, le=90)): # Use Query for validation
    """
    Get daily usage statistics over a period of days.
    """
    try:
        db_manager = _get_db_manager()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get events from the specified period
        events = db_manager.get_analytics_events(
            filters={
                "timestamp_gte": start_date.isoformat(),
                "timestamp_lt": end_date.isoformat()
            },
            limit=100000
        )
        
        # Prepare data structures
        daily_stats = {}
        
        # Pre-populate days to ensure all days appear in result
        for day_offset in range(days):
            day = (end_date - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            daily_stats[day] = {
                "interactions": 0,
                "unique_sessions": set(),
                "unique_users": set()
            }
        
        # Process events
        for event in events:
            # Extract date from timestamp (format: YYYY-MM-DDTHH:MM:SS)
            timestamp = event.get("timestamp", "")
            if not timestamp or "T" not in timestamp:
                continue
                
            date = timestamp.split("T")[0]  # Get YYYY-MM-DD part
            if date not in daily_stats:
                # Skip dates outside our range
                continue
                
            # Count user interactions
            if event.get("event_type") == "user_interaction":
                daily_stats[date]["interactions"] += 1
                
            # Track unique sessions and users
            session_id = event.get("session_id")
            user_id = event.get("user_id")
            
            if session_id:
                daily_stats[date]["unique_sessions"].add(session_id)
            if user_id:
                daily_stats[date]["unique_users"].add(user_id)
        
        # Convert sets to counts for JSON serialization
        for date, stats in daily_stats.items():
            stats["unique_sessions"] = len(stats["unique_sessions"])
            stats["unique_users"] = len(stats["unique_users"])
        
        # Sort by date (ascending)
        sorted_data = [{"date": k, **v} for k, v in daily_stats.items()]
        sorted_data.sort(key=lambda x: x["date"])
        
        return sorted_data
        
    except Exception as e:
        logger.error(f"Error getting daily stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve daily statistics")

@analytics_router.get("/session/{session_id}", 
                       dependencies=[Depends(get_current_active_user)]) # Require any logged-in user (or admin?)
async def get_session_stats(session_id: str):
    """
    Get detailed statistics for a specific chat session.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get events for the specific session
        events = db_manager.get_analytics_events(filters={"session_id": session_id}, limit=1000)
        
        # Return 404 if no events were found for this session
        if not events:
            raise HTTPException(status_code=404, detail=f"No data found for session: {session_id}")
        
        interactions = []
        start_time = None
        end_time = None
        
        for event in events:
            event_data = event.get("event_data")
            timestamp = event.get("timestamp")
            
            # Try to determine session timing
            if timestamp:
                timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if not start_time or timestamp_dt < start_time:
                    start_time = timestamp_dt
                if not end_time or timestamp_dt > end_time:
                    end_time = timestamp_dt
                    
            # Process user interactions
            if event.get("event_type") == "user_interaction" and isinstance(event_data, dict):
                interactions.append({
                    "user_message": event_data.get("user_message"),
                    "bot_response": event_data.get("bot_response"),
                    "intent": event_data.get("intent"),
                    "confidence": event_data.get("confidence"),
                    "entities": event_data.get("entities"),
                    "timestamp": timestamp
                })
        
        # Calculate session duration if possible
        duration = None
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        
        return {
            "session_id": session_id,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "duration_seconds": duration,
            "interaction_count": len(interactions),
            "interactions": interactions
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (like our 404)
        raise
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session statistics")

@analytics_router.get("/intents", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_intent_distribution():
    """
    Get distribution of intents detected in user interactions.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get user interaction events
        events = db_manager.get_analytics_events(filters={"event_type": "user_interaction"}, limit=100000)
        
        intent_counts = {}
        total_interactions = 0
        low_confidence_count = 0
        confidence_threshold = 0.7  # Configurable threshold
        
        for event in events:
            event_data = event.get("event_data")
            if isinstance(event_data, dict):
                total_interactions += 1
                intent = event_data.get("intent")
                confidence = event_data.get("confidence")
                
                # Count intent occurrences
                if intent:
                    if intent not in intent_counts:
                        intent_counts[intent] = {"count": 0, "low_confidence": 0}
                    intent_counts[intent]["count"] += 1
                    
                    # Track low confidence detections
                    if confidence and confidence < confidence_threshold:
                        intent_counts[intent]["low_confidence"] += 1
                        low_confidence_count += 1
        
        # Calculate percentages and create sorted list
        intent_distribution = []
        for intent, data in intent_counts.items():
            percentage = (data["count"] / total_interactions * 100) if total_interactions > 0 else 0
            intent_distribution.append({
                "intent": intent,
                "count": data["count"],
                "percentage": round(percentage, 2),
                "low_confidence_count": data["low_confidence"]
            })
        
        # Sort by count (descending)
        intent_distribution.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "total_interactions": total_interactions,
            "low_confidence_count": low_confidence_count,
            "low_confidence_percentage": round(low_confidence_count / total_interactions * 100, 2) if total_interactions > 0 else 0,
            "intents": intent_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting intent distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve intent distribution")

@analytics_router.get("/entities", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_entity_distribution():
    """
    Get distribution of entity types detected in user interactions.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get user interaction events
        events = db_manager.get_analytics_events(filters={"event_type": "user_interaction"}, limit=100000)
        
        entity_counts = {}
        total_entities = 0
        
        for event in events:
            event_data = event.get("event_data")
            if isinstance(event_data, dict):
                entities = event_data.get("entities", [])
                
                if isinstance(entities, list):
                    for entity in entities:
                        if isinstance(entity, dict):
                            entity_type = entity.get("type")
                            if entity_type:
                                if entity_type not in entity_counts:
                                    entity_counts[entity_type] = 0
                                entity_counts[entity_type] += 1
                                total_entities += 1
        
        # Create sorted list of entity types
        entity_distribution = []
        for entity_type, count in entity_counts.items():
            percentage = (count / total_entities * 100) if total_entities > 0 else 0
            entity_distribution.append({
                "entity_type": entity_type,
                "count": count,
                "percentage": round(percentage, 2)
            })
        
        # Sort by count (descending)
        entity_distribution.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "total_entities": total_entities,
            "entities": entity_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting entity distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entity distribution")

@analytics_router.get("/feedback", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_feedback_stats():
    """
    Get feedback statistics.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get feedback events
        events = db_manager.get_analytics_events(filters={"event_type": "user_feedback"}, limit=100000)
        
        feedback_list = []
        positive_count = 0
        negative_count = 0
        ratings = []

        for event in events:
            event_data = event.get("event_data")
            if isinstance(event_data, dict):
                rating = event_data.get("rating") # Assuming rating is stored
                is_positive = event_data.get("is_positive") # Or derive from rating
                feedback_list.append({
                     "message_id": event_data.get("message_id"),
                     "rating": rating,
                     "comment": event_data.get("comment"),
                     "timestamp": event.get("timestamp")
                 })
                if is_positive:
                     positive_count += 1
                else:
                     negative_count += 1
                if isinstance(rating, (int, float)):
                    ratings.append(rating)
            else:
                 logger.warning(f"Skipping event {event.get('id')} for feedback stats due to invalid event_data format.")

        # Calculate average rating if possible
        average_rating = sum(ratings) / len(ratings) if ratings else None
        
        return {
            "total_feedback": len(feedback_list),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "average_rating": average_rating,
            # Optionally return recent feedback items
            "recent_feedback": sorted(feedback_list, key=lambda x: x["timestamp"], reverse=True)[:50] 
        }

    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback statistics")

@analytics_router.get("/messages", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_message_stats(limit: int = Query(100, ge=1, le=1000), 
                      offset: int = Query(0, ge=0)): # Add pagination
    """
    Get recent user messages and their associated NLU results.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get user interaction events, sorted descending by time
        events = db_manager.get_analytics_events(
            filters={"event_type": "user_interaction"}, 
            limit=limit, 
            offset=offset,
            sort_by="timestamp", 
            sort_dir=-1
        )
        
        messages = []
        for event in events:
             event_data = event.get("event_data")
             if isinstance(event_data, dict):
                 messages.append({
                     "timestamp": event.get("timestamp"),
                     "session_id": event.get("session_id"),
                     "user_id": event.get("user_id"),
                     "user_message": event_data.get("user_message"),
                     "intent": event_data.get("intent"),
                     "confidence": event_data.get("confidence"),
                     "entities": event_data.get("entities")
                 })
             else:
                 logger.warning(f"Skipping event {event.get('id')} for message stats due to invalid event_data format.")
                 
        return messages

    except Exception as e:
        logger.error(f"Error getting message stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve message statistics") 