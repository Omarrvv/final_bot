# src/nlu/language.py
"""
Language detection module for the Egypt Tourism Chatbot.
"""
import os
import logging
import warnings
from typing import Tuple, Optional
import fasttext
import requests
from pathlib import Path

# Suppress NumPy 2.0 warnings from fasttext
warnings.filterwarnings("ignore", message="Unable to avoid copy while creating an array")
warnings.filterwarnings("ignore", category=FutureWarning, module="numpy")

logger = logging.getLogger(__name__)

class LanguageDetector:
    """
    Detects the language of input text.
    Supports English, Modern Standard Arabic, and Egyptian Arabic dialect.
    """
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.8):
        """
        Initialize language detector with the specified model.
        
        Args:
            model_path (str): Path to the FastText language detection model
            confidence_threshold (float): Threshold for language detection confidence
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self._load_model()
        
        # Egyptian Arabic patterns for dialect detection
        self.egyptian_patterns = [
            "إزي", "إزيك", "عايز", "دلوقتي", "فين", "إيه", "ازاي",
            "كدة", "بتاع", "مفيش", "طب", "يلا", "انا", "خالص"
        ]
        
        logger.info("Language detector initialized")
    
    def _load_model(self):
        """Load the FastText language detection model."""
        try:
            model_file = Path(self.model_path)
            
            # Download model if not exists
            if not model_file.exists():
                logger.info(f"Downloading language detection model to {model_file}")
                os.makedirs(model_file.parent, exist_ok=True)
                
                # Download from FastText
                url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
                response = requests.get(url)
                with open(model_file, 'wb') as f:
                    f.write(response.content)
            
            self.model = fasttext.load_model(str(model_file))
            logger.info("Successfully loaded language detection model")
        except Exception as e:
            logger.error(f"Failed to load language detection model: {str(e)}")
            # Create a fallback classifier function if model loading fails
            logger.warning("Using fallback language detection (basic pattern matching)")
            self.model = None
    
    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the given text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            tuple: (language_code, confidence_score)
        """
        if not text or len(text.strip()) < 2:
            return "en", 1.0  # Default to English for very short text
        
        # Use FastText model if available
        if self.model:
            try:
                predictions = self.model.predict(text, k=3)
                languages = [lang.replace('__label__', '') for lang in predictions[0]]
                confidences = predictions[1]
                
                primary_lang = languages[0]
                confidence = confidences[0]
                
                # Check if Arabic is detected
                if primary_lang == 'ar' or ('ar' in languages and confidences[languages.index('ar')] > 0.5):
                    # Check for Egyptian dialect if Arabic detected
                    if self._is_egyptian_dialect(text):
                        return "ar_eg", confidence
                    return "ar", confidence
                
                return primary_lang, confidence
            except Exception as e:
                logger.error(f"Language detection error: {str(e)}")
        
        # Fallback detection if model not available or error occurs
        return self._fallback_detect(text)
    
    def _is_egyptian_dialect(self, text: str) -> bool:
        """
        Check if text contains Egyptian Arabic dialect markers.
        
        Args:
            text (str): Arabic text to check
            
        Returns:
            bool: True if Egyptian dialect detected
        """
        # Count Egyptian dialect markers
        count = sum(1 for pattern in self.egyptian_patterns if pattern in text)
        
        # If more than 2 patterns or more than 10% of words are dialect markers
        words = text.split()
        return count >= 2 or (len(words) > 0 and count / len(words) >= 0.1)
    
    def _fallback_detect(self, text: str) -> Tuple[str, float]:
        """
        Fallback language detection using simple pattern matching.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            tuple: (language_code, confidence_score)
        """
        # Check for Arabic script (Unicode ranges)
        arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        
        if arabic_count > len(text) * 0.5:
            # Check for Egyptian dialect
            if self._is_egyptian_dialect(text):
                return "ar_eg", 0.7
            return "ar", 0.8
        
        # Default to English
        return "en", 0.6