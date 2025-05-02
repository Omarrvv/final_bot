# src/response/generator.py
"""
Response generation module for the Egypt Tourism Chatbot.
Generates appropriate responses based on dialog actions and context.
"""
import json
import logging
import os
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Response generator that creates appropriate responses.
    Uses templates and dynamic content based on context and dialog actions.
    """
    
    def __init__(self, templates_path: str, knowledge_base, config: Dict = None):
        """
        Initialize the response generator with templates.
        
        Args:
            templates_path (str): Path to response templates directory
            knowledge_base: Reference to the knowledge base
            config (Dict, optional): Configuration options
        """
        self.templates_path = templates_path
        self.knowledge_base = knowledge_base
        
        # Default configuration
        self.config = {
            "search_limits": {
                "attractions": 10,
                "restaurants": 5,
                "hotels": 5,
                "itinerary_attractions": 6
            },
            "default_language": "en",
            "fallback_language": "en"
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Load response templates
        self.templates = self._load_templates(templates_path)
        
        logger.info("Response generator initialized successfully")
    
    def _load_templates(self, templates_path: str) -> Dict:
        """Load response templates from directory."""
        templates = {}
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(templates_path, exist_ok=True)
            
            # Load each template file
            template_files = Path(templates_path).glob("*.json")
            for file_path in template_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template_name = file_path.stem
                        templates[template_name] = json.load(f)
                        logger.info(f"Loaded template: {template_name}")
                except Exception as e:
                    logger.error(f"Failed to load template {file_path}: {str(e)}")
            
            # If no templates found, create default templates
            if not templates:
                templates = self._create_default_templates(templates_path)
        except Exception as e:
            logger.error(f"Failed to load templates: {str(e)}")
            templates = self._create_default_templates(templates_path)
        
        return templates
    
    def _create_default_templates(self, templates_path: str) -> Dict:
        """Create and save default response templates."""
        templates = {
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
            },
            "attraction_details": {
                "en": [
                    "Here's what I know about {attraction_name}:\n\n{attraction_description}\n\n{attraction_history}\n\nPractical information:\n- Opening hours: {opening_hours}\n- Ticket prices: {ticket_prices}\n- Best time to visit: {best_time}",
                    "Let me tell you about {attraction_name}:\n\n{attraction_description}\n\n{attraction_history}\n\nVisitor information:\n- Hours: {opening_hours}\n- Admission: {ticket_prices}\n- Recommended: {best_time}"
                ],
                "ar": [
                    "إليك ما أعرفه عن {attraction_name}:\n\n{attraction_description}\n\n{attraction_history}\n\nمعلومات عملية:\n- ساعات العمل: {opening_hours}\n- أسعار التذاكر: {ticket_prices}\n- أفضل وقت للزيارة: {best_time}",
                    "دعني أخبرك عن {attraction_name}:\n\n{attraction_description}\n\n{attraction_history}\n\nمعلومات الزوار:\n- الساعات: {opening_hours}\n- رسوم الدخول: {ticket_prices}\n- موصى به: {best_time}"
                ]
            },
            "restaurant_list": {
                "en": [
                    "I found these restaurants in {location}:\n\n{restaurant_list}\n\nWould you like more details about any of these?",
                    "Here are some dining options in {location}:\n\n{restaurant_list}\n\nI can provide more information about any of these restaurants if you're interested."
                ],
                "ar": [
                    "وجدت هذه المطاعم في {location}:\n\n{restaurant_list}\n\nهل ترغب في مزيد من التفاصيل حول أي من هذه؟",
                    "إليك بعض خيارات تناول الطعام في {location}:\n\n{restaurant_list}\n\nيمكنني تقديم مزيد من المعلومات حول أي من هذه المطاعم إذا كنت مهتمًا."
                ]
            },
            "restaurant_details": {
                "en": [
                    "Here's information about {restaurant_name}:\n\n{restaurant_description}\n\nCuisine: {cuisine}\nLocation: {address}\nHours: {opening_hours}\nPrice range: {price_range}\n\nMenu highlights:\n{menu_highlights}",
                    "About {restaurant_name}:\n\n{restaurant_description}\n\n- Cuisine: {cuisine}\n- Address: {address}\n- Hours: {opening_hours}\n- Price: {price_range}\n\nPopular dishes:\n{menu_highlights}"
                ],
                "ar": [
                    "إليك معلومات عن {restaurant_name}:\n\n{restaurant_description}\n\nالمطبخ: {cuisine}\nالموقع: {address}\nالساعات: {opening_hours}\nنطاق السعر: {price_range}\n\nأبرز عناصر القائمة:\n{menu_highlights}",
                    "عن {restaurant_name}:\n\n{restaurant_description}\n\n- المطبخ: {cuisine}\n- العنوان: {address}\n- الساعات: {opening_hours}\n- السعر: {price_range}\n\nالأطباق الشعبية:\n{menu_highlights}"
                ]
            },
            "hotel_list": {
                "en": [
                    "I found these hotels in {location}:\n\n{hotel_list}\n\nWould you like more details about any of these?",
                    "Here are some accommodation options in {location}:\n\n{hotel_list}\n\nI can provide more information about any of these hotels if you're interested."
                ],
                "ar": [
                    "وجدت هذه الفنادق في {location}:\n\n{hotel_list}\n\nهل ترغب في مزيد من التفاصيل حول أي من هذه؟",
                    "إليك بعض خيارات الإقامة في {location}:\n\n{hotel_list}\n\nيمكنني تقديم مزيد من المعلومات حول أي من هذه الفنادق إذا كنت مهتمًا."
                ]
            },
            "hotel_details": {
                "en": [
                    "Here's information about {hotel_name}:\n\n{hotel_description}\n\nCategory: {category}\nLocation: {address}\nPrice range: {price_range}\n\nAmenities:\n{amenities}\n\nRoom types:\n{room_types}",
                    "About {hotel_name}:\n\n{hotel_description}\n\n- Category: {category}\n- Address: {address}\n- Price: {price_range}\n\nFacilities:\n{amenities}\n\nAccommodation options:\n{room_types}"
                ],
                "ar": [
                    "إليك معلومات عن {hotel_name}:\n\n{hotel_description}\n\nالفئة: {category}\nالموقع: {address}\nنطاق السعر: {price_range}\n\nوسائل الراحة:\n{amenities}\n\nأنواع الغرف:\n{room_types}",
                    "عن {hotel_name}:\n\n{hotel_description}\n\n- الفئة: {category}\n- العنوان: {address}\n- السعر: {price_range}\n\nالمرافق:\n{amenities}\n\nخيارات الإقامة:\n{room_types}"
                ]
            },
            "practical_info": {
                "en": [
                    "Here's practical information about {info_type} in Egypt:\n\n{info_details}",
                    "Important information about {info_type} for your Egypt trip:\n\n{info_details}"
                ],
                "ar": [
                    "إليك معلومات عملية حول {info_type} في مصر:\n\n{info_details}",
                    "معلومات مهمة حول {info_type} لرحلتك إلى مصر:\n\n{info_details}"
                ]
            },
            "transportation_info": {
                "en": [
                    "Here's information about {transport_type} in Egypt:\n\n{transport_details}",
                    "Transportation details about {transport_type} for your Egypt trip:\n\n{transport_details}"
                ],
                "ar": [
                    "إليك معلومات حول {transport_type} في مصر:\n\n{transport_details}",
                    "تفاصيل النقل حول {transport_type} لرحلتك إلى مصر:\n\n{transport_details}"
                ]
            },
            "suggested_itinerary": {
                "en": [
                    "Based on your preferences, here's a suggested {duration}-day itinerary for {location}:\n\n{itinerary_details}",
                    "I've created a {duration}-day itinerary for your trip to {location}:\n\n{itinerary_details}"
                ],
                "ar": [
                    "بناءً على تفضيلاتك، إليك خطة سفر مقترحة لمدة {duration} يوم في {location}:\n\n{itinerary_details}",
                    "لقد أنشأت خطة سفر لمدة {duration} يوم لرحلتك إلى {location}:\n\n{itinerary_details}"
                ]
            }
        }
        
        # Save each template to a separate file
        for template_name, template_data in templates.items():
            file_path = os.path.join(templates_path, f"{template_name}.json")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Created template file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save template {file_path}: {str(e)}")
        
        return templates
    
    def generate_response(self, dialog_action: Dict, nlu_result: Dict, context: Dict) -> Dict:
        """
        Generate a response based on dialog action, NLU result, and context.
        
        Args:
            dialog_action (dict): Dialog action to respond to
            nlu_result (dict): NLU processing result
            context (dict): Current conversation context
            
        Returns:
            dict: Response data including text, suggestions, etc.
        """
        action_type = dialog_action.get("action_type", "response")
        language = dialog_action.get("language", "en")
        
        # Generate response based on action type
        if action_type == "response":
            return self._generate_response_action(dialog_action, nlu_result, context)
        elif action_type == "prompt":
            return self._generate_prompt_action(dialog_action, context)
        elif action_type == "disambiguation":
            return self._generate_disambiguation_action(dialog_action, context)
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return self._generate_fallback_response(language)

    def generate_response(self, response_type: str, language: str, params: Dict = None) -> str:
        """
        Alternative signature for generate_response to handle direct calls from chatbot.py.
        
        Args:
            response_type (str): The type of response to generate
            language (str): The language for the response
            params (Dict, optional): Parameters for the response
            
        Returns:
            str: The generated response text
        """
        # Simple fallback if params are None
        if params is None:
            params = {}
        
        # Get template for response type
        template = self._get_template(response_type, language)
        
        # Generate response based on type
        if response_type == "attraction_details":
            return self._generate_attraction_details(template, params, language)
        elif response_type == "restaurant_list":
            return self._generate_restaurant_list(template, params, language)
        elif response_type == "restaurant_details":
            return self._generate_restaurant_details(template, params, language)
        elif response_type == "hotel_list":
            return self._generate_hotel_list(template, params, language)
        elif response_type == "hotel_details":
            return self._generate_hotel_details(template, params, language)
        elif response_type == "practical_info":
            return self._generate_practical_info(template, params, language)
        elif response_type == "transportation_info":
            return self._generate_transportation_info(template, params, language)
        elif response_type == "suggested_itinerary":
            return self._generate_itinerary(template, params, language)
        elif response_type == "greeting":
            return template
        elif response_type == "farewell":
            return template
        elif response_type == "fallback":
            return template
        elif response_type == "general":
            return template
        else:
            # Use fallback for unknown response types
            logger.warning(f"Unknown response type: {response_type}, using fallback")
            return self._get_template("fallback", language)
    
    def _generate_response_action(self, dialog_action: Dict, nlu_result: Dict, context: Dict) -> Dict:
        """Generate a response for a response action."""
        response_type = dialog_action.get("response_type", "fallback")
        language = dialog_action.get("language", "en")
        entities = dialog_action.get("entities", {})
        intent = dialog_action.get("intent", "")
        
        # Handle 'general' response type like 'fallback'
        if response_type == "general":
            logger.warning(f"Handling 'general' response type as 'fallback'.")
            response_type = "fallback"
            
        # Get response template
        template = self._get_template(response_type, language)
        
        # Fill template with data based on response type
        if response_type == "greeting":
            response_text = template
        elif response_type == "farewell":
            response_text = template
        elif response_type == "fallback":
            response_text = template
        elif response_type == "attraction_details":
            response_text = self._generate_attraction_details(template, entities, language)
        elif response_type == "restaurant_list":
            response_text = self._generate_restaurant_list(template, entities, language)
        elif response_type == "restaurant_details":
            response_text = self._generate_restaurant_details(template, entities, language)
        elif response_type == "hotel_list":
            response_text = self._generate_hotel_list(template, entities, language)
        elif response_type == "hotel_details":
            response_text = self._generate_hotel_details(template, entities, language)
        elif response_type == "practical_info":
            response_text = self._generate_practical_info(template, entities, language)
        elif response_type == "transportation_info":
            response_text = self._generate_transportation_info(template, entities, language)
        elif response_type == "suggested_itinerary":
            response_text = self._generate_itinerary(template, context, language)
        else:
            logger.warning(f"Unhandled response type: {response_type}. Using template directly.")
            response_text = template # Use template directly if type is unknown
        
        # Add media content if relevant
        media = self._get_media_content(response_type, entities, language)
        
        # Construct final response
        response = {
            "text": response_text, # Use the generated/template text
            "message": response_text, # Add the 'message' key as expected by the test
            "response_type": response_type,
            "language": language,
            "suggestions": dialog_action.get("suggestions", [])
        }
        
        if media:
            response["media"] = media
            
        return response
    
    def _generate_prompt_action(self, dialog_action: Dict, context: Dict) -> Dict:
        """Generate a response for a prompt action."""
        prompt_type = dialog_action.get("prompt_type", "")
        language = dialog_action.get("language", "en")
        prompt_text = dialog_action.get("prompt_text", "")
        
        # Prepare response
        response = {
            "text": prompt_text,
            "response_type": "prompt",
            "prompt_type": prompt_type,
            "language": language
        }
        
        # Add entity type if it's an entity request
        if prompt_type == "entity_request":
            response["entity_type"] = dialog_action.get("entity_type", "")
        
        return response
    
    def _generate_disambiguation_action(self, dialog_action: Dict, context: Dict) -> Dict:
        """Generate a response for a disambiguation action."""
        language = dialog_action.get("language", "en")
        prompt_text = dialog_action.get("prompt_text", "")
        options = dialog_action.get("options", [])
        
        # Format options for display
        formatted_options = []
        for i, option in enumerate(options):
            option_text = option.get("text", "")
            option_value = option.get("value", "")
            formatted_options.append(f"{i+1}. {option_text}")
        
        options_text = "\n".join(formatted_options)
        
        # Prepare response
        response = {
            "text": f"{prompt_text}\n\n{options_text}",
            "response_type": "disambiguation",
            "language": language,
            "options": options
        }
        
        return response
    
    def _generate_fallback_response(self, language: str) -> Dict:
        """Generate a fallback response."""
        template = self._get_template("fallback", language)
        
        return {
            "text": template,
            "response_type": "fallback",
            "language": language,
            "suggestions": ["attractions", "hotels", "restaurants", "practical_info"]
        }
    
    def _get_template(self, template_name: str, language: str) -> str:
        # Debug: print types and values
        logger.debug(f"_get_template called with template_name={template_name} (type={type(template_name)}), language={language} (type={type(language)})")
        # Ensure keys are strings
        if not isinstance(template_name, str):
            logger.warning(f"template_name is not a string: {template_name} (type={type(template_name)})")
            template_name = str(template_name)
        if not isinstance(language, str):
            logger.warning(f"language is not a string: {language} (type={type(language)})")
            language = str(language)
        """Get a template text for the specified template name and language."""
        # Convert numeric response types to strings if needed
        if isinstance(template_name, (int, float)):
            logger.warning(f"Numeric template name received: {template_name}, converting to 'fallback'")
            template_name = "fallback"
            
        if template_name not in self.templates:
            logger.warning(f"Template not found: {template_name}, using fallback")
            template_name = "fallback"
            # If fallback is also not found, return a default message
            if template_name not in self.templates:
                return "I'm sorry, I'm having trouble understanding. Could you try again?"
        
        templates = self.templates[template_name]
        
        # Handle nested dictionary structure
        lang_data = templates.get(language, templates.get("en", {}))
        
        # Check if lang_data is a dictionary with keys like 'default'
        if isinstance(lang_data, dict):
            # Return the default message if available, otherwise fallback
            if "default" in lang_data:
                return lang_data["default"]
            elif "fallback" in lang_data:
                return lang_data["fallback"]
            else:
                logger.warning(f"No default or fallback key in template {template_name} for language {language}")
                return "I'm sorry, I'm having trouble understanding. Could you try again?"
        
        # If it's a list (from default templates), use random choice
        elif isinstance(lang_data, list) and lang_data:
            return random.choice(lang_data)
            
        # If all else fails, return default message
        logger.warning(f"Invalid template format for {template_name}: {lang_data}")
        return "I'm sorry, I'm having trouble understanding. Could you try again?"
    
    def _generate_attraction_details(self, template: str, entities: Dict, language: str) -> str:
        """Generate attraction details text."""
        # Get attraction entity
        attraction_entities = entities.get("attraction", [])
        if not attraction_entities:
            return template.format(
                attraction_name="",
                attraction_description="(No attraction specified)",
                attraction_history="",
                opening_hours="",
                ticket_prices="",
                best_time=""
            )
        
        # Get attraction from knowledge base
        attraction_entity = attraction_entities[0]["value"]
        attraction = self._lookup_attraction(attraction_entity, language)
        
        if not attraction:
            return template.format(
                attraction_name=attraction_entity,
                attraction_description="(No information available)",
                attraction_history="",
                opening_hours="",
                ticket_prices="",
                best_time=""
            )
        
        # Extract details
        name = attraction["name"][language] if language in attraction["name"] else attraction["name"].get("en", "")
        description = attraction["description"][language] if language in attraction["description"] else attraction["description"].get("en", "")
        history = attraction.get("history", {}).get(language, attraction.get("history", {}).get("en", ""))
        
        # Get practical info
        practical = attraction.get("practical_info", {})
        opening_hours = practical.get("opening_hours", "")
        
        # Format ticket prices
        ticket_prices = ""
        if "ticket_prices" in practical:
            prices = practical["ticket_prices"]
            if language == "ar":
                # Format prices in Arabic
                if "foreigners" in prices:
                    ticket_prices += "الأجانب:\n"
                    if "adults" in prices["foreigners"]:
                        ticket_prices += f"- البالغين: {prices['foreigners']['adults']}\n"
                    if "students" in prices["foreigners"]:
                        ticket_prices += f"- الطلاب: {prices['foreigners']['students']}\n"
                
                if "egyptians" in prices:
                    ticket_prices += "المصريين:\n"
                    if "adults" in prices["egyptians"]:
                        ticket_prices += f"- البالغين: {prices['egyptians']['adults']}\n"
                    if "students" in prices["egyptians"]:
                        ticket_prices += f"- الطلاب: {prices['egyptians']['students']}\n"
            else:
                # Format prices in English
                if "foreigners" in prices:
                    ticket_prices += "Foreigners:\n"
                    if "adults" in prices["foreigners"]:
                        ticket_prices += f"- Adults: {prices['foreigners']['adults']}\n"
                    if "students" in prices["foreigners"]:
                        ticket_prices += f"- Students: {prices['foreigners']['students']}\n"
                
                if "egyptians" in prices:
                    ticket_prices += "Egyptians:\n"
                    if "adults" in prices["egyptians"]:
                        ticket_prices += f"- Adults: {prices['egyptians']['adults']}\n"
                    if "students" in prices["egyptians"]:
                        ticket_prices += f"- Students: {prices['egyptians']['students']}\n"
        
        best_time = practical.get("best_time_to_visit", "")
        
        # Fill template
        return template.format(
            attraction_name=name,
            attraction_description=description,
            attraction_history=history,
            opening_hours=opening_hours,
            ticket_prices=ticket_prices.strip(),
            best_time=best_time
        )
    
    def _generate_restaurant_list(self, template: str, entities: Dict, language: str) -> str:
        """Generate restaurant list text."""
        # Get location entity
        location_entities = entities.get("location", [])
        if not location_entities:
            return template.format(
                location="",
                restaurant_list="(No location specified)"
            )
        
        location_entity = location_entities[0]["value"]
        
        # Search for restaurants
        restaurants = self.knowledge_base.search_restaurants(
            query="",
            filters={"location": location_entity},
            language=language,
            limit=5
        )
        
        if not restaurants:
            no_results = "I couldn't find any restaurants in that location." if language == "en" else "لم أتمكن من العثور على أي مطاعم في هذا الموقع."
            return template.format(
                location=location_entity,
                restaurant_list=no_results
            )
        
        # Format restaurant list
        restaurant_list = ""
        for i, restaurant in enumerate(restaurants):
            name = restaurant["name"][language] if language in restaurant["name"] else restaurant["name"].get("en", "")
            cuisine = restaurant.get("cuisine", "")
            price_range = restaurant.get("price_range", "")
            
            restaurant_list += f"{i+1}. {name}\n"
            
            if cuisine:
                restaurant_list += f"   {'المطبخ' if language == 'ar' else 'Cuisine'}: {cuisine}\n"
            
            if price_range:
                restaurant_list += f"   {'نطاق السعر' if language == 'ar' else 'Price'}: {price_range}\n"
            
            restaurant_list += "\n"
        
        # Fill template
        return template.format(
            location=location_entity,
            restaurant_list=restaurant_list.strip()
        )
    
    def _generate_restaurant_details(self, template: str, entities: Dict, language: str) -> str:
        """Generate restaurant details text."""
        # Get restaurant entity
        restaurant_entities = entities.get("restaurant", [])
        if not restaurant_entities:
            return template.format(
                restaurant_name="",
                restaurant_description="(No restaurant specified)",
                cuisine="",
                address="",
                opening_hours="",
                price_range="",
                menu_highlights=""
            )
        
        # Get restaurant from knowledge base
        restaurant_entity = restaurant_entities[0]["value"]
        restaurant = self._lookup_restaurant(restaurant_entity, language)
        
        if not restaurant:
            return template.format(
                restaurant_name=restaurant_entity,
                restaurant_description="(No information available)",
                cuisine="",
                address="",
                opening_hours="",
                price_range="",
                menu_highlights=""
            )
        
        # Extract details
        name = restaurant["name"][language] if language in restaurant["name"] else restaurant["name"].get("en", "")
        description = restaurant["description"][language] if language in restaurant["description"] else restaurant["description"].get("en", "")
        cuisine = restaurant.get("cuisine", "")
        
        # Get location
        location = restaurant.get("location", {})
        address = location.get("address", {}).get(language, location.get("address", {}).get("en", ""))
        
        # Get hours
        hours = restaurant.get("hours", {})
        opening_hours = ""
        if "daily" in hours:
            opening_hours = hours["daily"]
        elif "weekdays" in hours and "weekends" in hours:
            weekdays = hours["weekdays"]
            weekends = hours["weekends"]
            opening_hours = f"{'أيام الأسبوع' if language == 'ar' else 'Weekdays'}: {weekdays}\n{'عطلة نهاية الأسبوع' if language == 'ar' else 'Weekends'}: {weekends}"
        
        # Get price range
        price_range = restaurant.get("price_range", "")
        
        # Format menu highlights
        menu_highlights = ""
        if "menu_highlights" in restaurant:
            for i, item in enumerate(restaurant["menu_highlights"]):
                item_name = item["name"][language] if language in item["name"] else item["name"].get("en", "")
                item_desc = item["description"][language] if language in item["description"] else item["description"].get("en", "")
                item_price = item.get("price", "")
                
                menu_highlights += f"{i+1}. {item_name}"
                if item_price:
                    menu_highlights += f" ({item_price})"
                menu_highlights += f"\n   {item_desc}\n"
        
        # Fill template
        return template.format(
            restaurant_name=name,
            restaurant_description=description,
            cuisine=cuisine,
            address=address,
            opening_hours=opening_hours,
            price_range=price_range,
            menu_highlights=menu_highlights.strip()
        )
    
    def _generate_hotel_list(self, template: str, entities: Dict, language: str) -> str:
        """Generate hotel list text."""
        # Get location entity
        location_entities = entities.get("location", [])
        if not location_entities:
            return template.format(
                location="",
                hotel_list="(No location specified)"
            )
        
        location_entity = location_entities[0]["value"]
        
        # Search for hotels
        hotels = self.knowledge_base.search_hotels(
            query="",
            filters={"location": location_entity},
            language=language,
            limit=5
        )
        
        if not hotels:
            no_results = "I couldn't find any hotels in that location." if language == "en" else "لم أتمكن من العثور على أي فنادق في هذا الموقع."
            return template.format(
                location=location_entity,
                hotel_list=no_results
            )
        
        # Format hotel list
        hotel_list = ""
        for i, hotel in enumerate(hotels):
            name = hotel["name"][language] if language in hotel["name"] else hotel["name"].get("en", "")
            category = hotel.get("category", "")
            price_range = hotel.get("price_range", {})
            price_min = price_range.get("min", "")
            price_max = price_range.get("max", "")
            price_text = f"{price_min} - {price_max}" if price_min and price_max else ""
            
            hotel_list += f"{i+1}. {name}\n"
            
            if category:
                hotel_list += f"   {'الفئة' if language == 'ar' else 'Category'}: {category}\n"
            
            if price_text:
                hotel_list += f"   {'نطاق السعر' if language == 'ar' else 'Price Range'}: {price_text}\n"
            
            hotel_list += "\n"
        
        # Fill template
        return template.format(
            location=location_entity,
            hotel_list=hotel_list.strip()
        )
    
    def _generate_hotel_details(self, template: str, entities: Dict, language: str) -> str:
        """Generate hotel details text."""
        # Get hotel entity
        hotel_entities = entities.get("hotel", [])
        if not hotel_entities:
            return template.format(
                hotel_name="",
                hotel_description="(No hotel specified)",
                category="",
                address="",
                price_range="",
                amenities="",
                room_types=""
            )
        
        # Get hotel from knowledge base
        hotel_entity = hotel_entities[0]["value"]
        hotel = self._lookup_hotel(hotel_entity, language)
        
        if not hotel:
            return template.format(
                hotel_name=hotel_entity,
                hotel_description="(No information available)",
                category="",
                address="",
                price_range="",
                amenities="",
                room_types=""
            )
        
        # Extract details
        name = hotel["name"][language] if language in hotel["name"] else hotel["name"].get("en", "")
        description = hotel["description"][language] if language in hotel["description"] else hotel["description"].get("en", "")
        category = hotel.get("category", "")
        
        # Get location
        location = hotel.get("location", {})
        address = location.get("address", {}).get(language, location.get("address", {}).get("en", ""))
        
        # Get price range
        price_range = hotel.get("price_range", {})
        price_min = price_range.get("min", "")
        price_max = price_range.get("max", "")
        price_text = f"{price_min} - {price_max}" if price_min and price_max else ""
        
        # Format amenities
        amenities_list = hotel.get("amenities", [])
        amenities = "\n".join([f"- {amenity}" for amenity in amenities_list])
        
        # Format room types
        room_types_text = ""
        if "room_types" in hotel:
            for i, room in enumerate(hotel["room_types"]):
                room_name = room["name"][language] if language in room["name"] else room["name"].get("en", "")
                room_desc = room["description"][language] if language in room["description"] else room["description"].get("en", "")
                room_price = room.get("price", "")
                
                room_types_text += f"{i+1}. {room_name}"
                if room_price:
                    room_types_text += f" ({room_price})"
                room_types_text += f"\n   {room_desc}\n"
        
        # Fill template
        return template.format(
            hotel_name=name,
            hotel_description=description,
            category=category,
            address=address,
            price_range=price_text,
            amenities=amenities,
            room_types=room_types_text.strip()
        )
    
    def _generate_practical_info(self, template: str, entities: Dict, language: str) -> str:
        """Generate practical information text."""
        # Get info type entity
        info_type_entities = entities.get("info_type", [])
        if not info_type_entities:
            return template.format(
                info_type="",
                info_details="(No information type specified)"
            )
        
        info_type_entity = info_type_entities[0]["value"].lower()
        
        # Map entity value to practical info category
        category_mapping = {
            "visa": "visa",
            "visas": "visa",
            "visa requirements": "visa",
            "تأشيرة": "visa",
            "متطلبات التأشيرة": "visa",
            
            "currency": "currency",
            "money": "currency",
            "عملة": "currency",
            "نقود": "currency",
            
            "weather": "weather",
            "climate": "weather",
            "طقس": "weather",
            "مناخ": "weather",
            
            "transportation": "transportation",
            "transport": "transportation",
            "مواصلات": "transportation",
            "نقل": "transportation",
            
            "health": "health_safety",
            "safety": "health_safety",
            "security": "health_safety",
            "صحة": "health_safety",
            "أمان": "health_safety",
            "سلامة": "health_safety",
            
            "culture": "cultural_customs",
            "customs": "cultural_customs",
            "etiquette": "cultural_customs",
            "ثقافة": "cultural_customs",
            "عادات": "cultural_customs",
            "آداب": "cultural_customs",
            
            "phone": "telecommunications",
            "internet": "telecommunications",
            "wifi": "telecommunications",
            "هاتف": "telecommunications",
            "إنترنت": "telecommunications",
            "واي فاي": "telecommunications",
            
            "holidays": "holidays_events",
            "events": "holidays_events",
            "festivals": "holidays_events",
            "عطلات": "holidays_events",
            "أحداث": "holidays_events",
            "مهرجانات": "holidays_events"
        }
        
        category = category_mapping.get(info_type_entity)
        if not category:
            # Try partial matching
            for key, value in category_mapping.items():
                if key in info_type_entity or info_type_entity in key:
                    category = value
                    break
        
        if not category:
            return template.format(
                info_type=info_type_entity,
                info_details="(No information available for this topic)"
            )
        
        # Get practical info from knowledge base
        info = self.knowledge_base.get_practical_info(category)
        if not info:
            return template.format(
                info_type=info_type_entity,
                info_details="(No information available)"
            )
        
        # Format info based on category and language
        info_details = self._format_practical_info(category, info, language)
        
        # Fill template
        display_name = {
            "visa": "Visa Requirements" if language == "en" else "متطلبات التأشيرة",
            "currency": "Currency Information" if language == "en" else "معلومات العملة",
            "weather": "Weather and Climate" if language == "en" else "الطقس والمناخ",
            "transportation": "Transportation Options" if language == "en" else "خيارات النقل",
            "health_safety": "Health and Safety" if language == "en" else "الصحة والسلامة",
            "cultural_customs": "Cultural Customs" if language == "en" else "العادات الثقافية",
            "telecommunications": "Phone and Internet" if language == "en" else "الهاتف والإنترنت",
            "holidays_events": "Holidays and Events" if language == "en" else "العطلات والفعاليات"
        }.get(category, info_type_entity)
        
        return template.format(
            info_type=display_name,
            info_details=info_details
        )
    
    def _format_practical_info(self, category: str, info: Dict, language: str) -> str:
        """Format practical information based on category and language."""
        if category == "visa":
            return self._format_visa_info(info, language)
        elif category == "currency":
            return self._format_currency_info(info, language)
        elif category == "weather":
            return self._format_weather_info(info, language)
        elif category == "transportation":
            return self._format_transportation_info(info, language)
        elif category == "health_safety":
            return self._format_health_safety_info(info, language)
        elif category == "cultural_customs":
            return self._format_cultural_customs_info(info, language)
        elif category == "telecommunications":
            return self._format_telecommunications_info(info, language)
        elif category == "holidays_events":
            return self._format_holidays_events_info(info, language)
        else:
            # Generic formatting for unknown categories
            return json.dumps(info, indent=2, ensure_ascii=False)
    
    def _format_visa_info(self, info: Dict, language: str) -> str:
        """Format visa information."""
        if not info or "types" not in info:
            return "(No visa information available)" if language == "en" else "(لا تتوفر معلومات عن التأشيرة)"
        
        visa_types = info["types"]
        requirements = info.get("requirements", [])
        
        if language == "ar":
            result = "أنواع التأشيرات:\n\n"
            
            for visa in visa_types:
                name = visa.get("name", {}).get("ar", visa.get("name", {}).get("en", ""))
                desc = visa.get("description", {}).get("ar", visa.get("description", {}).get("en", ""))
                duration = visa.get("duration", "")
                price = visa.get("price", "")
                
                result += f"{name}:\n"
                result += f"{desc}\n"
                if duration:
                    result += f"المدة: {duration}\n"
                if price:
                    result += f"السعر: {price}\n"
                result += "\n"
            
            if requirements:
                result += "المتطلبات العامة:\n"
                for req in requirements:
                    result += f"- {req}\n"
            
            return result.strip()
        else:
            result = "Visa Types:\n\n"
            
            for visa in visa_types:
                name = visa.get("name", {}).get("en", "")
                desc = visa.get("description", {}).get("en", "")
                duration = visa.get("duration", "")
                price = visa.get("price", "")
                
                result += f"{name}:\n"
                result += f"{desc}\n"
                if duration:
                    result += f"Duration: {duration}\n"
                if price:
                    result += f"Price: {price}\n"
                result += "\n"
            
            if requirements:
                result += "General Requirements:\n"
                for req in requirements:
                    result += f"- {req}\n"
            
            return result.strip()
    
    def _format_currency_info(self, info: Dict, language: str) -> str:
        """Format currency information."""
        if not info:
            return "(No currency information available)" if language == "en" else "(لا تتوفر معلومات عن العملة)"
        
        currency_name = info.get("name", {}).get(language, info.get("name", {}).get("en", ""))
        code = info.get("code", "")
        exchange_info = info.get("exchange_info", {}).get(language, info.get("exchange_info", {}).get("en", ""))
        tips = info.get("tips", {}).get(language, info.get("tips", {}).get("en", ""))
        
        if language == "ar":
            result = f"العملة: {currency_name} ({code})\n\n"
            if exchange_info:
                result += f"معلومات الصرف:\n{exchange_info}\n\n"
            if tips:
                result += f"نصائح:\n{tips}"
            return result.strip()
        else:
            result = f"Currency: {currency_name} ({code})\n\n"
            if exchange_info:
                result += f"Exchange Information:\n{exchange_info}\n\n"
            if tips:
                result += f"Tips:\n{tips}"
            return result.strip()

    def _format_weather_info(self, info: Dict, language: str) -> str:
        """Format weather information."""
        if not info:
            return "(No weather information available)" if language == "en" else "(لا تتوفر معلومات عن الطقس)"
        
        seasons = info.get("seasons", [])
        if not seasons:
            return "(Weather information unavailable)" if language == "en" else "(معلومات الطقس غير متوفرة)"
        
        if language == "ar":
            result = "الطقس والمناخ في مصر:\n\n"
            for season in seasons:
                name = season.get("name", {}).get("ar", season.get("name", {}).get("en", ""))
                months = season.get("months", "")
                description = season.get("description", {}).get("ar", season.get("description", {}).get("en", ""))
                temp_range = season.get("temperature_range", "")
                
                result += f"{name} ({months}):\n"
                if description:
                    result += f"{description}\n"
                if temp_range:
                    result += f"نطاق درجة الحرارة: {temp_range}\n"
                result += "\n"
            return result.strip()
        else:
            result = "Weather and Climate in Egypt:\n\n"
            for season in seasons:
                name = season.get("name", {}).get("en", "")
                months = season.get("months", "")
                description = season.get("description", {}).get("en", "")
                temp_range = season.get("temperature_range", "")
                
                result += f"{name} ({months}):\n"
                if description:
                    result += f"{description}\n"
                if temp_range:
                    result += f"Temperature Range: {temp_range}\n"
                result += "\n"
            return result.strip()

    def _format_health_safety_info(self, info: Dict, language: str) -> str:
        """Format health and safety information."""
        if not info:
            return "(No health and safety information available)" if language == "en" else "(لا تتوفر معلومات عن الصحة والسلامة)"
        
        health_info = info.get("health", {}).get(language, info.get("health", {}).get("en", ""))
        safety_info = info.get("safety", {}).get(language, info.get("safety", {}).get("en", ""))
        emergency_contacts = info.get("emergency_contacts", {})
        
        if language == "ar":
            result = ""
            if health_info:
                result += f"معلومات صحية:\n{health_info}\n\n"
            if safety_info:
                result += f"معلومات السلامة:\n{safety_info}\n\n"
            if emergency_contacts:
                result += "أرقام الطوارئ:\n"
                for contact_name, contact_number in emergency_contacts.items():
                    result += f"- {contact_name}: {contact_number}\n"
            return result.strip()
        else:
            result = ""
            if health_info:
                result += f"Health Information:\n{health_info}\n\n"
            if safety_info:
                result += f"Safety Information:\n{safety_info}\n\n"
            if emergency_contacts:
                result += "Emergency Contacts:\n"
                for contact_name, contact_number in emergency_contacts.items():
                    result += f"- {contact_name}: {contact_number}\n"
            return result.strip()

    def _format_cultural_customs_info(self, info: Dict, language: str) -> str:
        """Format cultural customs information."""
        if not info:
            return "(No cultural customs information available)" if language == "en" else "(لا تتوفر معلومات عن العادات الثقافية)"
        
        customs = info.get("customs", [])
        etiquette = info.get("etiquette", {}).get(language, info.get("etiquette", {}).get("en", ""))
        
        if language == "ar":
            result = "العادات الثقافية في مصر:\n\n"
            if customs:
                for custom in customs:
                    title = custom.get("title", {}).get("ar", custom.get("title", {}).get("en", ""))
                    description = custom.get("description", {}).get("ar", custom.get("description", {}).get("en", ""))
                    result += f"{title}:\n{description}\n\n"
            if etiquette:
                result += f"آداب السلوك:\n{etiquette}"
            return result.strip()
        else:
            result = "Cultural Customs in Egypt:\n\n"
            if customs:
                for custom in customs:
                    title = custom.get("title", {}).get("en", "")
                    description = custom.get("description", {}).get("en", "")
                    result += f"{title}:\n{description}\n\n"
            if etiquette:
                result += f"Etiquette:\n{etiquette}"
            return result.strip()

    def _format_telecommunications_info(self, info: Dict, language: str) -> str:
        """Format telecommunications information."""
        if not info:
            return "(No telecommunications information available)" if language == "en" else "(لا تتوفر معلومات عن الاتصالات)"
        
        phone_info = info.get("phone", {}).get(language, info.get("phone", {}).get("en", ""))
        internet_info = info.get("internet", {}).get(language, info.get("internet", {}).get("en", ""))
        providers = info.get("providers", [])
        
        if language == "ar":
            result = "معلومات الاتصالات في مصر:\n\n"
            if phone_info:
                result += f"الهاتف:\n{phone_info}\n\n"
            if internet_info:
                result += f"الإنترنت:\n{internet_info}\n\n"
            if providers:
                result += "مزودي الخدمة:\n"
                for provider in providers:
                    name = provider.get("name", "")
                    services = provider.get("services", "")
                    result += f"- {name}: {services}\n"
            return result.strip()
        else:
            result = "Telecommunications in Egypt:\n\n"
            if phone_info:
                result += f"Phone:\n{phone_info}\n\n"
            if internet_info:
                result += f"Internet:\n{internet_info}\n\n"
            if providers:
                result += "Service Providers:\n"
                for provider in providers:
                    name = provider.get("name", "")
                    services = provider.get("services", "")
                    result += f"- {name}: {services}\n"
            return result.strip()

    def _format_holidays_events_info(self, info: Dict, language: str) -> str:
        """Format holidays and events information."""
        if not info:
            return "(No holidays and events information available)" if language == "en" else "(لا تتوفر معلومات عن العطلات والفعاليات)"
        
        holidays = info.get("holidays", [])
        festivals = info.get("festivals", [])
        
        if language == "ar":
            result = "العطلات والفعاليات في مصر:\n\n"
            if holidays:
                result += "العطلات الرسمية:\n"
                for holiday in holidays:
                    name = holiday.get("name", {}).get("ar", holiday.get("name", {}).get("en", ""))
                    date = holiday.get("date", "")
                    description = holiday.get("description", {}).get("ar", holiday.get("description", {}).get("en", ""))
                    result += f"- {name} ({date}): {description}\n"
                result += "\n"
            if festivals:
                result += "المهرجانات والفعاليات:\n"
                for festival in festivals:
                    name = festival.get("name", {}).get("ar", festival.get("name", {}).get("en", ""))
                    period = festival.get("period", "")
                    description = festival.get("description", {}).get("ar", festival.get("description", {}).get("en", ""))
                    result += f"- {name} ({period}): {description}\n"
            return result.strip()
        else:
            result = "Holidays and Events in Egypt:\n\n"
            if holidays:
                result += "Public Holidays:\n"
                for holiday in holidays:
                    name = holiday.get("name", {}).get("en", "")
                    date = holiday.get("date", "")
                    description = holiday.get("description", {}).get("en", "")
                    result += f"- {name} ({date}): {description}\n"
                result += "\n"
            if festivals:
                result += "Festivals and Events:\n"
                for festival in festivals:
                    name = festival.get("name", {}).get("en", "")
                    period = festival.get("period", "")
                    description = festival.get("description", {}).get("en", "")
                    result += f"- {name} ({period}): {description}\n"
            return result.strip()
    
    def _generate_transportation_info(self, template: str, entities: Dict, language: str) -> str:
        """Generate transportation information text."""
        # Get transport type entity
        transport_entities = entities.get("transport_type", [])
        if not transport_entities:
            return template.format(
                transport_type="",
                transport_details="(No transportation type specified)"
            )
        
        transport_type = transport_entities[0]["value"].lower()
        
        # Map entity value to transportation category
        category_mapping = {
            "flights": "airports",
            "flight": "airports",
            "airplane": "airports",
            "air travel": "airports",
            "رحلات جوية": "airports",
            "طيران": "airports",
            
            "trains": "domestic",
            "train": "domestic",
            "rail": "domestic",
            "قطارات": "domestic",
            "قطار": "domestic",
            "سكة حديد": "domestic",
            
            "buses": "domestic",
            "bus": "domestic",
            "coach": "domestic",
            "حافلات": "domestic",
            "حافلة": "domestic",
            "باص": "domestic",
            
            "nile cruise": "domestic",
            "cruise": "domestic",
            "رحلة نيلية": "domestic",
            
            "taxi": "local",
            "cab": "local",
            "تاكسي": "local",
            
            "metro": "local",
            "subway": "local",
            "مترو": "local",
            
            "local": "local",
            "city": "local",
            "محلي": "local",
            "مدينة": "local"
        }
        
        # Try to match transport type
        matched_category = None
        for key, value in category_mapping.items():
            if key == transport_type or key in transport_type or transport_type in key:
                matched_category = value
                break
        
        if not matched_category:
            # Default to providing all transportation info
            return self._format_all_transportation_info(language)
        
        # Get transportation info from knowledge base
        info = self.knowledge_base.get_practical_info("transportation")
        if not info or matched_category not in info:
            return template.format(
                transport_type=transport_type,
                transport_details="(No information available)"
            )
        
        # Format specific transportation info
        transport_details = self._format_specific_transportation_info(matched_category, info[matched_category], language)
        
        # Fill template
        display_name = {
            "airports": "Flights & Airports" if language == "en" else "الرحلات الجوية والمطارات",
            "domestic": "Domestic Transportation" if language == "en" else "وسائل النقل الداخلية",
            "local": "Local Transportation" if language == "en" else "وسائل النقل المحلية"
        }.get(matched_category, transport_type)
        
        return template.format(
            transport_type=display_name,
            transport_details=transport_details
        )
    
    def _format_specific_transportation_info(self, category: str, info: List, language: str) -> str:
        """Format specific transportation information."""
        if not info:
            return "(No information available)" if language == "en" else "(لا تتوفر معلومات)"
        
        if category == "airports":
            # Format airports info
            result = ""
            for airport in info:
                name = airport.get("name", {}).get(language, airport.get("name", {}).get("en", ""))
                code = airport.get("code", "")
                location = airport.get("location", "")
                description = airport.get("description", {}).get(language, airport.get("description", {}).get("en", ""))
                
                result += f"{name} ({code})\n"
                if location:
                    result += f"{'الموقع' if language == 'ar' else 'Location'}: {location}\n"
                if description:
                    result += f"{description}\n"
                result += "\n"
            
            return result.strip()
        else:
            # Format domestic or local transportation
            result = ""
            for transport in info:
                mode = transport.get("mode", {}).get(language, transport.get("mode", {}).get("en", ""))
                description = transport.get("description", {}).get(language, transport.get("description", {}).get("en", ""))
                tips = transport.get("tips", {}).get(language, transport.get("tips", {}).get("en", ""))
                
                result += f"{mode}\n"
                if description:
                    result += f"{description}\n"
                if tips:
                    result += f"{'نصائح' if language == 'ar' else 'Tips'}: {tips}\n"
                result += "\n"
            
            return result.strip()
    
    def _format_all_transportation_info(self, language: str) -> str:
        """Format all transportation information."""
        info = self.knowledge_base.get_practical_info("transportation")
        if not info:
            return "(No transportation information available)" if language == "en" else "(لا تتوفر معلومات عن وسائل النقل)"
        
        if language == "ar":
            result = "معلومات النقل في مصر:\n\n"
            
            # Major airports
            result += "المطارات الرئيسية:\n"
            for airport in info.get("airports", [])[:3]:  # Show only top 3 airports
                name = airport.get("name", {}).get("ar", airport.get("name", {}).get("en", ""))
                code = airport.get("code", "")
                location = airport.get("location", "")
                
                result += f"- {name} ({code}) - {location}\n"
            result += "\n"
            
            # Domestic transportation
            result += "وسائل النقل بين المدن:\n"
            for transport in info.get("domestic", []):
                mode = transport.get("mode", {}).get("ar", transport.get("mode", {}).get("en", ""))
                result += f"- {mode}\n"
            result += "\n"
            
            # Local transportation
            result += "وسائل النقل المحلية:\n"
            for transport in info.get("local", []):
                mode = transport.get("mode", {}).get("ar", transport.get("mode", {}).get("en", ""))
                result += f"- {mode}\n"
            
            return result.strip()
        else:
            result = "Transportation Information in Egypt:\n\n"
            
            # Major airports
            result += "Major Airports:\n"
            for airport in info.get("airports", [])[:3]:  # Show only top 3 airports
                name = airport.get("name", {}).get("en", "")
                code = airport.get("code", "")
                location = airport.get("location", "")
                
                result += f"- {name} ({code}) - {location}\n"
            result += "\n"
            
            # Domestic transportation
            result += "Intercity Transportation:\n"
            for transport in info.get("domestic", []):
                mode = transport.get("mode", {}).get("en", "")
                result += f"- {mode}\n"
            result += "\n"
            
            # Local transportation
            result += "Local Transportation:\n"
            for transport in info.get("local", []):
                mode = transport.get("mode", {}).get("en", "")
                result += f"- {mode}\n"
            
            return result.strip()
    
    def _generate_itinerary(self, template: str, context: Dict, language: str) -> str:
        """Generate itinerary text based on context."""
        # Extract parameters
        location = context.get("location", "")
        duration = context.get("duration", "")
        interests = context.get("interests", [])
        
        if not location or not duration:
            missing = []
            if not location:
                missing.append("location" if language == "en" else "الموقع")
            if not duration:
                missing.append("duration" if language == "en" else "المدة")
            
            missing_text = " and ".join(missing) if language == "en" else " و ".join(missing)
            return template.format(
                duration=duration or "?",
                location=location or "?",
                itinerary_details=f"(Missing {missing_text})" if language == "en" else f"({missing_text} مفقود)"
            )
        
        # Check for service results
        service_results = context.get("service_results", {})
        itinerary_result = service_results.get("itinerary_generate", {})
        
        if itinerary_result and "itinerary" in itinerary_result:
            # Use pre-generated itinerary from service
            itinerary_details = itinerary_result["itinerary"]
        else:
            # Generate simple itinerary based on location
            itinerary_details = self._generate_simple_itinerary(location, duration, interests, language)
        
        # Fill template
        return template.format(
            duration=duration,
            location=location,
            itinerary_details=itinerary_details
        )
    
    def _generate_simple_itinerary(self, location: str, duration: str, interests: List, language: str) -> str:
        """Generate a simple itinerary based on location, duration, and interests."""
        # Convert duration to integer days if possible
        try:
            days = int(duration.split()[0])
        except (ValueError, IndexError):
            days = 3  # Default to 3 days
        
        # Get attractions for the location
        attractions = self.knowledge_base.search_attractions(
            query="",
            filters={"location": location},
            language=language,
            limit=days * 2  # Get enough attractions for all days
        )
        
        # Get restaurants for the location
        restaurants = self.knowledge_base.search_restaurants(
            query="",
            filters={"location": location},
            language=language,
            limit=days  # One restaurant per day
        )
        
        # Create itinerary
        if language == "ar":
            itinerary = f"خطة سفر مقترحة لـ {days} يوم في {location}:\n\n"
            
            for day in range(1, days + 1):
                itinerary += f"اليوم {day}:\n"
                
                # Morning activity
                if day <= len(attractions):
                    attraction = attractions[day - 1]
                    name = attraction["name"].get("ar", attraction["name"].get("en", ""))
                    itinerary += f"صباحًا: زيارة {name}\n"
                
                # Lunch
                if day <= len(restaurants):
                    restaurant = restaurants[day - 1]
                    name = restaurant["name"].get("ar", restaurant["name"].get("en", ""))
                    itinerary += f"الغداء: {name}\n"
                
                # Afternoon activity
                if day + days <= len(attractions):
                    attraction = attractions[day + days - 1]
                    name = attraction["name"].get("ar", attraction["name"].get("en", ""))
                    itinerary += f"بعد الظهر: استكشاف {name}\n"
                
                itinerary += "\n"
        else:
            itinerary = f"Suggested {days}-day itinerary for {location}:\n\n"
            
            for day in range(1, days + 1):
                itinerary += f"Day {day}:\n"
                
                # Morning activity
                if day <= len(attractions):
                    attraction = attractions[day - 1]
                    name = attraction["name"].get("en", "")
                    itinerary += f"Morning: Visit {name}\n"
                
                # Lunch
                if day <= len(restaurants):
                    restaurant = restaurants[day - 1]
                    name = restaurant["name"].get("en", "")
                    itinerary += f"Lunch: {name}\n"
                
                # Afternoon activity
                if day + days <= len(attractions):
                    attraction = attractions[day + days - 1]
                    name = attraction["name"].get("en", "")
                    itinerary += f"Afternoon: Explore {name}\n"
                
                itinerary += "\n"
        
        return itinerary.strip()
    
    def _get_media_content(self, response_type: str, entities: Dict, language: str) -> Optional[List[Dict]]:
        """Get media content for the response if available."""
        media = []
        
        if response_type == "attraction_details":
            # Add attraction images
            attraction_entities = entities.get("attraction", [])
            if attraction_entities:
                attraction_entity = attraction_entities[0]["value"]
                attraction = self._lookup_attraction(attraction_entity, language)
                
                if attraction and "images" in attraction:
                    for image in attraction["images"]:
                        media.append({
                            "type": "image",
                            "url": image,
                            "alt_text": f"Image of {attraction_entity}"
                        })
        
        elif response_type == "restaurant_details":
            # Add restaurant images
            restaurant_entities = entities.get("restaurant", [])
            if restaurant_entities:
                restaurant_entity = restaurant_entities[0]["value"]
                restaurant = self._lookup_restaurant(restaurant_entity, language)
                
                if restaurant and "images" in restaurant:
                    for image in restaurant["images"]:
                        media.append({
                            "type": "image",
                            "url": image,
                            "alt_text": f"Image of {restaurant_entity}"
                        })
        
        elif response_type == "hotel_details":
            # Add hotel images
            hotel_entities = entities.get("hotel", [])
            if hotel_entities:
                hotel_entity = hotel_entities[0]["value"]
                hotel = self._lookup_hotel(hotel_entity, language)
                
                if hotel and "images" in hotel:
                    for image in hotel["images"]:
                        media.append({
                            "type": "image",
                            "url": image,
                            "alt_text": f"Image of {hotel_entity}"
                        })
        
        return media if media else None
    
    def _lookup_attraction(self, name: str, language: str) -> Optional[Dict]:
        """Look up an attraction by name."""
        if not name:
            logger.warning("Empty attraction name provided for lookup")
            return None
        
        try:
            # Try direct ID lookup first
            attraction = self.knowledge_base.get_attraction_by_id(name)
            if attraction:
                logger.debug(f"Found attraction by ID: {name}")
                return attraction
            
            # Try search by name
            logger.debug(f"Looking up attraction by name: {name}")
            return self.knowledge_base.lookup_attraction(name, language)
        except Exception as e:
            logger.error(f"Error looking up attraction '{name}': {str(e)}")
            return None
    
    def _lookup_restaurant(self, name: str, language: str) -> Optional[Dict]:
        """Look up a restaurant by name."""
        if not name:
            logger.warning("Empty restaurant name provided for lookup")
            return None
        
        try:
            # Try direct ID lookup first
            restaurant = self.knowledge_base.get_restaurant_by_id(name)
            if restaurant:
                logger.debug(f"Found restaurant by ID: {name}")
                return restaurant
            
            # Try search by name
            logger.debug(f"Looking up restaurant by name: {name}")
            restaurants = self.knowledge_base.search_restaurants(name, language=language, limit=1)
            return restaurants[0] if restaurants else None
        except Exception as e:
            logger.error(f"Error looking up restaurant '{name}': {str(e)}")
            return None
    
    def _lookup_hotel(self, name: str, language: str) -> Optional[Dict]:
        """Look up a hotel by name."""
        if not name:
            logger.warning("Empty hotel name provided for lookup")
            return None
        
        try:
            # Try direct ID lookup first
            hotel = self.knowledge_base.get_hotel_by_id(name)
            if hotel:
                logger.debug(f"Found hotel by ID: {name}")
                return hotel
            
            # Try search by name
            logger.debug(f"Looking up hotel by name: {name}")
            hotels = self.knowledge_base.search_hotels(name, language=language, limit=1)
            return hotels[0] if hotels else None
        except Exception as e:
            logger.error(f"Error looking up hotel '{name}': {str(e)}")
            return None