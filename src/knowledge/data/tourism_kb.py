"""
Egypt Tourism Knowledge Base.
Structured information about Egyptian tourism, organized by categories.
"""
from typing import Dict, Any

class TourismKnowledgeBase:
    def __init__(self):
        self._data = {
            "general": self._load_general_info(),
            "attractions": self._load_attractions(),
            "cuisine": self._load_cuisine(),
            "travel_tips": self._load_travel_tips()
        }
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get information for a specific category."""
        return self._data.get(category, {})
    
    def get_topic(self, category: str, topic: str) -> str:
        """Get specific topic information within a category."""
        return self._data.get(category, {}).get(topic, "")
    
    @staticmethod
    def _load_general_info() -> Dict[str, str]:
        return {
            "greeting": "Welcome to Egypt! I'm your virtual guide to the land of the pharaohs. How can I help you today?",
            "about": "Egypt is a country in North Africa with a history spanning over 5000 years. Home to ancient wonders like the pyramids and temples, as well as beautiful beaches along the Red Sea.",
            "best_time": "The best time to visit Egypt is from October to April when the temperature is cooler. Summer months (June-August) can be extremely hot, especially in Upper Egypt."
        }
    
    @staticmethod
    def _load_attractions() -> Dict[str, str]:
        return {
            "pyramids": "The Pyramids of Giza are Egypt's most iconic monuments, built over 4,500 years ago as tombs for the pharaohs.",
            "luxor": "Luxor is home to the Valley of the Kings and the magnificent Karnak Temple complex.",
            "alexandria": "Alexandria, founded by Alexander the Great, features the modern Library of Alexandria and ancient Roman ruins."
        }
    
    @staticmethod
    def _load_cuisine() -> Dict[str, str]:
        return {
            "general": "Egyptian cuisine offers flavorful dishes with influences from the Mediterranean, Middle East, and North Africa.",
            "koshari": "Koshari is Egypt's national dish, a comforting mix of rice, lentils, pasta, chickpeas, topped with crispy fried onions and tangy tomato sauce.",
            "ful_medames": "Ful Medames is a staple Egyptian breakfast dish made of slow-cooked fava beans seasoned with olive oil, lemon juice, and cumin."
        }
    
    @staticmethod
    def _load_travel_tips() -> Dict[str, str]:
        return {
            "safety": "Egypt is generally safe for tourists. Stay aware of your surroundings and follow local customs and advice.",
            "transportation": "Major cities are connected by flights and trains. Within cities, use official taxis or ride-sharing apps.",
            "currency": "The Egyptian Pound (EGP) is the local currency. Major hotels and restaurants accept credit cards."
        }
