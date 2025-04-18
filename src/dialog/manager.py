# src/dialog/manager.py
"""
Dialog management module for the Egypt Tourism Chatbot.
Manages conversation flow and determines appropriate responses.
"""
import json
import logging
import os
from typing import Dict, List, Any, Optional
import random
from pathlib import Path

logger = logging.getLogger(__name__)

class DialogManager:
    """
    Dialog manager that handles conversation flow and state transitions.
    Determines appropriate responses based on user intents and context.
    """
    
    def __init__(self, flows_config: str, knowledge_base):
        """
        Initialize the dialog manager with dialog flows configuration.
        
        Args:
            flows_config (str): Path to dialog flows configuration file
            knowledge_base: Reference to the knowledge base
        """
        self.flows_config = flows_config
        self.knowledge_base = knowledge_base
        
        # Load dialog flows
        self.flows = self._load_flows(flows_config)
        
        # Default responses for fallback
        self.default_responses = {
            "greeting": {
                "en": [
                    "Hello! I'm your Egyptian tourism assistant. How can I help you explore Egypt today?",
                    "Welcome! I'm here to help you discover the wonders of Egypt. What would you like to know?",
                    "Greetings! I'm your guide to Egypt's treasures. How may I assist you?"
                ],
                "ar": [
                    "مرحبًا! أنا مساعدك السياحي المصري. كيف يمكنني مساعدتك في استكشاف مصر اليوم؟",
                    "أهلاً! أنا هنا لمساعدتك في اكتشاف عجائب مصر. ما الذي تود معرفته؟",
                    "تحياتي! أنا دليلك إلى كنوز مصر. كيف يمكنني مساعدتك؟"
                ]
            },
            "farewell": {
                "en": [
                    "Goodbye! Feel free to return whenever you have more questions about Egypt.",
                    "Farewell! I hope I've been helpful in planning your Egyptian adventure.",
                    "Until next time! Enjoy exploring the wonders of Egypt."
                ],
                "ar": [
                    "وداعًا! لا تتردد في العودة عندما يكون لديك المزيد من الأسئلة حول مصر.",
                    "مع السلامة! آمل أن أكون قد ساعدتك في التخطيط لمغامرتك المصرية.",
                    "إلى اللقاء! استمتع باستكشاف عجائب مصر."
                ]
            },
            "fallback": {
                "en": [
                    "I'm not sure I understand. Could you rephrase your question?",
                    "I don't have information about that. Is there something else about Egypt you'd like to know?",
                    "I'm still learning and don't have an answer for that yet. Can I help you with something else related to Egyptian tourism?"
                ],
                "ar": [
                    "لست متأكدًا من أنني أفهم. هل يمكنك إعادة صياغة سؤالك؟",
                    "ليس لدي معلومات حول ذلك. هل هناك شيء آخر عن مصر تود معرفته؟",
                    "ما زلت أتعلم وليس لدي إجابة على ذلك بعد. هل يمكنني مساعدتك في شيء آخر متعلق بالسياحة المصرية؟"
                ]
            }
        }
        
        logger.info("Dialog manager initialized successfully")
    
    def _load_flows(self, config_path: str) -> Dict:
        """Load dialog flows from configuration file."""
        try:
            # Check if file exists
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Create default flows if file doesn't exist
                default_flows = self._create_default_flows()
                
                # Save default flows to file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_flows, f, indent=2, ensure_ascii=False)
                
                return default_flows
        except Exception as e:
            logger.error(f"Failed to load dialog flows: {str(e)}")
            return self._create_default_flows()
    
    def _create_default_flows(self) -> Dict:
        """Create default dialog flows."""
        return {
            "greeting": {
                "initial_response": "greeting",
                "suggestions": ["attractions", "hotels", "restaurants", "practical_info"],
                "next_states": {
                    "*": "information_gathering"
                }
            },
            "information_gathering": {
                "requires_entities": [],
                "prompts": {
                    "location": {
                        "en": "Which part of Egypt are you interested in?",
                        "ar": "أي جزء من مصر تهتم به؟"
                    },
                    "duration": {
                        "en": "How long are you planning to stay?",
                        "ar": "كم من الوقت تخطط للبقاء؟"
                    },
                    "interests": {
                        "en": "What are you most interested in? (history, beaches, culture, adventure)",
                        "ar": "بماذا أنت مهتم أكثر؟ (التاريخ، الشواطئ، الثقافة، المغامرة)"
                    }
                },
                "next_states": {
                    "attraction_info": "attraction_details",
                    "restaurant_query": "restaurant_details",
                    "hotel_query": "hotel_details",
                    "practical_info": "provide_practical_info",
                    "transportation": "transportation_info",
                    "*": "information_gathering"
                }
            },
            "attraction_details": {
                "requires_entities": ["attraction"],
                "entity_missing_prompts": {
                    "attraction": {
                        "en": "Which attraction would you like to know about?",
                        "ar": "ما هو المعلم السياحي الذي ترغب في معرفة المزيد عنه؟"
                    }
                },
                "response": "attraction_details",
                "suggestions": ["practical_info", "nearby_attractions", "ticket_info"],
                "next_states": {
                    "practical_info": "attraction_practical_info",
                    "nearby_attractions": "nearby_attractions",
                    "ticket_info": "attraction_ticket_info",
                    "*": "information_gathering"
                }
            },
            "restaurant_details": {
                "requires_entities": ["location"],
                "entity_missing_prompts": {
                    "location": {
                        "en": "In which area are you looking for restaurants?",
                        "ar": "في أي منطقة تبحث عن مطاعم؟"
                    }
                },
                "response": "restaurant_list",
                "suggestions": ["cuisine_types", "price_range", "top_rated"],
                "next_states": {
                    "restaurant_specific": "specific_restaurant",
                    "*": "information_gathering"
                }
            },
            "hotel_details": {
                "requires_entities": ["location"],
                "entity_missing_prompts": {
                    "location": {
                        "en": "In which area are you looking for accommodation?",
                        "ar": "في أي منطقة تبحث عن الإقامة؟"
                    }
                },
                "response": "hotel_list",
                "suggestions": ["price_range", "amenities", "top_rated"],
                "next_states": {
                    "hotel_specific": "specific_hotel",
                    "*": "information_gathering"
                }
            },
            "provide_practical_info": {
                "requires_entities": ["info_type"],
                "entity_missing_prompts": {
                    "info_type": {
                        "en": "What kind of practical information do you need? (visa, weather, transportation, safety)",
                        "ar": "ما نوع المعلومات العملية التي تحتاجها؟ (تأشيرة، طقس، مواصلات، أمان)"
                    }
                },
                "response": "practical_info",
                "suggestions": ["visa", "weather", "transportation", "safety"],
                "next_states": {
                    "*": "information_gathering"
                }
            },
            "transportation_info": {
                "requires_entities": ["transport_type"],
                "entity_missing_prompts": {
                    "transport_type": {
                        "en": "What type of transportation are you interested in? (flights, trains, buses, local)",
                        "ar": "ما نوع وسائل النقل التي تهتم بها؟ (رحلات جوية، قطارات، حافلات، محلي)"
                    }
                },
                "response": "transportation_info",
                "suggestions": ["flights", "trains", "buses", "local_transport"],
                "next_states": {
                    "*": "information_gathering"
                }
            },
            "specific_restaurant": {
                "requires_entities": ["restaurant"],
                "entity_missing_prompts": {
                    "restaurant": {
                        "en": "Which restaurant would you like to know more about?",
                        "ar": "ما هو المطعم الذي ترغب في معرفة المزيد عنه؟"
                    }
                },
                "response": "restaurant_details",
                "suggestions": ["menu", "location", "opening_hours"],
                "next_states": {
                    "*": "information_gathering"
                }
            },
            "specific_hotel": {
                "requires_entities": ["hotel"],
                "entity_missing_prompts": {
                    "hotel": {
                        "en": "Which hotel would you like to know more about?",
                        "ar": "ما هو الفندق الذي ترغب في معرفة المزيد عنه؟"
                    }
                },
                "response": "hotel_details",
                "suggestions": ["room_types", "amenities", "location"],
                "next_states": {
                    "*": "information_gathering"
                }
            },
            "itinerary_planning": {
                "requires_entities": ["duration", "location"],
                "entity_missing_prompts": {
                    "duration": {
                        "en": "How many days will you be staying?",
                        "ar": "كم يوم ستبقى؟"
                    },
                    "location": {
                        "en": "Which areas of Egypt are you planning to visit?",
                        "ar": "ما هي مناطق مصر التي تخطط لزيارتها؟"
                    }
                },
                "response": "suggested_itinerary",
                "service_calls": [
                    {
                        "service": "itinerary",
                        "method": "generate",
                        "include_context": ["duration", "location", "interests"]
                    }
                ],
                "suggestions": ["modify_itinerary", "attraction_details", "transportation_info"],
                "next_states": {
                    "modify_itinerary": "modify_itinerary",
                    "*": "information_gathering"
                }
            }
        }
    
    def next_action(self, nlu_result: Dict, context: Dict) -> Dict:
        """
        Determine the next dialog action based on NLU result and context.
        
        Args:
            nlu_result (dict): NLU processing result
            context (dict): Current conversation context
            
        Returns:
            dict: Next dialog action
        """
        # Extract intent and entities
        intent = nlu_result.get("intent", "")
        entities = nlu_result.get("entities", {})
        language = nlu_result.get("language", "en")
        confidence = nlu_result.get("intent_confidence", 0.0)
        
        # Get current dialog state
        current_state = context.get("dialog_state", "greeting")
        
        # Handle greetings and farewells directly
        if intent == "greeting" and confidence > 0.7:
            return self._create_greeting_action(language)
        
        if intent == "farewell" and confidence > 0.7:
            return self._create_farewell_action(language)
        
        # Get flow for current state
        flow = self.flows.get(current_state, {})
        if not flow:
            logger.warning(f"No flow defined for state: {current_state}")
            return self._create_fallback_action(language)
        
        # Check if all required entities are present
        required_entities = flow.get("requires_entities", [])
        missing_entities = [entity for entity in required_entities 
                          if entity not in entities or not entities[entity]]
        
        # If missing required entities, prompt for them
        if missing_entities:
            return self._create_entity_prompt_action(
                missing_entity=missing_entities[0],
                flow=flow,
                language=language
            )
        
        # Determine next state based on intent
        next_states = flow.get("next_states", {})
        next_state = next_states.get(intent, next_states.get("*", current_state))
        
        # Create response action
        action = {
            "action_type": "response",
            "response_type": flow.get("response", "general"),
            "dialog_state": next_state,
            "suggestions": flow.get("suggestions", []),
            "language": language,
            "entities": entities,
            "intent": intent
        }
        
        # Add service calls if specified in flow
        if "service_calls" in flow:
            action["service_calls"] = flow["service_calls"]
        
        return action
    
    def _create_greeting_action(self, language: str) -> Dict:
        """Create a greeting response action."""
        return {
            "action_type": "response",
            "response_type": "greeting",
            "dialog_state": "information_gathering",
            "suggestions": ["attractions", "hotels", "restaurants", "practical_info"],
            "language": language
        }
    
    def _create_farewell_action(self, language: str) -> Dict:
        """Create a farewell response action."""
        return {
            "action_type": "response",
            "response_type": "farewell",
            "dialog_state": "end",
            "suggestions": [],
            "language": language
        }
    
    def _create_fallback_action(self, language: str) -> Dict:
        """Create a fallback response action."""
        return {
            "action_type": "response",
            "response_type": "fallback",
            "dialog_state": "information_gathering",
            "suggestions": ["attractions", "hotels", "restaurants", "practical_info"],
            "language": language
        }
    
    def _create_entity_prompt_action(self, missing_entity: str, flow: Dict, language: str) -> Dict:
        """Create an action to prompt for a missing entity."""
        # Get prompt for the missing entity
        prompts = flow.get("entity_missing_prompts", {}).get(missing_entity, {})
        prompt = prompts.get(language, prompts.get("en", f"Please provide a {missing_entity}"))
        
        return {
            "action_type": "prompt",
            "prompt_type": "entity_request",
            "entity_type": missing_entity,
            "prompt_text": prompt,
            "dialog_state": flow.get("name", "information_gathering"),
            "language": language
        }
    
    def get_suggestions(self, state: str, language: str = "en") -> List[Dict]:
        """
        Get suggested actions for a dialog state.
        
        Args:
            state (str): Dialog state
            language (str): Language code
            
        Returns:
            list: Suggested actions with texts
        """
        flow = self.flows.get(state, {})
        suggestions = flow.get("suggestions", [])
        
        result = []
        for suggestion in suggestions:
            suggestion_text = self._get_suggestion_text(suggestion, language)
            if suggestion_text:
                result.append({
                    "action": suggestion,
                    "text": suggestion_text
                })
        
        return result
    
    def _get_suggestion_text(self, suggestion: str, language: str) -> Optional[str]:
        """Get suggestion text in the specified language."""
        # This would be replaced with a proper suggestion text lookup
        # For now, just use a simple conversion
        suggestion_texts = {
            "en": {
                "attractions": "Top Attractions",
                "hotels": "Find Hotels",
                "restaurants": "Restaurants",
                "practical_info": "Practical Information",
                "visa": "Visa Requirements",
                "weather": "Weather Forecast",
                "transportation": "Transportation Options",
                "safety": "Safety Tips",
                "flights": "Flights",
                "trains": "Train Travel",
                "buses": "Bus Information",
                "local_transport": "Local Transport",
                "menu": "Restaurant Menu",
                "location": "Location & Directions",
                "opening_hours": "Opening Hours",
                "room_types": "Room Types",
                "amenities": "Hotel Amenities",
                "practical_info": "Practical Information",
                "nearby_attractions": "Nearby Attractions",
                "ticket_info": "Ticket Information",
                "cuisine_types": "Cuisine Types",
                "price_range": "Price Range",
                "top_rated": "Top Rated",
                "modify_itinerary": "Modify Itinerary"
            },
            "ar": {
                "attractions": "أهم المعالم السياحية",
                "hotels": "البحث عن فنادق",
                "restaurants": "مطاعم",
                "practical_info": "معلومات عملية",
                "visa": "متطلبات التأشيرة",
                "weather": "توقعات الطقس",
                "transportation": "خيارات النقل",
                "safety": "نصائح الأمان",
                "flights": "الرحلات الجوية",
                "trains": "السفر بالقطار",
                "buses": "معلومات الحافلات",
                "local_transport": "النقل المحلي",
                "menu": "قائمة الطعام",
                "location": "الموقع والاتجاهات",
                "opening_hours": "ساعات العمل",
                "room_types": "أنواع الغرف",
                "amenities": "مرافق الفندق",
                "practical_info": "معلومات عملية",
                "nearby_attractions": "المعالم القريبة",
                "ticket_info": "معلومات التذاكر",
                "cuisine_types": "أنواع المطبخ",
                "price_range": "نطاق السعر",
                "top_rated": "الأعلى تقييماً",
                "modify_itinerary": "تعديل خط السير"
            }
        }
        
        lang_texts = suggestion_texts.get(language, suggestion_texts.get("en", {}))
        return lang_texts.get(suggestion, suggestion.replace("_", " ").title())
    
    def handle_disambiguation(self, options: List[Dict], context: Dict, language: str = "en") -> Dict:
        """
        Create an action to handle disambiguation when multiple options are available.
        
        Args:
            options (list): List of options to disambiguate
            context (dict): Current conversation context
            language (str): Language code
            
        Returns:
            dict: Disambiguation action
        """
        prompts = {
            "en": "I found multiple options. Which one did you mean?",
            "ar": "وجدت عدة خيارات. أي واحد تقصد؟"
        }
        
        return {
            "action_type": "disambiguation",
            "prompt_text": prompts.get(language, prompts["en"]),
            "options": options,
            "dialog_state": context.get("dialog_state", "information_gathering"),
            "language": language
        }
    
    def get_default_response(self, response_type: str, language: str = "en") -> str:
        """
        Get a random default response for a response type.
        
        Args:
            response_type (str): Response type
            language (str): Language code
            
        Returns:
            str: Default response text
        """
        responses = self.default_responses.get(response_type, {})
        lang_responses = responses.get(language, responses.get("en", []))
        
        if not lang_responses:
            return ""
        
        return random.choice(lang_responses)