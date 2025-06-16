"""
Hierarchical Intent Classifier - Phase 1 Week 2 Enhancement
Implements hierarchical classification with disambiguation and context awareness
"""

import json
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from .intent_classifier import AdvancedIntentClassifier

logger = logging.getLogger(__name__)

class HierarchicalIntentClassifier(AdvancedIntentClassifier):
    """
    Enhanced intent classifier with hierarchical structure and disambiguation
    """
    
    def __init__(self, config: Dict, embedding_service, knowledge_base=None):
        super().__init__(config, embedding_service, knowledge_base)
        self.hierarchy_config = self._load_hierarchy_config()
        self.intent_hierarchy = self.hierarchy_config.get('intent_hierarchy', {})
        self.intent_relationships = self.hierarchy_config.get('intent_relationships', {})
        self.context_rules = self.hierarchy_config.get('context_rules', {})
        self.disambiguation_rules = self.hierarchy_config.get('disambiguation_rules', {})
        self.confidence_thresholds = self.hierarchy_config.get('confidence_thresholds', {})
        
        # Context tracking
        self.conversation_context = {}
        self.context_history = []
        
        logger.info(f"🏛️ Hierarchical Intent Classifier initialized")
        logger.info(f"   Hierarchy domains: {list(self.intent_hierarchy.keys())}")
        logger.info(f"   Disambiguation rules: {len(self.disambiguation_rules)}")
        logger.info(f"   Context rules: {len(self.context_rules)}")
    
    def _load_hierarchy_config(self) -> Dict:
        """Load hierarchical configuration"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            hierarchy_path = os.path.join(project_root, "configs", "intent_hierarchy.json")
            
            if os.path.exists(hierarchy_path):
                with open(hierarchy_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ Loaded hierarchical configuration from {hierarchy_path}")
                return config
            else:
                logger.warning(f"❌ Hierarchy config not found: {hierarchy_path}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error loading hierarchy config: {e}")
            return {}
    
    def classify(self, text: str, embedding=None, language=None, context=None) -> Dict[str, Any]:
        """
        Enhanced classification with hierarchical structure and disambiguation
        """
        # Get base classification from parent class
        base_result = super().classify(text, embedding, language, context)
        
        # Apply hierarchical enhancements
        enhanced_result = self._apply_hierarchical_classification(text, base_result, context)
        
        # Apply disambiguation if needed
        final_result = self._apply_disambiguation(text, enhanced_result)
        
        # Update context
        self._update_context(final_result, context)
        
        return final_result
    
    def _apply_hierarchical_classification(self, text: str, base_result: Dict, context: Optional[Dict]) -> Dict:
        """Apply hierarchical classification logic"""
        intent = base_result.get('intent')
        confidence = base_result.get('confidence', 0)
        top_intents = base_result.get('top_intents', [])
        
        # Get domain for the classified intent
        domain = self._get_intent_domain(intent)
        
        # Apply context boosts
        if context and 'conversation_history' in context:
            boosted_scores = self._apply_context_boosts(top_intents, context)
            if boosted_scores:
                # Re-rank based on boosted scores
                top_intent = max(boosted_scores, key=boosted_scores.get)
                if top_intent != intent:
                    logger.info(f"🔄 Context boost changed intent: {intent} → {top_intent}")
                    intent = top_intent
                    confidence = boosted_scores[top_intent]
        
        # Add hierarchical information
        enhanced_result = base_result.copy()
        enhanced_result.update({
            'intent': intent,
            'confidence': confidence,
            'domain': domain,
            'hierarchy_info': {
                'domain': domain,
                'domain_priority': self.intent_hierarchy.get(domain, {}).get('priority', 0),
                'context_sensitive': self.intent_hierarchy.get(domain, {}).get('context_sensitive', False)
            }
        })
        
        return enhanced_result
    
    def _apply_disambiguation(self, text: str, result: Dict) -> Dict:
        """Apply disambiguation rules for conflicting intents"""
        intent = result.get('intent')
        confidence = result.get('confidence', 0)
        top_intents = result.get('top_intents', [])

        logger.debug(f"🔍 Disambiguation check for: '{text}' → {intent}")
        logger.debug(f"   Top intents: {[(i.get('intent'), i.get('score', 0)) for i in top_intents[:3]]}")

        # Check if disambiguation is needed
        if len(top_intents) >= 2:
            top_score = top_intents[0].get('score', 0)
            second_score = top_intents[1].get('score', 0)
            similarity_difference = top_score - second_score
            
            # Find applicable disambiguation rule
            logger.debug(f"   Checking {len(self.disambiguation_rules)} disambiguation rules...")
            for rule_name, rule in self.disambiguation_rules.items():
                rule_applies = self._rule_applies(intent, top_intents[1].get('intent'), rule, similarity_difference)
                logger.debug(f"   Rule '{rule_name}': {rule_applies}")

                if rule_applies:
                    disambiguated_intent = self._apply_disambiguation_rule(text, rule, top_intents)

                    # CRITICAL FIX: Apply disambiguation even if intent doesn't change (for confirmation)
                    logger.info(f"🎯 Disambiguation applied ({rule_name}): {intent} → {disambiguated_intent}")
                    result['intent'] = disambiguated_intent
                    result['disambiguation_applied'] = rule_name
                    result['original_intent'] = intent

                    # Update confidence if intent changed
                    if disambiguated_intent != intent:
                        # Find the confidence for the new intent
                        for intent_info in top_intents:
                            if intent_info.get('intent') == disambiguated_intent:
                                result['confidence'] = intent_info.get('score', confidence)
                                break

                    break
            else:
                logger.debug(f"   No disambiguation rules applied")
        
        return result
    
    def _rule_applies(self, primary_intent: str, secondary_intent: str, rule: Dict, similarity_diff: float) -> bool:
        """Check if a disambiguation rule applies"""
        rule_primary = rule.get('primary_intent')
        rule_secondary = rule.get('secondary_intent')
        condition = rule.get('condition', '')
        
        # Check intent match
        intents_match = (
            (primary_intent == rule_primary and secondary_intent == rule_secondary) or
            (primary_intent == rule_secondary and secondary_intent == rule_primary)
        )
        
        # Check condition
        condition_met = True
        if 'similarity_difference <' in condition:
            threshold = float(condition.split('<')[1].strip())
            condition_met = similarity_diff < threshold
        
        return intents_match and condition_met
    
    def _apply_disambiguation_rule(self, text: str, rule: Dict, top_intents: List[Dict]) -> str:
        """Apply specific disambiguation rule"""
        resolution = rule.get('resolution', 'keyword_based')
        
        if resolution == 'keyword_based':
            return self._keyword_based_disambiguation(text, rule)
        
        # Default: return original intent
        return top_intents[0].get('intent', 'general_query')
    
    def _keyword_based_disambiguation(self, text: str, rule: Dict) -> str:
        """Perform keyword-based disambiguation"""
        keywords = rule.get('keywords', {})
        text_lower = text.lower()
        
        scores = {}
        for intent_type, intent_keywords in keywords.items():
            score = sum(1 for keyword in intent_keywords if keyword.lower() in text_lower)
            if score > 0:
                scores[intent_type] = score
        
        if scores:
            # Get the intent type with highest keyword score
            best_type = max(scores, key=scores.get)
            
            # Map back to actual intent
            if best_type.endswith('_indicators'):
                intent_name = best_type.replace('_indicators', '')
                if intent_name == 'hotel':
                    return 'hotel_query'
                elif intent_name == 'restaurant':
                    return 'restaurant_query'
                elif intent_name == 'tour':
                    return 'tour_query'
                elif intent_name == 'booking':
                    return 'booking_query'
                elif intent_name == 'location':
                    return 'location_query'
                elif intent_name == 'event':
                    return 'event_query'
                elif intent_name == 'practical':
                    return 'practical_info'
                elif intent_name == 'faq':
                    return 'faq_query'
        
        # Default to primary intent from rule
        return rule.get('primary_intent', 'general_query')
    
    def _get_intent_domain(self, intent: str) -> str:
        """Get the domain for a given intent"""
        for domain, config in self.intent_hierarchy.items():
            if intent in config.get('intents', []):
                return domain
        return 'unknown'
    
    def _apply_context_boosts(self, top_intents: List[Dict], context: Dict) -> Dict[str, float]:
        """Apply context-based score boosts"""
        boosted_scores = {}
        
        # Get current context state
        current_context = self.conversation_context.get('active_context')
        
        if current_context and current_context in self.context_rules:
            context_rule = self.context_rules[current_context]
            boosts = context_rule.get('boosts', {})
            
            # Apply boosts to top intents
            for intent_info in top_intents:
                intent = intent_info.get('intent')
                base_score = intent_info.get('score', 0)
                boost = boosts.get(intent, 0)
                boosted_scores[intent] = base_score + boost
        else:
            # No context boosts, use original scores
            for intent_info in top_intents:
                intent = intent_info.get('intent')
                score = intent_info.get('score', 0)
                boosted_scores[intent] = score
        
        return boosted_scores
    
    def _update_context(self, result: Dict, context: Optional[Dict]):
        """Update conversation context based on classification result"""
        intent = result.get('intent')
        
        # Check if this intent triggers a new context
        for context_name, context_rule in self.context_rules.items():
            if intent in context_rule.get('triggers', []):
                self.conversation_context['active_context'] = context_name
                self.conversation_context['context_turns'] = 0
                self.conversation_context['max_duration'] = context_rule.get('duration', 3)
                logger.debug(f"🔄 Context activated: {context_name}")
                break
        
        # Update context turn counter
        if 'active_context' in self.conversation_context:
            self.conversation_context['context_turns'] += 1
            
            # Check if context should expire
            if self.conversation_context['context_turns'] >= self.conversation_context.get('max_duration', 3):
                logger.debug(f"🔄 Context expired: {self.conversation_context['active_context']}")
                self.conversation_context.clear()
        
        # Add to context history
        self.context_history.append({
            'intent': intent,
            'confidence': result.get('confidence', 0),
            'domain': result.get('domain', 'unknown')
        })
        
        # Keep only recent history
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
    
    def get_context_info(self) -> Dict:
        """Get current context information"""
        return {
            'active_context': self.conversation_context.get('active_context'),
            'context_turns': self.conversation_context.get('context_turns', 0),
            'recent_history': self.context_history[-3:] if self.context_history else []
        }
    
    def reset_context(self):
        """Reset conversation context"""
        self.conversation_context.clear()
        self.context_history.clear()
        logger.info("🔄 Conversation context reset")
