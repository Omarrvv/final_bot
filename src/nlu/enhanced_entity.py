"""
Enhanced entity extraction for the Egypt Tourism Chatbot.
Provides improved entity recognition with confidence scoring and contextual awareness.
"""
import re
import logging
import spacy
import numpy as np
from typing import Dict, List, Any, Optional, Set, Tuple
from difflib import SequenceMatcher
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EnhancedEntityExtractor:
    """
    Enhanced entity extractor with fuzzy matching and contextual awareness.
    Extracts entities such as locations, attractions, dates, and more.
    """
    
    def __init__(self, language: str, config: Dict, nlp_model, knowledge_base, embedding_model=None):
        """
        Initialize entity extractor for a specific language.
        
        Args:
            language (str): Language code ('en' or 'ar')
            config (Dict): Configuration for entity extraction
            nlp_model: SpaCy language model
            knowledge_base: Knowledge base for entity resolution
            embedding_model: Model for creating text embeddings
        """
        self.language = language
        self.config = config
        self.nlp_model = nlp_model
        self.knowledge_base = knowledge_base
        self.embedding_model = embedding_model
        
        # Compile entity detection patterns
        self.patterns = self._compile_patterns()
        
        # Load entity lists from knowledge base
        self.entity_lists = self._load_entity_lists()
        
        # Entity type mapping
        self.entity_type_mapping = {
            "GPE": "location",
            "LOC": "location",
            "FAC": "attraction",
            "ORG": "attraction",
            "EVENT": "event",
            "PERSON": "person",
            "DATE": "date",
            "TIME": "time",
            "MONEY": "price",
            "CARDINAL": "number",
            "ORDINAL": "number"
        }
        
        # Pronouns for coreference resolution
        self.personal_pronouns = {
            'en': ['it', 'they', 'them', 'this', 'that', 'these', 'those', 
                   'there', 'here', 'the place', 'this place', 'that place',
                   'the attraction', 'the hotel', 'the restaurant'],
            'ar': ['هو', 'هي', 'هم', 'هن', 'هذا', 'هذه', 'ذلك', 'تلك', 'هؤلاء', 'أولئك',
                  'هناك', 'هنا', 'المكان', 'هذا المكان', 'ذلك المكان',
                  'المعلم', 'الفندق', 'المطعم']
        }
        
        # Entity relationship patterns
        self.entity_relationship_patterns = {
            'en': {
                'near': [
                    r'(?:near|close to|around|nearby|in the vicinity of|adjacent to)\s+(.+?)(?:\.|,|\s+and|\s+or|\s+but|\s+$)',
                    r'(.+?)\s+(?:near|close to|nearby|around|in the vicinity of|adjacent to)\s+(.+?)(?:\.|,|\s+and|\s+or|\s+but|\s+$)'
                ],
                'between': [
                    r'between\s+(.+?)\s+and\s+(.+?)(?:\.|,|\s+and|\s+or|\s+but|\s+$)'
                ],
                'part_of': [
                    r'(?:in|at|inside|within)\s+(.+?)(?:\.|,|\s+and|\s+or|\s+but|\s+$)'
                ]
            },
            'ar': {
                'near': [
                    r'(?:بالقرب من|قريب من|حول|بجوار|في محيط|متاخم ل)\s+(.+?)(?:\.|,|؛|\s+و|\s+أو|\s+لكن|\s+$)',
                    r'(.+?)\s+(?:بالقرب من|قريب من|حول|بجوار|في محيط|متاخم ل)\s+(.+?)(?:\.|,|؛|\s+و|\s+أو|\s+لكن|\s+$)'
                ],
                'between': [
                    r'بين\s+(.+?)\s+و\s+(.+?)(?:\.|,|؛|\s+و|\s+أو|\s+لكن|\s+$)'
                ],
                'part_of': [
                    r'(?:في|عند|داخل|ضمن)\s+(.+?)(?:\.|,|؛|\s+و|\s+أو|\s+لكن|\s+$)'
                ]
            }
        }
        
        # Performance tracking metrics
        self.metrics = {
            'total_extractions': 0,
            'successful_resolutions': 0,
            'coreference_resolutions': 0,
            'entity_relationships_detected': 0,
            'low_confidence_entities': 0,
            'entity_types_extracted': {}
        }
        
    def _compile_patterns(self) -> Dict[str, Dict]:
        """Compile regex patterns for entity extraction."""
        patterns = {}
        
        # Get patterns from config or use defaults
        entity_patterns = self.config.get("entity_patterns", {})
        
        # Get language-specific patterns
        lang_patterns = entity_patterns.get(self.language, {})
        
        # Compile patterns for each entity type
        for entity_type, pattern_list in lang_patterns.items():
            if entity_type not in patterns:
                patterns[entity_type] = {
                    "regex": [],
                    "confidence": []
                }
                
            # Compile regex patterns
            for pattern_obj in pattern_list:
                pattern = pattern_obj.get("pattern", "")
                confidence = pattern_obj.get("confidence", 0.8)
                
                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    patterns[entity_type]["regex"].append(compiled_pattern)
                    patterns[entity_type]["confidence"].append(confidence)
                except re.error as e:
                    logger.error(f"Error compiling pattern '{pattern}': {str(e)}")
                    
        return patterns
        
    def _load_entity_lists(self):
        """Load entity lists from knowledge base for fuzzy and semantic matching."""
        entity_lists = {
            "attraction": [],
            "location": [],
            "hotel": [],
            "restaurant": [],
            "cuisine": [],
            "facility": [],
            "category": [],
            "transportation": []
        }
        
        # Load attractions
        attractions = self.knowledge_base.search_attractions(limit=500, language=self.language)
        if attractions:  # Check if attractions is not None
            for attraction in attractions:
                if not attraction:  # Skip None or empty items
                    continue
                    
                # Safely get name with fallbacks
                name = None
                if isinstance(attraction.get("name"), dict):
                    name = attraction.get("name", {}).get(self.language) or attraction.get("name", {}).get("en")
                elif isinstance(attraction.get("name"), str):
                    name = attraction.get("name")
                    
                if name:
                    entity_lists["attraction"].append(name)
                
                # Safely get location with fallbacks
                location = None
                if isinstance(attraction.get("location"), dict):
                    location = attraction.get("location", {}).get(self.language) or attraction.get("location", {}).get("en")
                elif isinstance(attraction.get("location"), str):
                    location = attraction.get("location")
                    
                if location and location not in entity_lists["location"]:
                    entity_lists["location"].append(location)
                
                # Safely get category with fallbacks
                category = None
                if isinstance(attraction.get("category"), dict):
                    category = attraction.get("category", {}).get(self.language) or attraction.get("category", {}).get("en")
                elif isinstance(attraction.get("category"), str):
                    category = attraction.get("category")
                    
                if category and category not in entity_lists["category"]:
                    entity_lists["category"].append(category)
                
        # Load hotels
        hotels = self.knowledge_base.search_hotels(query={}, limit=300)
        if hotels:  # Check if hotels is not None
            for hotel in hotels:
                if not hotel:  # Skip None or empty items
                    continue
                    
                # Safely get name with fallbacks
                name = None
                if isinstance(hotel.get("name"), dict):
                    name = hotel.get("name", {}).get(self.language) or hotel.get("name", {}).get("en")
                elif isinstance(hotel.get("name"), str):
                    name = hotel.get("name")
                    
                if name:
                    entity_lists["hotel"].append(name)
                
                # Safely get location with fallbacks
                location = None
                if isinstance(hotel.get("location"), dict):
                    location = hotel.get("location", {}).get(self.language) or hotel.get("location", {}).get("en")
                elif isinstance(hotel.get("location"), str):
                    location = hotel.get("location")
                    
                if location and location not in entity_lists["location"]:
                    entity_lists["location"].append(location)
                
                # Safely get facilities with fallbacks
                facilities = []
                if isinstance(hotel.get("facilities"), list):
                    facilities = hotel.get("facilities", [])
                    
                for facility in facilities:
                    facility_name = None
                    if isinstance(facility, dict):
                        facility_name = facility.get(self.language) or facility.get('en')
                    elif facility:
                        facility_name = str(facility)
                        
                    if facility_name and facility_name not in entity_lists["facility"]:
                        entity_lists["facility"].append(facility_name)
                    
        # Load restaurants
        restaurants = self.knowledge_base.search_restaurants(query={}, limit=300)
        if restaurants:  # Check if restaurants is not None
            for restaurant in restaurants:
                if not restaurant:  # Skip None or empty items
                    continue
                    
                # Safely get name with fallbacks
                name = None
                if isinstance(restaurant.get("name"), dict):
                    name = restaurant.get("name", {}).get(self.language) or restaurant.get("name", {}).get("en")
                elif isinstance(restaurant.get("name"), str):
                    name = restaurant.get("name")
                    
                if name:
                    entity_lists["restaurant"].append(name)
                
                # Safely get location with fallbacks
                location = None
                if isinstance(restaurant.get("location"), dict):
                    location = restaurant.get("location", {}).get(self.language) or restaurant.get("location", {}).get("en")
                elif isinstance(restaurant.get("location"), str):
                    location = restaurant.get("location")
                    
                if location and location not in entity_lists["location"]:
                    entity_lists["location"].append(location)
                
                # Safely get cuisines with fallbacks
                cuisines = []
                if isinstance(restaurant.get("cuisine"), list):
                    cuisines = restaurant.get("cuisine", [])
                elif restaurant.get("cuisine"):
                    cuisines = [restaurant.get("cuisine")]
                    
                for cuisine in cuisines:
                    cuisine_name = None
                    if isinstance(cuisine, dict):
                        cuisine_name = cuisine.get(self.language) or cuisine.get('en')
                    elif cuisine:
                        cuisine_name = str(cuisine)
                        
                    if cuisine_name and cuisine_name not in entity_lists["cuisine"]:
                        entity_lists["cuisine"].append(cuisine_name)
                    
        return entity_lists

    def extract(self, text: str, intent: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract entities from text using multiple extraction methods.
        
        Args:
            text (str): Input text to extract entities from
            intent (str, optional): Intent for context-aware extraction
            context (Dict, optional): Conversation context
            
        Returns:
            Dict: Extracted entities with confidence scores
        """
        # Initialize result structures
        entities = {}
        confidence_scores = {}
        entity_relationships = {}
        
        # Process with spaCy
        doc = self.nlp_model(text)
        
        # Extract entities using different methods
        self._extract_spacy_entities(doc, entities, confidence_scores)
        self._extract_regex_entities(text, entities, confidence_scores)
        self._extract_fuzzy_entities(text, entities, confidence_scores)
        self._extract_semantic_entities(text, entities, confidence_scores, intent)
        
        # Extract entity relationships
        entity_relationships = self._extract_entity_relationships(text, entities)
        
        # Resolve coreferences
        if context:
            self._resolve_coreferences(text, entities, confidence_scores, context)
        
        # Resolve entities against knowledge base
        self._resolve_entities(entities, confidence_scores, intent, context)
        
        # Update metrics
        self._update_metrics(entities)
        
        # Prepare and return result
        result = {
            "entities": entities,
            "confidence": confidence_scores
        }
        
        # Add entity relationships if found
        if entity_relationships:
            result["relationships"] = entity_relationships
            
        return result
        
    def _extract_spacy_entities(self, doc, entities: Dict[str, List[str]], confidence: Dict[str, List[float]]):
        """Extract entities using spaCy NER."""
        for ent in doc.ents:
            entity_type = self._map_spacy_entity(ent.label_)
            
            if entity_type:
                # Add to entities list
                if entity_type not in entities:
                    entities[entity_type] = []
                    confidence[entity_type] = []
                    
                # Normalize entity value
                entity_value = ent.text.strip()
                
                # Only add if not already present
                if entity_value not in entities[entity_type]:
                    entities[entity_type].append(entity_value)
                    confidence[entity_type].append(0.8)  # Default confidence for spaCy entities
                    
    def _extract_regex_entities(self, text: str, entities: Dict[str, List[str]], confidence: Dict[str, List[float]]):
        """Extract entities using regular expressions."""
        for entity_type, pattern_data in self.patterns.items():
            # Skip if no patterns
            if not pattern_data["regex"]:
                continue
                
            # Initialize entity type if not present
            if entity_type not in entities:
                entities[entity_type] = []
                confidence[entity_type] = []
                
            # Check each pattern
            for i, pattern in enumerate(pattern_data["regex"]):
                pattern_confidence = pattern_data["confidence"][i]
                
                # Find all matches
                matches = pattern.findall(text)
                
                for match in matches:
                    if isinstance(match, tuple):
                        # If the pattern contains capturing groups
                        for group in match:
                            if group.strip():
                                self._add_entity(entities, confidence, entity_type, group.strip(), pattern_confidence)
                    elif match.strip():
                        # Single match
                        self._add_entity(entities, confidence, entity_type, match.strip(), pattern_confidence)
                        
    def _extract_fuzzy_entities(self, text: str, entities: Dict[str, List[str]], confidence: Dict[str, List[float]]):
        """Extract entities using fuzzy matching against known entities."""
        # Minimum similarity ratio
        min_ratio = 0.85
        
        # Check each entity list
        for entity_type, entity_list in self.entity_lists.items():
            # Skip if already processed or empty list
            if not entity_list:
                continue
                
            # Initialize entity type if not present
            if entity_type not in entities:
                entities[entity_type] = []
                confidence[entity_type] = []
                
            # Check each known entity
            for known_entity in entity_list:
                # Only consider entities with length > 3 to avoid false positives
                if len(known_entity) <= 3:
                    continue
                    
                # Calculate similarity ratio
                ratio = SequenceMatcher(None, text.lower(), known_entity.lower()).ratio()
                
                # Partial match for longer entities
                if len(known_entity) > 5:
                    # Try to find as substring
                    if known_entity.lower() in text.lower():
                        ratio = max(ratio, 0.95)  # High confidence for exact substring match
                        
                # If similar enough, add the entity
                if ratio >= min_ratio:
                    # Add with confidence proportional to match quality
                    self._add_entity(entities, confidence, entity_type, known_entity, ratio)
                    
    def _extract_semantic_entities(self, text: str, entities: Dict[str, List[str]], 
                               confidence: Dict[str, List[float]], intent: Optional[str] = None):
        """Extract entities using semantic similarity."""
        # Skip if no embedding model
        if not self.embedding_model:
            return
            
        # Get text embedding
        try:
            # Check if the embedding model is callable (function) or has an encode method
            if callable(self.embedding_model) and not hasattr(self.embedding_model, 'encode'):
                text_embedding = self.embedding_model([text])[0]
            else:
                text_embedding = self.embedding_model.encode([text])[0]
            
            # For each entity type, check semantic similarity to known entities
            for entity_type, entity_list in self.entity_lists.items():
                # Skip if already processed or empty list
                if not entity_list or len(entity_list) < 5:  # Only use for types with enough examples
                    continue
                    
                # Skip if not relevant to intent
                if intent and not self._is_relevant_to_intent(entity_type, intent):
                    continue
                    
                # Initialize entity type if not present
                if entity_type not in entities:
                    entities[entity_type] = []
                    confidence[entity_type] = []
                    
                # Encode known entities (could be optimized with caching)
                known_embeddings = []
                for entity in entity_list:
                    if callable(self.embedding_model) and not hasattr(self.embedding_model, 'encode'):
                        known_embeddings.append(self.embedding_model([entity])[0])
                    else:
                        known_embeddings.append(self.embedding_model.encode([entity])[0])
                    
                # Calculate similarity to each known entity
                similarities = cosine_similarity([text_embedding], known_embeddings)[0]
                
                # Find highly similar entities
                for i, similarity in enumerate(similarities):
                    if similarity > 0.8:  # High threshold for semantic matching
                        self._add_entity(entities, confidence, entity_type, entity_list[i], similarity)
                        
        except Exception as e:
            logger.error(f"Error in semantic entity extraction: {str(e)}")
            
    def _is_relevant_to_intent(self, entity_type: str, intent: str) -> bool:
        """Check if entity type is relevant to the given intent."""
        # Define relevant entity types for each intent
        relevance_map = {
            "attraction_info": ["attraction", "location", "date", "time"],
            "hotel_info": ["hotel", "location", "date", "time", "facility"],
            "restaurant_info": ["restaurant", "location", "cuisine", "date", "time"],
            "transportation": ["location", "transportation", "date", "time"],
            "practical_info": ["location"]
        }
        
        # Check if intent exists in map
        if intent in relevance_map:
            return entity_type in relevance_map[intent]
            
        # Default to true for unknown intents
        return True
        
    def _add_entity(self, entities: Dict[str, List[str]], confidence: Dict[str, List[float]], 
                entity_type: str, entity_value: str, score: float):
        """Add an entity if not already present or update with higher confidence."""
        # Initialize lists if needed
        if entity_type not in entities:
            entities[entity_type] = []
            confidence[entity_type] = []
            
        # Check if entity already exists
        if entity_value in entities[entity_type]:
            # Update confidence if higher
            idx = entities[entity_type].index(entity_value)
            if score > confidence[entity_type][idx]:
                confidence[entity_type][idx] = score
        else:
            # Add new entity
            entities[entity_type].append(entity_value)
            confidence[entity_type].append(score)
            
    def _map_spacy_entity(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity label to our entity types."""
        return self.entity_type_mapping.get(spacy_label)
        
    def _resolve_entities(self, entities: Dict[str, List[str]], confidence: Dict[str, List[float]],
                      intent: Optional[str], context: Optional[Dict]):
        """Resolve extracted entities against knowledge base."""
        # Intent-specific resolution
        if intent == "attraction_info":
            self._resolve_attraction_entities(entities, confidence, context)
        elif intent == "hotel_info":
            self._resolve_hotel_entities(entities, confidence, context)
        elif intent == "restaurant_info":
            self._resolve_restaurant_entities(entities, confidence, context)
            
        # Process all entity types to canonicalize and improve confidence
        self._canonicalize_entities(entities, confidence)
        
        # Remove low confidence entities (below 0.6)
        for entity_type in list(entities.keys()):
            indices_to_remove = []
            
            for i, conf in enumerate(confidence.get(entity_type, [])):
                if conf < 0.6:
                    indices_to_remove.append(i)
                    self.metrics['low_confidence_entities'] += 1
                    
            # Remove from highest index to lowest to avoid shifting
            for idx in sorted(indices_to_remove, reverse=True):
                if idx < len(entities[entity_type]):
                    entities[entity_type].pop(idx)
                    confidence[entity_type].pop(idx)
                    
    def _canonicalize_entities(self, entities: Dict[str, List[str]], confidence: Dict[str, List[float]]):
        """Canonicalize entity values to their standard forms."""
        for entity_type in list(entities.keys()):
            if entity_type in self.entity_lists:
                for i, entity_value in enumerate(entities[entity_type]):
                    # Find best match in knowledge base
                    best_match = None
                    best_score = 0
                    
                    for known_entity in self.entity_lists[entity_type]:
                        # Check exact match
                        if entity_value.lower() == known_entity.lower():
                            best_match = known_entity
                            best_score = 1.0
                            break
                            
                        # Check fuzzy match
                        score = SequenceMatcher(None, entity_value.lower(), known_entity.lower()).ratio()
                        if score > 0.85 and score > best_score:
                            best_match = known_entity
                            best_score = score
                            
                    # Update to canonical form if found
                    if best_match and best_match != entity_value:
                        entities[entity_type][i] = best_match
                        # Increase confidence slightly for canonical entities
                        confidence[entity_type][i] = min(confidence[entity_type][i] + 0.1, 1.0)
                        self.metrics['successful_resolutions'] += 1
                        
    def _resolve_attraction_entities(self, entities: Dict[str, List[str]], confidence: Dict[str, List[float]],
                             context: Optional[Dict]):
        """Resolve attraction entities against knowledge base."""
        # Check if we have attraction entities
        if "attraction" not in entities:
            return
            
        resolved_attractions = []
        resolved_confidences = []
        
        for i, attraction_name in enumerate(entities["attraction"]):
            # Get confidence score
            conf = confidence["attraction"][i]
            
            # Look up in knowledge base
            attraction = self.knowledge_base.lookup_attraction(attraction_name, self.language)
            
            if attraction:
                # Get canonical name from knowledge base
                canonical_name = attraction.get("name", {}).get(self.language, attraction_name)
                resolved_attractions.append(canonical_name)
                resolved_confidences.append(max(conf, 0.9))  # Boost confidence for verified attractions
                
                # Add location if available and not already present
                location = attraction.get("location", {}).get(self.language)
                if location:
                    if "location" not in entities:
                        entities["location"] = []
                        confidence["location"] = []
                        
                    if location not in entities["location"]:
                        entities["location"].append(location)
                        confidence["location"].append(0.9)
            else:
                # Keep unresolved attraction with original confidence
                resolved_attractions.append(attraction_name)
                resolved_confidences.append(conf)
                
        # Update with resolved attractions
        entities["attraction"] = resolved_attractions
        confidence["attraction"] = resolved_confidences
        
    def _resolve_hotel_entities(self, entities: Dict[str, List[str]], confidence: Dict[str, List[float]],
                        context: Optional[Dict]):
        """Resolve hotel entities against knowledge base."""
        # Check if we have hotel entities
        if "hotel" not in entities:
            return
            
        resolved_hotels = []
        resolved_confidences = []
        
        for i, hotel_name in enumerate(entities["hotel"]):
            # Get confidence score
            conf = confidence["hotel"][i]
            
            # Look up in knowledge base
            hotel = self.knowledge_base.lookup_hotel(hotel_name, self.language)
            
            if hotel:
                # Get canonical name from knowledge base
                canonical_name = hotel.get("name", {}).get(self.language, hotel_name)
                resolved_hotels.append(canonical_name)
                resolved_confidences.append(max(conf, 0.9))  # Boost confidence for verified hotels
                
                # Add location if available and not already present
                location = hotel.get("location", {}).get(self.language)
                if location:
                    if "location" not in entities:
                        entities["location"] = []
                        confidence["location"] = []
                        
                    if location not in entities["location"]:
                        entities["location"].append(location)
                        confidence["location"].append(0.9)
                        
                # Add facilities if available
                facilities = hotel.get("facilities", [])
                for facility in facilities:
                    if isinstance(facility, dict):
                        facility_name = facility.get(self.language, facility.get('en', str(facility)))
                    else:
                        facility_name = str(facility)
                    if facility_name:
                        if "facility" not in entities:
                            entities["facility"] = []
                            confidence["facility"] = []
                            
                        if facility_name not in entities["facility"]:
                            entities["facility"].append(facility_name)
                            confidence["facility"].append(0.85)
            else:
                # Keep unresolved hotel with original confidence
                resolved_hotels.append(hotel_name)
                resolved_confidences.append(conf)
                
        # Update with resolved hotels
        entities["hotel"] = resolved_hotels
        confidence["hotel"] = resolved_confidences
        
    def _resolve_restaurant_entities(self, entities: Dict[str, List[str]], confidence: Dict[str, List[float]],
                             context: Optional[Dict]):
        """Resolve restaurant entities against knowledge base."""
        # Check if we have restaurant entities
        if "restaurant" not in entities:
            return
            
        resolved_restaurants = []
        resolved_confidences = []
        
        for i, restaurant_name in enumerate(entities["restaurant"]):
            # Get confidence score
            conf = confidence["restaurant"][i]
            
            # Look up in knowledge base
            restaurant = self.knowledge_base.lookup_restaurant(restaurant_name, self.language)
            
            if restaurant:
                # Get canonical name from knowledge base
                canonical_name = restaurant.get("name", {}).get(self.language, restaurant_name)
                resolved_restaurants.append(canonical_name)
                resolved_confidences.append(max(conf, 0.9))  # Boost confidence for verified restaurants
                
                # Add location if available and not already present
                location = restaurant.get("location", {}).get(self.language)
                if location:
                    if "location" not in entities:
                        entities["location"] = []
                        confidence["location"] = []
                        
                    if location not in entities["location"]:
                        entities["location"].append(location)
                        confidence["location"].append(0.9)
                        
                # Add cuisines if available
                cuisines = restaurant.get("cuisine", [])
                for cuisine in cuisines:
                    if isinstance(cuisine, dict):
                        cuisine_name = cuisine.get(self.language, cuisine.get('en', str(cuisine)))
                    else:
                        cuisine_name = str(cuisine)
                    if cuisine_name:
                        if "cuisine" not in entities:
                            entities["cuisine"] = []
                            confidence["cuisine"] = []
                            
                        if cuisine_name not in entities["cuisine"]:
                            entities["cuisine"].append(cuisine_name)
                            confidence["cuisine"].append(0.85)
            else:
                # Keep unresolved restaurant with original confidence
                resolved_restaurants.append(restaurant_name)
                resolved_confidences.append(conf)
                
        # Update with resolved restaurants
        entities["restaurant"] = resolved_restaurants
        confidence["restaurant"] = resolved_confidences
    
    def _resolve_coreferences(self, text: str, entities: Dict[str, List[str]], 
                         confidence: Dict[str, List[float]], context: Dict):
        """
        Resolve coreferences using conversation context.
        
        Args:
            text (str): Current message text
            entities (Dict): Extracted entities
            confidence (Dict): Confidence scores
            context (Dict): Conversation context
        """
        # Get pronouns for current language
        pronouns = self.personal_pronouns.get(self.language, [])
        
        # Check for pronouns in text
        found_pronoun = False
        for pronoun in pronouns:
            # Simple pronoun matching pattern
            pattern = r'\b' + re.escape(pronoun) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_pronoun = True
                break
                
        if not found_pronoun:
            return
            
        # Get conversation history and active entities
        history = context.get('history', [])
        active_entities = context.get('active_entities', {})
        
        # No history or active entities to resolve against
        if not history or not active_entities:
            return
            
        # Check recently mentioned entities
        for entity_type in ["attraction", "hotel", "restaurant", "location"]:
            # If we don't have this entity type in current message but it exists in context
            if entity_type not in entities and entity_type in active_entities:
                recent_entities = active_entities[entity_type]
                
                if recent_entities:
                    # Add the most recently mentioned entity
                    latest_entity = recent_entities[0]
                    
                    if entity_type not in entities:
                        entities[entity_type] = []
                        confidence[entity_type] = []
                        
                    entities[entity_type].append(latest_entity)
                    # Slightly lower confidence for coreference resolution
                    confidence[entity_type].append(0.75)
                    
                    logger.debug(f"Resolved coreference: '{pronoun}' -> '{latest_entity}' ({entity_type})")
                    self.metrics['coreference_resolutions'] += 1

    def _extract_entity_relationships(self, text: str, entities: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """
        Extract relationships between entities.
        
        Args:
            text (str): Input text
            entities (Dict): Extracted entities
            
        Returns:
            Dict: Entity relationships by type
        """
        relationships = {}
        
        # Skip if no entities or no location entities (common in relationships)
        if not entities or "location" not in entities:
            return relationships
            
        # Get relationship patterns for current language
        rel_patterns = self.entity_relationship_patterns.get(self.language, {})
        
        # Process each relationship type
        for rel_type, patterns in rel_patterns.items():
            # Skip if no patterns
            if not patterns:
                continue
                
            # Prepare storage for this relationship type
            if rel_type not in relationships:
                relationships[rel_type] = []
                
            # Check each pattern
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if rel_type == "near" or rel_type == "part_of":
                        # Single entity relationship
                        if match.groups() and match.group(1).strip():
                            entity = match.group(1).strip()
                            # Check if mentioned entity is in our entity list
                            found = False
                            for e_type, e_list in entities.items():
                                if entity in e_list:
                                    # Add relationship
                                    relationships[rel_type].append({
                                        "entity": entity,
                                        "type": e_type
                                    })
                                    found = True
                                    break
                                    
                            # If not found in entity list, check using fuzzy matching
                            if not found:
                                for e_type, e_list in self.entity_lists.items():
                                    for known_entity in e_list:
                                        if SequenceMatcher(None, entity.lower(), known_entity.lower()).ratio() > 0.85:
                                            # Add relationship with canonical name
                                            relationships[rel_type].append({
                                                "entity": known_entity,
                                                "type": e_type
                                            })
                                            found = True
                                            break
                                    if found:
                                        break
                    elif rel_type == "between" and len(match.groups()) >= 2:
                        # Relationship between two entities
                        entity1 = match.group(1).strip()
                        entity2 = match.group(2).strip()
                        
                        if entity1 and entity2:
                            # Add relationship between the two entities
                            relationships[rel_type].append({
                                "entity1": entity1,
                                "entity2": entity2
                            })
                            
        # If relationships found, record metric
        if any(rels for rels in relationships.values()):
            self.metrics['entity_relationships_detected'] += 1
            
        return relationships

    def _update_metrics(self, entities: Dict[str, List[str]]):
        """Update performance metrics."""
        # Count total extractions
        total = sum(len(values) for values in entities.values())
        self.metrics['total_extractions'] += total
        
        # Count by type
        for entity_type, values in entities.items():
            if entity_type not in self.metrics['entity_types_extracted']:
                self.metrics['entity_types_extracted'][entity_type] = 0
                
            self.metrics['entity_types_extracted'][entity_type] += len(values)
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get entity extraction performance metrics."""
        # Calculate overall resolution rate
        resolution_rate = 0
        if self.metrics['total_extractions'] > 0:
            resolution_rate = self.metrics['successful_resolutions'] / self.metrics['total_extractions']
            
        # Prepare metrics object
        metrics_obj = {
            'total_extractions': self.metrics['total_extractions'],
            'successful_resolutions': self.metrics['successful_resolutions'],
            'resolution_rate': round(resolution_rate, 2),
            'coreference_resolutions': self.metrics['coreference_resolutions'],
            'entity_relationships_detected': self.metrics['entity_relationships_detected'],
            'low_confidence_entities': self.metrics['low_confidence_entities'],
            'entity_types_extracted': self.metrics['entity_types_extracted']
        }
        
        return metrics_obj
        
    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            'total_extractions': 0,
            'successful_resolutions': 0,
            'coreference_resolutions': 0,
            'entity_relationships_detected': 0,
            'low_confidence_entities': 0,
            'entity_types_extracted': {}
        } 