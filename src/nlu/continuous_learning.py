"""
Continuous Learning Module for the Egypt Tourism Chatbot.
Allows the system to learn from user interactions and improve over time.
"""
import json
import logging
import os
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class EntityLearner:
    """
    Continuous learning for entity recognition that improves over time.
    Learns from user feedback and corrections to improve entity extraction.
    """
    
    def __init__(self, storage_path: str = "data/learning", min_examples: int = 3, 
                 confidence_threshold: float = 0.7, save_interval: int = 5):
        """
        Initialize the entity learner.
        
        Args:
            storage_path (str): Path to store learned data
            min_examples (int): Minimum examples needed before applying learning
            confidence_threshold (float): Minimum confidence for learned entities
            save_interval (int): Save learned data every N learning events
        """
        self.storage_path = storage_path
        self.min_examples = min_examples
        self.confidence_threshold = confidence_threshold
        self.save_interval = save_interval
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Dictionary to track learned entities
        self.learned_entities = defaultdict(lambda: defaultdict(list))
        
        # Dictionary to track entity corrections
        self.entity_corrections = defaultdict(lambda: defaultdict(list))
        
        # Counter for learning events
        self.learning_events = 0
        
        # Thread lock for concurrency safety
        self.lock = threading.Lock()
        
        # Load previously learned data if available
        self._load_learned_data()
        
    def _load_learned_data(self):
        """Load previously learned data from disk."""
        entity_file = os.path.join(self.storage_path, "learned_entities.json")
        corrections_file = os.path.join(self.storage_path, "entity_corrections.json")
        
        try:
            if os.path.exists(entity_file):
                with open(entity_file, 'r', encoding='utf-8') as f:
                    learned_dict = json.load(f)
                    
                    # Convert dict to defaultdict
                    for entity_type, examples in learned_dict.items():
                        for text_key, entity_examples in examples.items():
                            self.learned_entities[entity_type][text_key] = entity_examples
                    
                    logger.info(f"Loaded {sum(len(examples) for examples in learned_dict.values())} learned entities")
        except Exception as e:
            logger.error(f"Error loading learned entities: {str(e)}")
            
        try:
            if os.path.exists(corrections_file):
                with open(corrections_file, 'r', encoding='utf-8') as f:
                    corrections_dict = json.load(f)
                    
                    # Convert dict to defaultdict
                    for entity_type, corrections in corrections_dict.items():
                        for original, corrected_list in corrections.items():
                            self.entity_corrections[entity_type][original] = corrected_list
                    
                    logger.info(f"Loaded {sum(len(c) for c in corrections_dict.values())} entity corrections")
        except Exception as e:
            logger.error(f"Error loading entity corrections: {str(e)}")
    
    def _save_learned_data(self):
        """Save learned data to disk."""
        entity_file = os.path.join(self.storage_path, "learned_entities.json")
        corrections_file = os.path.join(self.storage_path, "entity_corrections.json")
        
        try:
            # Convert defaultdict to dict for JSON serialization
            learned_dict = {}
            for entity_type, examples in self.learned_entities.items():
                learned_dict[entity_type] = dict(examples)
                
            with open(entity_file, 'w', encoding='utf-8') as f:
                json.dump(learned_dict, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved {sum(len(examples) for examples in learned_dict.values())} learned entities")
        except Exception as e:
            logger.error(f"Error saving learned entities: {str(e)}")
            
        try:
            # Convert defaultdict to dict for JSON serialization
            corrections_dict = {}
            for entity_type, corrections in self.entity_corrections.items():
                corrections_dict[entity_type] = dict(corrections)
                
            with open(corrections_file, 'w', encoding='utf-8') as f:
                json.dump(corrections_dict, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved {sum(len(c) for c in corrections_dict.values())} entity corrections")
        except Exception as e:
            logger.error(f"Error saving entity corrections: {str(e)}")
            
    def learn_from_feedback(self, message: str, extracted_entities: Dict[str, List[str]], 
                         correct_entities: Dict[str, List[str]], user_id: Optional[str] = None) -> bool:
        """
        Learn from explicit user feedback about entities.
        
        Args:
            message (str): Original user message
            extracted_entities (Dict): Entities extracted by the system
            correct_entities (Dict): Correct entities provided by user feedback
            user_id (str, optional): User ID for tracking
            
        Returns:
            bool: Success flag
        """
        with self.lock:
            try:
                self.learning_events += 1
                
                # Process missing entities (entities that should have been extracted)
                for entity_type, entities in correct_entities.items():
                    # Check if this entity type wasn't extracted or some entities were missed
                    if entity_type not in extracted_entities or not set(entities).issubset(set(extracted_entities[entity_type])):
                        # Find the entities that were missed
                        missed_entities = [e for e in entities if entity_type not in extracted_entities or 
                                        e not in extracted_entities[entity_type]]
                        
                        for entity in missed_entities:
                            # Create a key based on normalized message text
                            text_key = self._normalize_text(message)
                            
                            # Add to learned entities
                            if entity not in self.learned_entities[entity_type][text_key]:
                                self.learned_entities[entity_type][text_key].append(entity)
                                logger.info(f"Learned new entity: '{entity}' ({entity_type}) from '{message}'")
                
                # Process incorrect entities (entities that were wrongly extracted)
                for entity_type, entities in extracted_entities.items():
                    if entity_type not in correct_entities:
                        # This entity type shouldn't have been extracted at all
                        for entity in entities:
                            # Record this as a negative example
                            text_key = self._normalize_text(message)
                            negative_key = f"NEG_{entity}"
                            
                            if negative_key not in self.learned_entities[entity_type][text_key]:
                                self.learned_entities[entity_type][text_key].append(negative_key)
                                logger.info(f"Learned negative entity: '{entity}' ({entity_type}) from '{message}'")
                    else:
                        # Find the entities that were incorrectly extracted
                        incorrect_entities = [e for e in entities if e not in correct_entities[entity_type]]
                        
                        for entity in incorrect_entities:
                            # Record this as a negative example
                            text_key = self._normalize_text(message)
                            negative_key = f"NEG_{entity}"
                            
                            if negative_key not in self.learned_entities[entity_type][text_key]:
                                self.learned_entities[entity_type][text_key].append(negative_key)
                                logger.info(f"Learned negative entity: '{entity}' ({entity_type}) from '{message}'")
                
                # Record corrections for entity values
                for entity_type, correct_vals in correct_entities.items():
                    if entity_type in extracted_entities:
                        extracted_vals = extracted_entities[entity_type]
                        
                        # Find potential corrections by comparing values
                        for extracted in extracted_vals:
                            # Find the closest correct entity
                            best_match = None
                            best_score = 0
                            
                            for correct in correct_vals:
                                score = SequenceMatcher(None, extracted.lower(), correct.lower()).ratio()
                                if score > 0.5 and score > best_score:  # Only consider reasonable matches
                                    best_match = correct
                                    best_score = score
                            
                            # If we found a reasonable match and they're not identical
                            if best_match and best_match.lower() != extracted.lower():
                                # Add to corrections
                                if best_match not in self.entity_corrections[entity_type][extracted]:
                                    self.entity_corrections[entity_type][extracted].append(best_match)
                                    logger.info(f"Learned entity correction: '{extracted}' -> '{best_match}' ({entity_type})")
                
                # Save learned data periodically
                if self.learning_events % self.save_interval == 0:
                    self._save_learned_data()
                    
                return True
                
            except Exception as e:
                logger.error(f"Error in learn_from_feedback: {str(e)}")
                return False
                
    def learn_from_session(self, messages: List[Dict], entities: List[Dict], 
                        user_id: Optional[str] = None) -> int:
        """
        Learn from a successful conversation session.
        
        Args:
            messages (List[Dict]): Messages from the session
            entities (List[Dict]): Entities extracted in each turn
            user_id (str, optional): User ID for tracking
            
        Returns:
            int: Number of learning events
        """
        with self.lock:
            try:
                learning_count = 0
                
                # Process each message-entity pair
                for i, (message_obj, entity_obj) in enumerate(zip(messages, entities)):
                    if i + 1 >= len(messages):
                        # Skip the last message if there's no following message
                        continue
                        
                    if not entity_obj.get("entities"):
                        # Skip if no entities were extracted
                        continue
                        
                    # Get the user message and extracted entities
                    message = message_obj.get("text", "")
                    extracted_entities = entity_obj.get("entities", {})
                    
                    # Check if entity was used successfully in conversation
                    next_message = messages[i + 1].get("text", "")
                    
                    # If next message is positive (not asking for clarification or correction)
                    if self._is_positive_response(next_message):
                        # Consider entities as correct
                        for entity_type, entities in extracted_entities.items():
                            for entity in entities:
                                # Create a key based on normalized message text
                                text_key = self._normalize_text(message)
                                
                                # Add to learned entities if not already present
                                if entity not in self.learned_entities[entity_type][text_key]:
                                    self.learned_entities[entity_type][text_key].append(entity)
                                    learning_count += 1
                    
                # Save learned data if we learned anything
                if learning_count > 0:
                    self.learning_events += learning_count
                    logger.info(f"Learned {learning_count} entities from successful session")
                    
                    if self.learning_events % self.save_interval == 0:
                        self._save_learned_data()
                
                return learning_count
                
            except Exception as e:
                logger.error(f"Error in learn_from_session: {str(e)}")
                return 0
                
    def enhance_entities(self, text: str, entities: Dict[str, List[str]], 
                     confidence: Dict[str, List[float]]) -> Tuple[Dict[str, List[str]], Dict[str, List[float]]]:
        """
        Enhance entity extraction using learned knowledge.
        
        Args:
            text (str): Input text
            entities (Dict): Initially extracted entities
            confidence (Dict): Confidence scores
            
        Returns:
            Tuple: Enhanced entities and confidence scores
        """
        with self.lock:
            try:
                # Create a copy of the input to avoid modifying the original
                enhanced_entities = {k: v.copy() for k, v in entities.items()}
                enhanced_confidence = {k: v.copy() for k, v in confidence.items()}
                
                # Normalize input text
                text_key = self._normalize_text(text)
                
                # Add learned entities
                for entity_type, examples_dict in self.learned_entities.items():
                    # Get examples for this text or similar texts
                    learned_examples = []
                    learned_confidence = []
                    
                    # Exact match
                    if text_key in examples_dict:
                        exact_examples = [e for e in examples_dict[text_key] if not e.startswith("NEG_")]
                        learned_examples.extend(exact_examples)
                        learned_confidence.extend([1.0] * len(exact_examples))
                    
                    # Fuzzy match
                    for stored_key, examples in examples_dict.items():
                        if stored_key != text_key:
                            similarity = SequenceMatcher(None, text_key, stored_key).ratio()
                            if similarity > 0.8:  # High similarity threshold
                                # Filter out negative examples
                                positive_examples = [e for e in examples if not e.startswith("NEG_")]
                                learned_examples.extend(positive_examples)
                                
                                # Confidence is proportional to text similarity
                                learned_confidence.extend([similarity] * len(positive_examples))
                    
                    # Add to entities if we have enough examples
                    if learned_examples and sum(1 for c in learned_confidence if c >= self.confidence_threshold) >= self.min_examples:
                        # Initialize entity type if needed
                        if entity_type not in enhanced_entities:
                            enhanced_entities[entity_type] = []
                            enhanced_confidence[entity_type] = []
                        
                        # Add each learned entity that's not already in the list
                        for i, entity in enumerate(learned_examples):
                            if i < len(learned_confidence) and learned_confidence[i] >= self.confidence_threshold:
                                if entity not in enhanced_entities[entity_type]:
                                    enhanced_entities[entity_type].append(entity)
                                    enhanced_confidence[entity_type].append(learned_confidence[i])
                
                # Remove incorrect entities (negative examples)
                for entity_type, examples_dict in self.learned_entities.items():
                    if entity_type in enhanced_entities:
                        # Skip if entity type not in results
                        if text_key in examples_dict:
                            # Get negative examples for this text
                            negative_examples = [e[4:] for e in examples_dict[text_key] if e.startswith("NEG_")]
                            
                            # Remove negative examples from results
                            indices_to_remove = []
                            for i, entity in enumerate(enhanced_entities[entity_type]):
                                if entity in negative_examples:
                                    indices_to_remove.append(i)
                            
                            # Remove from highest index to lowest
                            for idx in sorted(indices_to_remove, reverse=True):
                                if idx < len(enhanced_entities[entity_type]):
                                    enhanced_entities[entity_type].pop(idx)
                                    enhanced_confidence[entity_type].pop(idx)
                
                # Apply corrections
                for entity_type, corrections in self.entity_corrections.items():
                    if entity_type in enhanced_entities:
                        for i, entity in enumerate(enhanced_entities[entity_type]):
                            if entity in corrections:
                                # Get the most common correction
                                corrected_values = corrections[entity]
                                if corrected_values:
                                    corrected = corrected_values[0]  # Use the first/most recent correction
                                    
                                    # Replace with corrected value
                                    enhanced_entities[entity_type][i] = corrected
                                    # Slightly increase confidence for corrected entities
                                    if i < len(enhanced_confidence[entity_type]):
                                        enhanced_confidence[entity_type][i] = min(enhanced_confidence[entity_type][i] + 0.1, 1.0)
                
                return enhanced_entities, enhanced_confidence
                
            except Exception as e:
                logger.error(f"Error in enhance_entities: {str(e)}")
                return entities, confidence
                
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for matching purposes.
        
        Args:
            text (str): Text to normalize
            
        Returns:
            str: Normalized text
        """
        # Simple normalization: lowercase and remove extra whitespace
        normalized = text.lower().strip()
        normalized = ' '.join(normalized.split())
        
        # If text is too long, create a prefix key
        if len(normalized) > 100:
            normalized = normalized[:100]
            
        return normalized
        
    def _is_positive_response(self, message: str) -> bool:
        """
        Determine if a response indicates a successful entity extraction.
        
        Args:
            message (str): Message to analyze
            
        Returns:
            bool: True if response is positive
        """
        # Negative indicators (asking for clarification or correction)
        negative_indicators = [
            "what", "which", "where", "who", "when", "how", "?", 
            "didn't understand", "don't understand", 
            "what do you mean", "could you clarify",
            "not what i", "that's not", "that is not", 
            "incorrect", "wrong", "mistake", "error"
        ]
        
        # Check for negative indicators
        text = message.lower()
        for indicator in negative_indicators:
            if indicator in text:
                return False
                
        # If no negative indicators, assume positive
        return True
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the learning system.
        
        Returns:
            Dict: Statistics
        """
        stats = {
            "total_learning_events": self.learning_events,
            "entity_types": {},
            "corrections": {},
            "total_learned_entities": 0,
            "total_corrections": 0
        }
        
        # Count learned entities
        for entity_type, examples_dict in self.learned_entities.items():
            entity_count = 0
            negative_count = 0
            text_keys = 0
            
            for text_key, examples in examples_dict.items():
                text_keys += 1
                for example in examples:
                    if example.startswith("NEG_"):
                        negative_count += 1
                    else:
                        entity_count += 1
                        
            stats["entity_types"][entity_type] = {
                "count": entity_count,
                "negative_examples": negative_count,
                "text_patterns": text_keys
            }
            
            stats["total_learned_entities"] += entity_count
            
        # Count corrections
        for entity_type, corrections in self.entity_corrections.items():
            correction_count = sum(len(values) for values in corrections.values())
            stats["corrections"][entity_type] = correction_count
            stats["total_corrections"] += correction_count
            
        return stats
        
    def reset(self, entity_type: Optional[str] = None):
        """
        Reset learned data.
        
        Args:
            entity_type (str, optional): Entity type to reset, or None for all
        """
        with self.lock:
            if entity_type:
                # Reset specific entity type
                if entity_type in self.learned_entities:
                    self.learned_entities[entity_type] = defaultdict(list)
                    
                if entity_type in self.entity_corrections:
                    self.entity_corrections[entity_type] = defaultdict(list)
                    
                logger.info(f"Reset learned data for entity type: {entity_type}")
            else:
                # Reset all learned data
                self.learned_entities = defaultdict(lambda: defaultdict(list))
                self.entity_corrections = defaultdict(lambda: defaultdict(list))
                self.learning_events = 0
                
                logger.info("Reset all learned data")
                
            # Save empty data
            self._save_learned_data()
                
class FeedbackCollector:
    """
    Collects and processes user feedback for continuous learning.
    Handles implicit and explicit feedback collection.
    """
    
    def __init__(self, entity_learner, storage_path: str = "data/feedback"):
        """
        Initialize the feedback collector.
        
        Args:
            entity_learner: Entity learner component
            storage_path (str): Path to store feedback data
        """
        self.entity_learner = entity_learner
        self.storage_path = storage_path
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Feedback storage
        self.pending_feedback = {}
        self.processed_feedback = []
        
        # Load pending feedback if available
        self._load_pending_feedback()
        
    def _load_pending_feedback(self):
        """Load pending feedback from disk."""
        feedback_file = os.path.join(self.storage_path, "pending_feedback.json")
        
        try:
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    self.pending_feedback = json.load(f)
                    
                    logger.info(f"Loaded {len(self.pending_feedback)} pending feedback items")
        except Exception as e:
            logger.error(f"Error loading pending feedback: {str(e)}")
            
    def _save_pending_feedback(self):
        """Save pending feedback to disk."""
        feedback_file = os.path.join(self.storage_path, "pending_feedback.json")
        
        try:
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending_feedback, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved {len(self.pending_feedback)} pending feedback items")
        except Exception as e:
            logger.error(f"Error saving pending feedback: {str(e)}")
            
    def collect_explicit_feedback(self, message_id: str, user_message: str, 
                             extracted_entities: Dict[str, List[str]],
                             correct_entities: Dict[str, List[str]],
                             user_id: Optional[str] = None) -> bool:
        """
        Collect explicit feedback from users.
        
        Args:
            message_id (str): ID of the message
            user_message (str): Original user message
            extracted_entities (Dict): Entities extracted by the system
            correct_entities (Dict): Correct entities provided by user
            user_id (str, optional): User ID
            
        Returns:
            bool: Success flag
        """
        try:
            # Store feedback
            feedback_item = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id,
                "user_message": user_message,
                "extracted_entities": extracted_entities,
                "correct_entities": correct_entities,
                "user_id": user_id,
                "processed": False
            }
            
            # Add to pending feedback
            self.pending_feedback[message_id] = feedback_item
            
            # Save pending feedback
            self._save_pending_feedback()
            
            # Process immediately
            return self.process_feedback_item(message_id)
            
        except Exception as e:
            logger.error(f"Error collecting explicit feedback: {str(e)}")
            return False
            
    def collect_implicit_feedback(self, session_id: str, messages: List[Dict], 
                             entities: List[Dict], user_id: Optional[str] = None) -> bool:
        """
        Collect implicit feedback from conversation session.
        
        Args:
            session_id (str): Session ID
            messages (List[Dict]): Messages from the session
            entities (List[Dict]): Entities extracted in each turn
            user_id (str, optional): User ID
            
        Returns:
            bool: Success flag
        """
        try:
            # Learn from successful conversation
            learning_count = self.entity_learner.learn_from_session(messages, entities, user_id)
            
            logger.info(f"Collected implicit feedback from session {session_id}: {learning_count} learning events")
            
            return learning_count > 0
            
        except Exception as e:
            logger.error(f"Error collecting implicit feedback: {str(e)}")
            return False
            
    def process_feedback_item(self, message_id: str) -> bool:
        """
        Process a specific feedback item.
        
        Args:
            message_id (str): ID of the message with feedback
            
        Returns:
            bool: Success flag
        """
        try:
            # Get feedback item
            if message_id not in self.pending_feedback:
                logger.warning(f"Feedback item not found: {message_id}")
                return False
                
            feedback_item = self.pending_feedback[message_id]
            
            # Skip if already processed
            if feedback_item.get("processed", False):
                return True
                
            # Extract data
            user_message = feedback_item.get("user_message", "")
            extracted_entities = feedback_item.get("extracted_entities", {})
            correct_entities = feedback_item.get("correct_entities", {})
            user_id = feedback_item.get("user_id")
            
            # Learn from feedback
            success = self.entity_learner.learn_from_feedback(
                user_message, extracted_entities, correct_entities, user_id
            )
            
            if success:
                # Mark as processed
                feedback_item["processed"] = True
                self.pending_feedback[message_id] = feedback_item
                
                # Save pending feedback
                self._save_pending_feedback()
                
                # Move to processed list
                self.processed_feedback.append(feedback_item)
                
                # Limit processed list size
                if len(self.processed_feedback) > 1000:
                    self.processed_feedback = self.processed_feedback[-1000:]
                    
                logger.info(f"Processed feedback for message {message_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing feedback item: {str(e)}")
            return False
            
    def process_all_pending(self) -> int:
        """
        Process all pending feedback items.
        
        Returns:
            int: Number of successfully processed items
        """
        try:
            success_count = 0
            
            # Get IDs to avoid modification during iteration
            message_ids = list(self.pending_feedback.keys())
            
            for message_id in message_ids:
                if self.process_feedback_item(message_id):
                    success_count += 1
                    
            return success_count
            
        except Exception as e:
            logger.error(f"Error processing pending feedback: {str(e)}")
            return 0
            
    def clear_processed_feedback(self, days: int = 30) -> int:
        """
        Clear processed feedback older than specified days.
        
        Args:
            days (int): Age in days
            
        Returns:
            int: Number of cleared items
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            
            # Clear processed feedback
            original_count = len(self.processed_feedback)
            self.processed_feedback = [
                item for item in self.processed_feedback
                if item.get("timestamp", "") > cutoff_str
            ]
            
            cleared_count = original_count - len(self.processed_feedback)
            
            # Clear processed items from pending feedback
            message_ids = list(self.pending_feedback.keys())
            for message_id in message_ids:
                item = self.pending_feedback[message_id]
                if item.get("processed", False) and item.get("timestamp", "") <= cutoff_str:
                    del self.pending_feedback[message_id]
                    
            # Save pending feedback
            self._save_pending_feedback()
            
            logger.info(f"Cleared {cleared_count} processed feedback items")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing processed feedback: {str(e)}")
            return 0
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get feedback collection statistics.
        
        Returns:
            Dict: Statistics
        """
        try:
            stats = {
                "pending_count": len(self.pending_feedback),
                "processed_count": len(self.processed_feedback),
                "unprocessed_count": sum(1 for item in self.pending_feedback.values() 
                                    if not item.get("processed", False)),
                "entity_learner_stats": self.entity_learner.get_stats()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "error": str(e)
            } 
