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
    Get overview statistics for the chatbot.
    Includes total sessions, users, messages, and feedback (last 30 days).
    """
    try:
        db_manager = _get_db_manager()
        
        # Get data from the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        events = db_manager.log_analytics_event(
            filters={
                "timestamp_gte": start_date.isoformat(),
                "timestamp_lt": end_date.isoformat()
            },
            limit=100000 # Consider performance implications
        )
        
        # --- Aggregation Logic (Same as before, but check event_data parsing) ---
        # Check if event_data was correctly parsed from JSON string by get_analytics_events
        valid_events = [e for e in events if isinstance(e.get('event_data'), dict)] # Ensure event_data is a dict
        if len(valid_events) != len(events):
             logger.warning(f"Some analytics events had invalid event_data format (expected dict). Found {len(valid_events)} valid out of {len(events)}.")
             
        stats = {
            "total_sessions": len(set(e["session_id"] for e in valid_events if e["session_id"])),
            "total_users": len(set(e["user_id"] for e in valid_events if e["user_id"])),
            "total_messages": sum(1 for e in valid_events if e["event_type"] in ["user_message", "bot_message"]),
            "user_messages": sum(1 for e in valid_events if e["event_type"] == "user_message"),
            "bot_messages": sum(1 for e in valid_events if e["event_type"] == "bot_message"),
            "average_session_length": 0,
            "feedback": {
                "positive": sum(1 for e in valid_events if e["event_type"] == "user_feedback" and e["event_data"].get("is_positive", False)),
                "negative": sum(1 for e in valid_events if e["event_type"] == "user_feedback" and not e["event_data"].get("is_positive", False))
            },
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": 30
            }
        }
        
        # Calculate average session length (same logic as before)
        if stats["total_sessions"] > 0:
            sessions = defaultdict(list)
            for event in valid_events:
                session_id = event.get("session_id")
                if session_id:
                    sessions[session_id].append(event)
            
            session_durations = []
            for session_id, session_events in sessions.items():
                if len(session_events) < 2: continue # Need at least 2 events for duration
                session_events.sort(key=lambda e: isoparse(e["timestamp"]))
                start = isoparse(session_events[0]["timestamp"])
                end = isoparse(session_events[-1]["timestamp"])
                duration = (end - start).total_seconds()
                if 0 < duration < 3600: 
                    session_durations.append(duration)
            
            if session_durations:
                stats["average_session_length"] = sum(session_durations) / len(session_durations)
        
        return stats # FastAPI handles JSON response
        
    except Exception as e:
        logger.error(f"Error getting overview stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve overview statistics")

@analytics_router.get("/daily", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_daily_stats(days: int = Query(7, ge=1, le=90)): # Use Query for validation
    """
    Get daily statistics for the chatbot.
    """
    try:
        db_manager = _get_db_manager()
        
        # Calculate date range
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = end_date - timedelta(days=days -1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        events = db_manager.log_analytics_event(
            filters={
                "timestamp_gte": start_date.isoformat(),
                "timestamp_lt": (end_date + timedelta(microseconds=1)).isoformat()
            },
            limit=100000
        )
        
        # --- Aggregation Logic (Same as before) ---
        daily_summary = defaultdict(lambda: {"sessions": set(), "messages": 0, "users": set()})
        for event in events:
            try:
                event_time = isoparse(event["timestamp"])
                event_date_str = event_time.strftime('%Y-%m-%d')
                if event.get("session_id"):
                     daily_summary[event_date_str]["sessions"].add(event["session_id"])
                if event.get("user_id"):
                     daily_summary[event_date_str]["users"].add(event["user_id"])
                if event["event_type"] in ["user_message", "bot_message", "user_interaction"]:
                     daily_summary[event_date_str]["messages"] += 1
            except Exception as parse_err:
                 logger.warning(f"Could not process event timestamp or data: {event.get('id')}, Error: {parse_err}")
        
        results = []
        current_date = start_date
        while current_date <= end_date:
             date_str = current_date.strftime('%Y-%m-%d')
             stats = daily_summary[date_str]
             results.append({
                 "date": date_str,
                 "sessions": len(stats["sessions"]),
                 "messages": stats["messages"],
                 "unique_users": len(stats["users"])
             })
             current_date += timedelta(days=1)
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting daily stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve daily statistics")

# Note: No Pydantic model defined for response here, relying on dict structure.
# Consider adding a response_model later for better validation/docs.
@analytics_router.get("/session/{session_id}", 
                       dependencies=[Depends(get_current_active_user)]) # Require any logged-in user (or admin?)
async def get_session_stats(session_id: str):
    """
    Get statistics and events for a specific session.
    """
    try:
        db_manager = _get_db_manager()
        events = db_manager.log_analytics_event(filters={"session_id": session_id}, limit=1000)
        
        if not events:
             raise HTTPException(status_code=404, detail="Session not found or no events logged")
            
        # --- Aggregation Logic (Same as before) ---
        events.sort(key=lambda e: isoparse(e["timestamp"]))
        start_time = isoparse(events[0]["timestamp"])
        end_time = isoparse(events[-1]["timestamp"])
        duration_seconds = (end_time - start_time).total_seconds()
        # Filter for user interaction events more robustly
        user_interactions = [e for e in events if e["event_type"] == "user_interaction"]
        
        session_details = {
            "session_id": session_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "interaction_count": len(user_interactions),
            "user_id": events[0].get("user_id"), # Assuming user_id is consistent
            "events": events # Return raw events for detail
        }
        
        return session_details
        
    except Exception as e:
        logger.error(f"Error getting session stats for {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve session statistics")

@analytics_router.get("/intents", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_intent_distribution():
    """
    Get distribution of intents across all sessions.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get interaction events (assuming intent is in event_data)
        events = db_manager.log_analytics_event(filters={"event_type": "user_interaction"}, limit=100000)
        
        intent_counts = Counter()
        for event in events:
            # Ensure event_data is a dict and contains intent
            event_data = event.get("event_data")
            if isinstance(event_data, dict):
                intent = event_data.get("intent")
                if intent:
                    intent_counts[intent] += 1
            else:
                logger.warning(f"Skipping event {event.get('id')} for intent count due to invalid event_data format.")
        
        # Convert Counter to desired format
        distribution = [
            {"intent": intent, "count": count, "percentage": (count / sum(intent_counts.values())) * 100 if sum(intent_counts.values()) > 0 else 0}
            for intent, count in intent_counts.items()
        ]
        distribution.sort(key=lambda x: x["count"], reverse=True)
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error getting intent distribution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve intent distribution")

@analytics_router.get("/entities", 
                       dependencies=[Depends(get_current_admin_user)]) # Require admin
def get_entity_distribution():
    """
    Get distribution of extracted entities across all sessions.
    """
    try:
        db_manager = _get_db_manager()
        
        # Get interaction events (assuming entities are in event_data)
        events = db_manager.log_analytics_event(filters={"event_type": "user_interaction"}, limit=100000)
        
        entity_counts = Counter()
        entity_values = defaultdict(Counter)
        
        for event in events:
            event_data = event.get("event_data")
            if isinstance(event_data, dict):
                entities = event_data.get("entities")
                if isinstance(entities, dict):
                    for entity_type, entity_list in entities.items():
                        if isinstance(entity_list, list):
                             entity_counts[entity_type] += len(entity_list)
                             for entity_value in entity_list:
                                 if isinstance(entity_value, dict): # Handle cases where entity is a dict
                                     value = entity_value.get('value') # Example: extract 'value' field
                                     if value:
                                          entity_values[entity_type][str(value).lower()] += 1 # Count lowercased value
                                 elif isinstance(entity_value, (str, int, float)): # Handle primitive types
                                     entity_values[entity_type][str(entity_value).lower()] += 1
            else:
                 logger.warning(f"Skipping event {event.get('id')} for entity count due to invalid event_data format.")
                 
        # Prepare results
        results = []
        for entity_type, total_count in entity_counts.items():
            top_values = [
                {"value": val, "count": cnt}
                for val, cnt in entity_values[entity_type].most_common(10) # Get top 10 values
            ]
            results.append({
                "entity_type": entity_type,
                "total_count": total_count,
                "top_values": top_values
            })
        
        results.sort(key=lambda x: x["total_count"], reverse=True)
        return results

    except Exception as e:
        logger.error(f"Error getting entity distribution: {str(e)}", exc_info=True)
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
        events = db_manager.log_analytics_event(filters={"event_type": "user_feedback"}, limit=100000)
        
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
        events = db_manager.log_analytics_event(
            filters={"event_type": "user_interaction"}, 
            limit=limit, 
            skip=offset,
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