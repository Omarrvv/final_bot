"""
External Services Module

This module consolidates all external service integrations including:
- Weather service integration
- Translation service integration
- Other external API integrations

Replaces scattered services in src/integration/plugins/
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import logging
from datetime import datetime

from .base_service import BaseService

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """External service types."""
    WEATHER = "weather"
    TRANSLATION = "translation"
    CURRENCY = "currency"
    MAPS = "maps"


@dataclass
class ServiceResponse:
    """Standard response from external services."""
    success: bool
    data: Any
    error_message: Optional[str] = None
    service_type: Optional[str] = None
    response_time_ms: Optional[float] = None


class ExternalService(ABC):
    """Base class for external service integrations."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.timeout = config.get('timeout', 30)
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available."""
        pass
    
    @abstractmethod
    def get_service_type(self) -> ServiceType:
        """Get the service type."""
        pass


class WeatherService(ExternalService):
    """
    Weather service integration for tourism information.
    
    Provides weather data for Egyptian cities and tourist destinations.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config.get('weather_api_key') or config.get('api_key')
        self.base_url = config.get('base_url', 'http://api.openweathermap.org/data/2.5')
    
    def get_service_type(self) -> ServiceType:
        return ServiceType.WEATHER
    
    def is_available(self) -> bool:
        """Check if weather service is available."""
        return bool(self.api_key and self.enabled)
    
    def get_current_weather(self, location: str, language: str = "en") -> ServiceResponse:
        """
        Get current weather for a location.
        
        Args:
            location: City name or coordinates
            language: Language for weather description
            
        Returns:
            ServiceResponse with weather data
        """
        start_time = datetime.now()
        
        try:
            if not self.is_available():
                return ServiceResponse(
                    success=False,
                    data=None,
                    error_message="Weather service not available",
                    service_type="weather"
                )
            
            # Mock implementation for demo
            weather_data = self._get_mock_weather(location, "current")
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=True,
                data=weather_data,
                service_type="weather",
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Weather service error: {str(e)}")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=False,
                data=None,
                error_message=str(e),
                service_type="weather",
                response_time_ms=response_time
            )
    
    def get_forecast(self, location: str, days: int = 5, language: str = "en") -> ServiceResponse:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name or coordinates
            days: Number of forecast days
            language: Language for weather description
            
        Returns:
            ServiceResponse with forecast data
        """
        start_time = datetime.now()
        
        try:
            if not self.is_available():
                return ServiceResponse(
                    success=False,
                    data=None,
                    error_message="Weather service not available",
                    service_type="weather"
                )
            
            # Mock implementation for demo
            forecast_data = self._get_mock_weather(location, "forecast", days)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=True,
                data=forecast_data,
                service_type="weather",
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Weather forecast error: {str(e)}")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=False,
                data=None,
                error_message=str(e),
                service_type="weather",
                response_time_ms=response_time
            )
    
    def get_best_time_to_visit(self, location: str, language: str = "en") -> ServiceResponse:
        """
        Get best time to visit recommendation based on weather patterns.
        
        Args:
            location: City or destination name
            language: Language for recommendations
            
        Returns:
            ServiceResponse with travel recommendations
        """
        start_time = datetime.now()
        
        try:
            # Mock implementation with Egyptian tourism knowledge
            recommendations = self._get_travel_recommendations(location, language)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=True,
                data=recommendations,
                service_type="weather",
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Travel recommendation error: {str(e)}")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=False,
                data=None,
                error_message=str(e),
                service_type="weather",
                response_time_ms=response_time
            )
    
    def _get_mock_weather(self, location: str, weather_type: str, days: int = 1) -> Dict[str, Any]:
        """Generate mock weather data for testing."""
        if weather_type == "current":
            return {
                "location": location,
                "temperature": 28,
                "humidity": 45,
                "description": "Sunny",
                "wind_speed": 12,
                "visibility": "Good"
            }
        else:  # forecast
            forecast = []
            for i in range(days):
                forecast.append({
                    "date": (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat(),
                    "temperature_high": 30 + i,
                    "temperature_low": 18 + i,
                    "description": "Sunny" if i % 2 == 0 else "Partly Cloudy",
                    "humidity": 40 + i * 2
                })
            return {"location": location, "forecast": forecast}
    
    def _get_travel_recommendations(self, location: str, language: str) -> Dict[str, Any]:
        """Generate travel recommendations based on location."""
        # Simplified recommendations for Egyptian destinations
        recommendations = {
            "en": {
                "best_months": ["October", "November", "December", "January", "February", "March"],
                "avoid_months": ["June", "July", "August"],
                "notes": "Egypt has a desert climate with mild winters and hot summers. The best time to visit is during the cooler months."
            },
            "ar": {
                "best_months": ["أكتوبر", "نوفمبر", "ديسمبر", "يناير", "فبراير", "مارس"],
                "avoid_months": ["يونيو", "يوليو", "أغسطس"],
                "notes": "مصر لديها مناخ صحراوي مع شتاء معتدل وصيف حار. أفضل وقت للزيارة هو خلال الأشهر الباردة."
            }
        }
        
        return recommendations.get(language, recommendations["en"])


class TranslationService(ExternalService):
    """
    Translation service integration for multi-language support.
    
    Provides text translation capabilities for tourism content.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config.get('translation_api_key') or config.get('api_key')
        self.supported_languages = config.get('supported_languages', ['en', 'ar'])
    
    def get_service_type(self) -> ServiceType:
        return ServiceType.TRANSLATION
    
    def is_available(self) -> bool:
        """Check if translation service is available."""
        return bool(self.api_key and self.enabled)
    
    def translate(self, text: Union[str, List[str]], target_language: str, 
                 source_language: Optional[str] = None) -> ServiceResponse:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate (string or list of strings)
            target_language: Target language code
            source_language: Source language code (optional, auto-detect if None)
            
        Returns:
            ServiceResponse with translated text
        """
        start_time = datetime.now()
        
        try:
            if not self.is_available():
                return ServiceResponse(
                    success=False,
                    data=None,
                    error_message="Translation service not available",
                    service_type="translation"
                )
            
            # Mock implementation for demo
            if isinstance(text, str):
                translated_text = self._mock_translate(text, target_language)
                result = {"translated_text": translated_text, "source_language": source_language or "auto"}
            else:
                translated_texts = [self._mock_translate(t, target_language) for t in text]
                result = {"translated_texts": translated_texts, "source_language": source_language or "auto"}
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=True,
                data=result,
                service_type="translation",
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Translation service error: {str(e)}")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=False,
                data=None,
                error_message=str(e),
                service_type="translation",
                response_time_ms=response_time
            )
    
    def detect_language(self, text: Union[str, List[str]]) -> ServiceResponse:
        """
        Detect the language of the given text.
        
        Args:
            text: Text to analyze (string or list of strings)
            
        Returns:
            ServiceResponse with detected language information
        """
        start_time = datetime.now()
        
        try:
            if not self.is_available():
                return ServiceResponse(
                    success=False,
                    data=None,
                    error_message="Translation service not available",
                    service_type="translation"
                )
            
            # Mock implementation for demo
            if isinstance(text, str):
                detected = self._mock_detect_language(text)
                result = {"language": detected["language"], "confidence": detected["confidence"]}
            else:
                detections = [self._mock_detect_language(t) for t in text]
                result = {"detections": detections}
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=True,
                data=result,
                service_type="translation",
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                success=False,
                data=None,
                error_message=str(e),
                service_type="translation",
                response_time_ms=response_time
            )
    
    def get_supported_languages(self) -> ServiceResponse:
        """Get list of supported languages."""
        return ServiceResponse(
            success=True,
            data={"languages": self.supported_languages},
            service_type="translation"
        )
    
    def _mock_translate(self, text: str, target_language: str) -> str:
        """Mock translation for testing."""
        if target_language == "ar" and "egypt" in text.lower():
            return "مصر"
        elif target_language == "en" and "مصر" in text:
            return "Egypt"
        else:
            return f"[Translated to {target_language}] {text}"
    
    def _mock_detect_language(self, text: str) -> Dict[str, Any]:
        """Mock language detection for testing."""
        # Simple heuristic: check for Arabic characters
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return {"language": "ar", "confidence": 0.95}
        else:
            return {"language": "en", "confidence": 0.90}


class ExternalServicesManager(BaseService):
    """
    Unified manager for all external service integrations.
    
    This service consolidates and manages:
    - Weather service integration
    - Translation service integration  
    - Other external API services
    
    Replaces scattered integration/plugins services.
    """
    
    def __init__(self, db_manager=None, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_manager)
        self.config = config or {}
        self.services: Dict[str, ExternalService] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize external services based on configuration."""
        try:
            # Initialize weather service
            weather_config = self.config.get('weather', {})
            if weather_config.get('enabled', True):
                self.services['weather'] = WeatherService('weather', weather_config)
            
            # Initialize translation service
            translation_config = self.config.get('translation', {})
            if translation_config.get('enabled', True):
                self.services['translation'] = TranslationService('translation', translation_config)
            
            logger.info(f"Initialized {len(self.services)} external services")
            
        except Exception as e:
            logger.error(f"Error initializing external services: {str(e)}")
    
    def get_weather(self, location: str, language: str = "en") -> ServiceResponse:
        """Get current weather for a location."""
        weather_service = self.services.get('weather')
        if not weather_service:
            return ServiceResponse(
                success=False,
                data=None,
                error_message="Weather service not configured",
                service_type="weather"
            )
        
        return weather_service.get_current_weather(location, language)
    
    def get_forecast(self, location: str, days: int = 5, language: str = "en") -> ServiceResponse:
        """Get weather forecast for a location."""
        weather_service = self.services.get('weather')
        if not weather_service:
            return ServiceResponse(
                success=False,
                data=None,
                error_message="Weather service not configured",
                service_type="weather"
            )
        
        return weather_service.get_forecast(location, days, language)
    
    def get_travel_recommendations(self, location: str, language: str = "en") -> ServiceResponse:
        """Get best time to visit recommendations."""
        weather_service = self.services.get('weather')
        if not weather_service:
            return ServiceResponse(
                success=False,
                data=None,
                error_message="Weather service not configured",
                service_type="weather"
            )
        
        return weather_service.get_best_time_to_visit(location, language)
    
    def translate_text(self, text: Union[str, List[str]], target_language: str,
                      source_language: Optional[str] = None) -> ServiceResponse:
        """Translate text to target language."""
        translation_service = self.services.get('translation')
        if not translation_service:
            return ServiceResponse(
                success=False,
                data=None,
                error_message="Translation service not configured",
                service_type="translation"
            )
        
        return translation_service.translate(text, target_language, source_language)
    
    def detect_language(self, text: Union[str, List[str]]) -> ServiceResponse:
        """Detect language of text."""
        translation_service = self.services.get('translation')
        if not translation_service:
            return ServiceResponse(
                success=False,
                data=None,
                error_message="Translation service not configured",
                service_type="translation"
            )
        
        return translation_service.detect_language(text)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all external services."""
        status = {
            "services": {},
            "total_services": len(self.services),
            "available_services": 0
        }
        
        for name, service in self.services.items():
            service_status = {
                "name": name,
                "type": service.get_service_type().value,
                "available": service.is_available(),
                "enabled": service.enabled
            }
            status["services"][name] = service_status
            
            if service.is_available():
                status["available_services"] += 1
        
        return status
    
    def get_service(self, service_name: str) -> Optional[ExternalService]:
        """Get a specific external service."""
        return self.services.get(service_name)
    
    def get_available_services(self) -> List[str]:
        """Get list of available service names."""
        return [name for name, service in self.services.items() if service.is_available()] 