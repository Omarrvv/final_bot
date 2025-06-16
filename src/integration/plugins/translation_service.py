# src/integration/plugins/translation_service.py
"""
Translation service plugin for the Egypt Tourism Chatbot.
Provides text translation functionality using external translation APIs.
"""
import logging
import os
from typing import Dict, List, Optional, Any

# Make google.cloud import optional to avoid external dependency failures
try:
    from google.cloud import translate_v2 as translate # Import Google client
    from google.api_core.exceptions import GoogleAPICallError, Forbidden
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    translate = None
    GoogleAPICallError = Exception
    Forbidden = Exception

from src.integration.service_hub import Service

logger = logging.getLogger(__name__)

class TranslationService(Service):
    """
    Translation service implementation.
    Provides text translation between languages.
    """
    
    def __init__(self, name: str, config: Dict):
        """
        Initialize the translation service.
        
        Args:
            name (str): Service name
            config (dict): Service configuration
        """
        super().__init__(name, config)
        self.config = config or {}
        self.api_key = self.config.get("api_key") or os.getenv("TRANSLATION_API_KEY")
        # Project ID might be needed for some auth methods, but API key usually sufficient for translate
        self.project_id = self.config.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT") 
        self.cache_ttl = self.config.get("cache_ttl", 86400) # Default to 1 day
        self.client = None
        self.initialized = False
        
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.warning("TranslationService: Google Cloud libraries not available. Service will work in fallback mode.")
            self.client = None
            self.initialized = False
        elif not self.api_key:
            logger.warning("TranslationService: TRANSLATION_API_KEY not found in config or environment. Service will not function.")
            self.client = None
            self.initialized = False
        else:
            try:
                # Initialize the client using the API key
                # Note: For production on GCP, Application Default Credentials (ADC)
                # or a Service Account key file might be preferred over an API key.
                # Using API key directly is simpler for local dev where ADC isn't set up.
                self.client = translate.Client(target_language='en', client_options={'api_key': self.api_key})
                # Perform a simple test call to verify connection/auth
                self.client.detect_language(["test"])
                self.initialized = True
                logger.info("TranslationService initialized successfully with Google Cloud Translate.")
            except Forbidden as e:
                 logger.error(f"TranslationService Init Failed: Permission denied. Ensure API key is valid, has Translation API enabled, and billing might be required. Error: {e}")
                 self.client = None # Ensure client is None if init fails
                 self.initialized = False
            except Exception as e:
                logger.error(f"TranslationService Init Failed: Could not initialize Google Translate client. Error: {e}", exc_info=True)
                self.client = None # Ensure client is None if init fails
                self.initialized = False
        
        # Define supported languages
        self.supported_languages = {
            "en": "English",
            "ar": "Arabic",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
            "zh": "Chinese (Simplified)",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean"
        }
    
    def get_type(self) -> str:
        """Get the service type."""
        return "translation"
    
    def _is_ready(self) -> bool:
        """Check if the service is initialized and ready."""
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.debug("Google Cloud libraries not available, translation service disabled.")
            return False
        if not self.initialized or not self.client:
            logger.error("TranslationService called but not initialized properly (check API key and configuration).")
            return False
        return True

    def translate(self, text: str | List[str], target_language: str, source_language: Optional[str] = None) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
        """
        Translate text to the target language.

        Args:
            text (str or list): Text or list of texts to translate.
            target_language (str): Target language code (e.g., 'en', 'ar').
            source_language (str, optional): Source language code. If None, detects automatically.

        Returns:
            Dict or List[Dict]: Translation result(s) or None if error.
            Each result dict contains: 'translatedText', 'detectedSourceLanguage', 'input'.
        """
        if not self._is_ready():
            return None
            
        try:
            logger.debug(f"Translating to {target_language}. Source: {source_language or 'auto'}. Text: {str(text)[:50]}...")
            # client.translate expects a list or a single string
            result = self.client.translate(
                text,
                target_language=target_language,
                source_language=source_language # Pass None for auto-detect
            )
            logger.debug(f"Google Translate API result: {result}")
            # The result structure is slightly different for single vs list input
            # We want to return a consistent structure if possible, mirroring the API
            return result
        except GoogleAPICallError as e:
            logger.error(f"Google Translate API error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error during translation: {e}", exc_info=True)
            return None

    def detect_language(self, text: str | List[str]) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
        """
        Detect the language of the text.

        Args:
            text (str or list): Text or list of texts to detect language for.

        Returns:
            Dict or List[Dict]: Detection result(s) or None if error.
            Each result dict contains: 'language', 'confidence', 'input'.
        """
        if not self._is_ready():
            return None
            
        try:
            logger.debug(f"Detecting language for text: {str(text)[:50]}...")
            result = self.client.detect_language(text)
            logger.debug(f"Google Detect Language API result: {result}")
            return result
        except GoogleAPICallError as e:
            logger.error(f"Google Detect Language API error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error during language detection: {e}", exc_info=True)
            return None

    def get_supported_languages(self) -> Dict:
        """
        Get a list of supported languages.
        
        Returns:
            dict: Supported languages
        """
        return {
            "languages": [
                {"code": code, "name": name}
                for code, name in self.supported_languages.items()
            ]
        }