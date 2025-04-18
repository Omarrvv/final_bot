# src/nlu/entity.py
"""
Entity extraction module for the Egypt Tourism Chatbot.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Extracts entities (locations, attractions, dates, etc.) from user messages.
    Handles specialized extraction for Egyptian tourism entities.
    """
    
    def __init__(self, language: str, config: Dict, nlp_model, knowledge_base):
        """
        Initialize entity extractor for specific language.
        
        Args:
            language (str): Language code (e.g., 'en', 'ar')
            config (dict): Entity extraction configuration
            nlp_model: SpaCy model for NER
            knowledge_base: Reference to knowledge base for entity lookup
        """
        self.language = language
        self.config = config
        self.nlp_model = nlp_model
        self.knowledge_base = knowledge_base
        
        # Initialize regex patterns for entity extraction
        self.patterns = self._compile_patterns()
        
        logger.info(f"Entity extractor initialized for language: {language}")
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for entity extraction."""
        patterns = {}
        
        # Location patterns (cities, regions)
        patterns["location"] = [
            # --- Temporarily simplify for testing --- 
            # # English location patterns - Added word boundaries \b
            # re.compile(r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
            # re.compile(r'\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
            # re.compile(r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
            # re.compile(r'\bnear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
            # re.compile(r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
            # Add pattern for just the location name (like 'Cairo', 'Luxor')
            re.compile(r'\b(Cairo|Luxor|Aswan|Giza|Alexandria|Sharm\s+el\s+Sheikh)\b', re.IGNORECASE),
            # # Arabic location patterns (if language is Arabic) - Added word boundaries
            # re.compile(r'\bفي\s+(\S+(?:\s+\S+)*)\b', re.UNICODE),
            # re.compile(r'\bإلى\s+(\S+(?:\s+\S+)*)\b', re.UNICODE),
            # re.compile(r'\bمن\s+(\S+(?:\s+\S+)*)\b', re.UNICODE),
            # re.compile(r'\bبالقرب\s+من\s+(\S+(?:\s+\S+)*)\b', re.UNICODE),
            re.compile(r'\b(القاهرة|الأقصر|أسوان|الجيزة|الاسكندرية|شرم\s+الشيخ)\b', re.UNICODE)
        ]
        
        # Attraction patterns
        patterns["attraction"] = [
            # Monument types with proper names
            re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(pyramid|temple|museum|tomb|mosque|church|palace|garden|park)', re.IGNORECASE),
            re.compile(r'(pyramid|temple|museum|tomb|mosque|church|palace|garden|park)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
            re.compile(r'the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
            # Arabic attraction patterns
            re.compile(r'(معبد|هرم|متحف|مقبرة|مسجد|كنيسة|قصر|حديقة)\s+(\S+(?:\s+\S+)*)', re.UNICODE),
            re.compile(r'(\S+(?:\s+\S+)*)\s+(معبد|هرم|متحف|مقبرة|مسجد|كنيسة|قصر|حديقة)', re.UNICODE)
        ]
        
        # Date and time patterns
        patterns["datetime"] = [
            # Date formats
            re.compile(r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', re.IGNORECASE),
            re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?', re.IGNORECASE),
            re.compile(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})'),
            # Time formats
            re.compile(r'(\d{1,2}):(\d{2})\s*(am|pm)?', re.IGNORECASE),
            re.compile(r'(\d{1,2})\s*(am|pm)', re.IGNORECASE),
            # Duration
            re.compile(r'(\d+)\s+(day|days|hour|hours|week|weeks)', re.IGNORECASE),
            # Arabic date/time patterns
            re.compile(r'(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)', re.UNICODE),
            re.compile(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})'),
            re.compile(r'(\d{1,2}):(\d{2})\s*(صباحا|مساء)?', re.UNICODE),
            re.compile(r'(\d+)\s+(يوم|أيام|ساعة|ساعات|أسبوع|أسابيع)', re.UNICODE)
        ]
        
        # Price and budget patterns
        patterns["budget"] = [
            re.compile(r'(\d+)\s*(dollar|dollars|USD|\$|£|pound|pounds|EGP)', re.IGNORECASE),
            re.compile(r'(\$|£)(\d+)'),
            re.compile(r'(cheap|affordable|budget|expensive|luxury|high-end)', re.IGNORECASE),
            re.compile(r'(\$|\$\$|\$\$\$|\$\$\$\$|\$\$\$\$\$)'),
            # Arabic price patterns
            re.compile(r'(\d+)\s*(دولار|دولارات|جنيه|جنيهات)', re.UNICODE),
            re.compile(r'(رخيص|ميسور|اقتصادي|غالي|فاخر|راقي)', re.UNICODE)
        ]
        
        # Specific Egypt tourism entity patterns
        patterns["egypt_specific"] = [
            # Nile cruises
            re.compile(r'(nile\s+cruise|nile\s+cruises|felucca|dahabiya)', re.IGNORECASE),
            re.compile(r'(رحلة|رحلات)\s+(النيل|نيلية)', re.UNICODE),
            # Desert safaris
            re.compile(r'(desert\s+safari|desert\s+trip|oasis\s+tour)', re.IGNORECASE),
            re.compile(r'(رحلة|رحلات)\s+(صحراوية|الواحات)', re.UNICODE),
            # Dive sites
            re.compile(r'(diving|dive\s+site|snorkeling|red\s+sea)', re.IGNORECASE),
            re.compile(r'(غوص|غطس|شعاب|البحر\s+الأحمر)', re.UNICODE)
        ]
        
        return patterns
    
    def extract(self, text: str, intent: Optional[str] = None, 
                context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract entities from user message.
        
        Args:
            text (str): User message text
            intent (str, optional): Detected intent for context-specific extraction
            context (dict, optional): Current conversation context
            
        Returns:
            dict: Extracted entities organized by type
        """
        # Default empty context if none provided
        if context is None:
            context = {}
        
        # Initialize results
        entities = {}
        confidence_scores = {}
        
        # Apply regex patterns first
        for entity_type, patterns in self.patterns.items():
            entities[entity_type] = []
            confidence_scores[entity_type] = []
            
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    for match in matches:
                        entity_value = None
                        # If findall returns tuples (multiple groups), take the first non-empty group.
                        if isinstance(match, tuple):
                            # Find the first non-empty group, assuming it's the main entity
                            for group in match:
                                if group: # Check if group is not empty
                                    entity_value = group.strip()
                                    break 
                        # If findall returns strings (single group or no groups), use the string.
                        elif isinstance(match, str):
                            entity_value = match.strip()
                        
                        if entity_value and entity_value not in entities[entity_type]:
                            entities[entity_type].append(entity_value)
                            # Pattern matches get medium-high confidence
                            confidence_scores[entity_type].append(0.8)
        
        # Apply NLP model if available
        if self.nlp_model:
            try:
                doc = self.nlp_model(text)
                
                # Extract named entities
                for ent in doc.ents:
                    entity_type = self._map_spacy_entity(ent.label_)
                    if entity_type:
                        entity_value = ent.text.strip()
                        
                        # Add to entities if not already present
                        if entity_type not in entities:
                            entities[entity_type] = []
                            confidence_scores[entity_type] = []
                        
                        if entity_value and entity_value not in entities[entity_type]:
                            entities[entity_type].append(entity_value)
                            # SpaCy entities get medium confidence
                            confidence_scores[entity_type].append(0.7)
            except Exception as e:
                logger.error(f"Error in NLP entity extraction: {str(e)}")
        
        # Apply knowledge base for entity resolution
        self._resolve_entities(entities, confidence_scores, intent, context)
        
        # Format the results
        result = {"entities": {}}
        for entity_type, values in entities.items():
            if values:  # Only include non-empty entity types
                result["entities"][entity_type] = []
                
                # Pair each entity with its confidence score
                for i, value in enumerate(values):
                    score = confidence_scores[entity_type][i] if i < len(confidence_scores[entity_type]) else 0.5
                    result["entities"][entity_type].append({
                        "value": value,
                        "confidence": score
                    })
        
        return result
    
    def _map_spacy_entity(self, spacy_label: str) -> Optional[str]:
        """Map SpaCy entity labels to our entity types."""
        mapping = {
            "GPE": "location",
            "LOC": "location",
            "FAC": "attraction",
            "ORG": "attraction",
            "PERSON": "person",
            "DATE": "datetime",
            "TIME": "datetime",
            "MONEY": "budget",
            "CARDINAL": None,  # Ignore cardinal numbers by default
            "ORDINAL": None    # Ignore ordinal numbers by default
        }
        
        return mapping.get(spacy_label)
    
    def _resolve_entities(self, entities: Dict[str, List[str]], 
                          confidence_scores: Dict[str, List[float]],
                          intent: Optional[str], context: Optional[Dict]) -> None:
        """
        Resolve and validate entities against the knowledge base.
        
        Args:
            entities: Dictionary of extracted entities
            confidence_scores: Confidence scores for entities
            intent: Detected intent for context-specific resolution
            context: Conversation context
        """
        # Resolve locations
        if "location" in entities and entities["location"]:
            resolved_locations = []
            resolved_scores = []
            
            for i, location in enumerate(entities["location"]):
                score = confidence_scores["location"][i] if i < len(confidence_scores["location"]) else 0.5
                
                # Lookup in knowledge base
                kb_results = self.knowledge_base.lookup_location(location, self.language)
                
                if kb_results:
                    # Use canonical name from knowledge base
                    resolved_locations.append(kb_results["canonical_name"])
                    # Increase confidence for validated entities
                    resolved_scores.append(min(score + 0.2, 1.0))
                else:
                    # Keep original if not found
                    resolved_locations.append(location)
                    resolved_scores.append(score)
            
            entities["location"] = resolved_locations
            confidence_scores["location"] = resolved_scores
        
        # Resolve attractions
        if "attraction" in entities and entities["attraction"]:
            resolved_attractions = []
            resolved_scores = []
            
            for i, attraction in enumerate(entities["attraction"]):
                score = confidence_scores["attraction"][i] if i < len(confidence_scores["attraction"]) else 0.5
                
                # Lookup in knowledge base with location context if available
                location_context = None
                if "location" in entities and entities["location"]:
                    location_context = entities["location"][0]
                
                kb_results = self.knowledge_base.lookup_attraction(
                    attraction, self.language, location_context
                )
                
                if kb_results:
                    # Use canonical name from knowledge base
                    resolved_attractions.append(kb_results["canonical_name"])
                    # Increase confidence for validated entities
                    resolved_scores.append(min(score + 0.2, 1.0))
                else:
                    # Keep original if not found
                    resolved_attractions.append(attraction)
                    resolved_scores.append(score)
            
            entities["attraction"] = resolved_attractions
            confidence_scores["attraction"] = resolved_scores
        
        # Handle intent-specific entity resolution
        if intent == "restaurant_query":
            self._resolve_restaurant_entities(entities, confidence_scores, context)
        elif intent == "hotel_query":
            self._resolve_hotel_entities(entities, confidence_scores, context)
    
    def _resolve_restaurant_entities(self, entities: Dict[str, List[str]], 
                                     confidence_scores: Dict[str, List[float]],
                                     context: Optional[Dict]) -> None:
        """Resolve entities specifically for restaurant queries."""
        # Extract cuisine type from text or context
        if "cuisine_type" not in entities and context and "text" in context:
            # Common cuisine types in Egypt
            cuisine_types = [
                "egyptian", "middle eastern", "mediterranean", "seafood", 
                "international", "italian", "asian", "fast food",
                "مصري", "شرق أوسطي", "متوسطي", "مأكولات بحرية", 
                "عالمي", "إيطالي", "آسيوي", "وجبات سريعة"
            ]
            
            text = context["text"].lower()
            for cuisine in cuisine_types:
                if cuisine.lower() in text:
                    if "cuisine_type" not in entities:
                        entities["cuisine_type"] = []
                        confidence_scores["cuisine_type"] = []
                    
                    entities["cuisine_type"].append(cuisine)
                    confidence_scores["cuisine_type"].append(0.7)
    
    def _resolve_hotel_entities(self, entities: Dict[str, List[str]], 
                                confidence_scores: Dict[str, List[float]],
                                context: Optional[Dict]) -> None:
        """Resolve entities specifically for hotel queries."""
        # Extract hotel type from text or context
        if "hotel_type" not in entities and context and "text" in context:
            # Common hotel types
            hotel_types = [
                "luxury", "budget", "mid-range", "resort", "boutique",
                "5-star", "4-star", "3-star", "hostel", "apartment",
                "فاخر", "اقتصادي", "متوسط", "منتجع", "بوتيك",
                "5 نجوم", "4 نجوم", "3 نجوم", "نزل", "شقة"
            ]
            
            text = context["text"].lower()
            for hotel_type in hotel_types:
                if hotel_type.lower() in text:
                    if "hotel_type" not in entities:
                        entities["hotel_type"] = []
                        confidence_scores["hotel_type"] = []
                    
                    entities["hotel_type"].append(hotel_type)
                    confidence_scores["hotel_type"].append(0.7)