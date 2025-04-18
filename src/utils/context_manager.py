"""
Enhanced context management system for the Egypt Tourism Chatbot.
Provides sophisticated context tracking, history management, and reference resolution.
"""
import logging
import re
import copy
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Advanced context manager for tracking conversation state and history.
    Manages context across multiple turns and provides reference resolution.
    """
    
    def __init__(self, session_manager=None, max_history_size: int = 10):
        """
        Initialize the context manager.
        
        Args:
            session_manager: Session manager for persistent storage
            max_history_size (int): Maximum number of turns to keep in history
        """
        self.session_manager = session_manager
        self.max_history_size = max_history_size
        
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current context for a session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Dict: Current context
        """
        if not self.session_manager:
            logger.warning("No session manager available for context retrieval")
            return self._create_empty_context()
            
        try:
            context = self.session_manager.get_context(session_id)
            
            if not context:
                context = self._create_empty_context()
                self.session_manager.set_context(session_id, context)
                
            return context
        except Exception as e:
            logger.error(f"Error getting context for session {session_id}: {str(e)}")
            return self._create_empty_context()
            
    def update_context(self, session_id: str, user_message: str, nlu_result: Dict, 
                    response: Dict, dialog_action: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Update context with new information from the current turn.
        
        Args:
            session_id (str): Session ID
            user_message (str): User's message
            nlu_result (Dict): NLU processing result
            response (Dict): Generated response
            dialog_action (Dict, optional): Dialog action that generated the response
            
        Returns:
            Dict: Updated context
        """
        # Get current context
        context = self.get_context(session_id)
        
        # Update basic information
        context["last_updated"] = datetime.now().isoformat()
        context["last_intent"] = nlu_result.get("intent")
        context["language"] = nlu_result.get("language", context.get("language", "en"))
        
        # Update dialog state
        if dialog_action and "next_state" in dialog_action:
            context["dialog_state"] = dialog_action["next_state"]
            
        # Update turn count
        context["turn_count"] = context.get("turn_count", 0) + 1
        
        # Merge entities
        self._update_entities(context, nlu_result)
        
        # Add current turn to history
        self._add_to_history(context, user_message, nlu_result, response, dialog_action)
        
        # Store updated context
        if self.session_manager:
            try:
                self.session_manager.set_context(session_id, context)
            except Exception as e:
                logger.error(f"Error updating context for session {session_id}: {str(e)}")
        
        return context
    
    def resolve_references(self, text: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Resolve references to previous entities and conversation elements.
        
        Args:
            text (str): User's message
            context (Dict): Current context
            
        Returns:
            Tuple[str, Dict]: Resolved text and entity references
        """
        if not text or not context:
            return text, {}
            
        # Create a dict to track resolved references
        resolved_references = {}
        
        # Look for pronouns and resolve them
        pronoun_map = {
            "it": ["attraction", "restaurant", "hotel", "location"],
            "they": ["attractions", "restaurants", "hotels", "locations"],
            "there": ["location"],
            "them": ["attractions", "restaurants", "hotels"],
            "that place": ["location", "attraction", "restaurant", "hotel"],
            "this place": ["location", "attraction", "restaurant", "hotel"],
        }
        
        # Get active entities from context
        active_entities = self._get_active_entities(context)
        
        # Simple pronoun resolution
        words = text.lower().split()
        for pronoun, entity_types in pronoun_map.items():
            if pronoun in text.lower():
                # Find the most recently mentioned entity of the appropriate types
                for entity_type in entity_types:
                    if entity_type in active_entities and active_entities[entity_type]:
                        resolved_references[pronoun] = {
                            "type": entity_type,
                            "value": active_entities[entity_type][-1]
                        }
                        break
        
        # Check for specific reference patterns like "the first one", "the second", etc.
        ordinal_refs = {
            "the first one": 0,
            "the second one": 1,
            "the third one": 2,
            "the first": 0,
            "the second": 1,
            "the third": 2,
            "the last one": -1,
            "the previous one": -1
        }
        
        for ref, index in ordinal_refs.items():
            if ref in text.lower():
                # Look for lists in the last bot response
                history = context.get("history", [])
                if history:
                    last_response = history[-1].get("response", {})
                    response_text = last_response.get("text", "")
                    
                    # Check if the response contains a list
                    list_items = self._extract_list_items(response_text)
                    
                    if list_items and 0 <= index < len(list_items) or index == -1:
                        idx = index if index >= 0 else len(list_items) - 1
                        resolved_references[ref] = {
                            "type": "list_item",
                            "value": list_items[idx]
                        }
        
        # For now, we don't modify the original text, just return references
        # A more advanced implementation could replace pronouns with their referents
        return text, resolved_references
        
    def _create_empty_context(self) -> Dict[str, Any]:
        """
        Create an empty context structure.
        
        Returns:
            Dict: Empty context template
        """
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "turn_count": 0,
            "dialog_state": "greeting",
            "language": "en",
            "entities": {},
            "history": [],
            "preferences": {}
        }
    
    def _update_entities(self, context: Dict[str, Any], nlu_result: Dict[str, Any]):
        """
        Update context entities with new entities from NLU result.
        
        Args:
            context (Dict): Current context
            nlu_result (Dict): NLU processing result
        """
        # Initialize entities if not present
        if "entities" not in context:
            context["entities"] = {}
            
        # Get entities from NLU result
        new_entities = nlu_result.get("entities", {})
        
        # Merge with existing entities
        for entity_type, entity_values in new_entities.items():
            if not entity_values:
                continue
                
            if entity_type not in context["entities"]:
                context["entities"][entity_type] = []
                
            # Add new entities, filtering duplicates
            for value in entity_values:
                if value not in context["entities"][entity_type]:
                    context["entities"][entity_type].append(value)
                    
        # Get entity confidences
        confidences = nlu_result.get("confidence", {})
        
        # Track entity mentions with timestamp and confidence
        if "entity_mentions" not in context:
            context["entity_mentions"] = {}
            
        for entity_type, entity_values in new_entities.items():
            if not entity_values:
                continue
                
            if entity_type not in context["entity_mentions"]:
                context["entity_mentions"][entity_type] = {}
                
            for i, value in enumerate(entity_values):
                conf = 1.0  # Default confidence
                
                # Get confidence if available
                if entity_type in confidences and i < len(confidences[entity_type]):
                    conf = confidences[entity_type][i]
                    
                # Add or update mention
                if value not in context["entity_mentions"][entity_type]:
                    context["entity_mentions"][entity_type][value] = []
                    
                context["entity_mentions"][entity_type][value].append({
                    "timestamp": datetime.now().isoformat(),
                    "confidence": conf,
                    "turn": context.get("turn_count", 0)
                })
    
    def _add_to_history(self, context: Dict[str, Any], user_message: str, nlu_result: Dict,
                     response: Dict, dialog_action: Optional[Dict] = None):
        """
        Add current turn to conversation history.
        
        Args:
            context (Dict): Current context
            user_message (str): User's message
            nlu_result (Dict): NLU processing result
            response (Dict): Generated response
            dialog_action (Dict, optional): Dialog action that generated the response
        """
        # Initialize history if not present
        if "history" not in context:
            context["history"] = []
            
        # Create turn data
        turn_data = {
            "timestamp": datetime.now().isoformat(),
            "turn": context.get("turn_count", 0),
            "user_message": user_message,
            "intent": nlu_result.get("intent"),
            "intent_confidence": nlu_result.get("confidence"),
            "entities": nlu_result.get("entities", {}),
            "response": response,
            "dialog_action": dialog_action
        }
        
        # Add to history
        context["history"].append(turn_data)
        
        # Trim history if it's too long
        if len(context["history"]) > self.max_history_size:
            context["history"] = context["history"][-self.max_history_size:]
    
    def _get_active_entities(self, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get active entities for reference resolution.
        
        Args:
            context (Dict): Current context
            
        Returns:
            Dict: Active entities by type
        """
        # Start with all entities from context
        active_entities = copy.deepcopy(context.get("entities", {}))
        
        # Get entities mentioned in recent turns
        history = context.get("history", [])
        
        # Prioritize recently mentioned entities
        for turn in reversed(history[-3:]):  # Look at last 3 turns
            entities = turn.get("entities", {})
            
            for entity_type, values in entities.items():
                if not values:
                    continue
                    
                if entity_type not in active_entities:
                    active_entities[entity_type] = []
                    
                # Move recent entities to the end of the list (higher priority)
                for value in values:
                    if value in active_entities[entity_type]:
                        active_entities[entity_type].remove(value)
                    active_entities[entity_type].append(value)
        
        return active_entities
    
    def _extract_list_items(self, text: str) -> List[str]:
        """
        Extract list items from text.
        
        Args:
            text (str): Text to parse
            
        Returns:
            List[str]: Extracted list items
        """
        # Simple extraction of numbered or bulleted list items
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for numbered list format: "1. item" or "1) item"
            if re.match(r'^\d+[\.\)]', line):
                item = re.sub(r'^\d+[\.\)]', '', line).strip()
                if item:
                    items.append(item)
                    
            # Check for bulleted list format: "• item" or "- item" or "* item"
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                item = line[1:].strip()
                if item:
                    items.append(item)
        
        return items
        
    def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """
        Update user preferences in context.
        
        Args:
            session_id (str): Session ID
            preferences (Dict): User preferences to update
        """
        context = self.get_context(session_id)
        
        if "preferences" not in context:
            context["preferences"] = {}
            
        # Update preferences
        for key, value in preferences.items():
            context["preferences"][key] = value
            
        # Store updated context
        if self.session_manager:
            try:
                self.session_manager.set_context(session_id, context)
            except Exception as e:
                logger.error(f"Error updating preferences for session {session_id}: {str(e)}")
                
    def clear_context(self, session_id: str) -> bool:
        """
        Clear context for a session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: Success flag
        """
        if not self.session_manager:
            return False
            
        try:
            empty_context = self._create_empty_context()
            self.session_manager.set_context(session_id, empty_context)
            return True
        except Exception as e:
            logger.error(f"Error clearing context for session {session_id}: {str(e)}")
            return False 
