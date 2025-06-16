# src/nlu/language.py
"""
Language detection module for the Egypt Tourism Chatbot.
"""
import os
import logging
import warnings
from typing import Tuple, Optional
import requests
from pathlib import Path

# CRITICAL FIX: Use langdetect instead of FastText for NumPy 2.0 compatibility
try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    import fasttext
    # Suppress NumPy 2.0 warnings from fasttext only if we need to use it
    warnings.filterwarnings("ignore", message="Unable to avoid copy while creating an array")
    warnings.filterwarnings("ignore", message=".*copy.*", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*copy.*", category=FutureWarning)
    warnings.filterwarnings("ignore", category=FutureWarning, module="numpy")
    warnings.filterwarnings("ignore", category=UserWarning, module="fasttext")
    warnings.filterwarnings("ignore", message=".*numpy_2_0_migration_guide.*")
    warnings.filterwarnings("ignore", message=".*adapting-to-changes-in-the-copy-keyword.*")

logger = logging.getLogger(__name__)

class LanguageDetector:
    """
    Detects the language of input text.
    Supports English, Modern Standard Arabic, and Egyptian Arabic dialect.
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.8):
        """
        Initialize language detector with the specified model.

        Args:
            model_path (str, optional): Path to the FastText language detection model
            confidence_threshold (float): Threshold for language detection confidence
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None

        # CRITICAL FIX: Define supported language codes for Egypt Tourism
        self.supported_languages = ["en", "ar", "ar_eg"]

        # Egyptian Arabic patterns for dialect detection (enhanced)
        self.egyptian_patterns = [
            "إزي", "إزيك", "عايز", "دلوقتي", "فين", "إيه", "ازاي",
            "كدة", "بتاع", "مفيش", "طب", "يلا", "انا", "خالص",
            "عشان", "لسه", "هو", "هي", "احنا", "انتو", "هما",
            "بقى", "كمان", "برضو", "علطول", "خلاص", "ماشي"
        ]

        self._load_model()
        logger.info(f"✅ Language detector initialized (Model: {'Loaded' if self.model else 'Fallback'})")
    
    def _load_model(self):
        """Load language detection model - using langdetect for NumPy 2.0 compatibility."""
        try:
            if LANGDETECT_AVAILABLE:
                # Use langdetect - no model file needed, built-in language detection
                self.model = "langdetect"  # Flag to indicate langdetect is available
                logger.info("✅ Using langdetect for language detection (NumPy 2.0 compatible)")
                return

            # Fallback to FastText if langdetect not available
            logger.warning("langdetect not available, falling back to FastText")

            # CRITICAL FIX: Handle None model_path and resolve absolute path
            if self.model_path is None:
                logger.warning("Model path is None, using fallback language detection")
                self.model = None
                return

            # Resolve absolute path from project root
            if not os.path.isabs(self.model_path):
                # Get project root (assuming this file is in src/nlu/)
                project_root = Path(__file__).parent.parent.parent
                model_file = project_root / self.model_path
            else:
                model_file = Path(self.model_path)

            logger.info(f"Loading FastText model from: {model_file}")

            # Download model if not exists
            if not model_file.exists():
                logger.info(f"Downloading language detection model to {model_file}")
                os.makedirs(model_file.parent, exist_ok=True)

                # Download from FastText
                url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
                response = requests.get(url)
                with open(model_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded language detection model to {model_file}")

            self.model = fasttext.load_model(str(model_file))
            logger.info("✅ Successfully loaded FastText language detection model")
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

        # CRITICAL FIX: Use langdetect if available (NumPy 2.0 compatible)
        if self.model == "langdetect" and LANGDETECT_AVAILABLE:
            try:
                # Use langdetect for clean, warning-free detection
                detected_lang = detect(text)

                # Get confidence using detect_langs
                lang_probs = detect_langs(text)
                confidence = max(prob.prob for prob in lang_probs if prob.lang == detected_lang)

                # Normalize language code and handle Arabic variants
                if detected_lang == 'ar':
                    if self._is_egyptian_dialect(text):
                        return "ar_eg", confidence
                    return "ar", confidence
                elif detected_lang == 'en':
                    return "en", confidence
                else:
                    # For other languages, check if it's Arabic script
                    if self._contains_arabic_script(text):
                        if self._is_egyptian_dialect(text):
                            return "ar_eg", 0.7
                        return "ar", 0.8
                    return "en", confidence

            except (LangDetectException, Exception) as e:
                logger.debug(f"langdetect failed: {e}, falling back to pattern matching")
                return self._fallback_detect(text)

        # Use FastText model if available (with warning suppression)
        elif self.model and self.model != "langdetect":
            try:
                # Comprehensive warning suppression for FastText
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    warnings.filterwarnings("ignore", message="Unable to avoid copy while creating an array")
                    warnings.filterwarnings("ignore", message=".*copy.*")
                    warnings.filterwarnings("ignore", message=".*numpy_2_0_migration_guide.*")
                    warnings.filterwarnings("ignore", category=UserWarning)
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    predictions = self.model.predict(text, k=3)

                languages = [lang.replace('__label__', '') for lang in predictions[0]]
                confidences = predictions[1]

                primary_lang = languages[0]
                confidence = confidences[0]

                # Enhanced Arabic detection and normalization
                detected_lang, final_confidence = self._normalize_language_code(
                    primary_lang, confidence, languages, confidences, text
                )

                logger.debug(f"Language detected: {detected_lang} ({final_confidence:.3f}) for text: '{text[:50]}...'")
                return detected_lang, final_confidence

            except Exception as e:
                logger.error(f"FastText language detection error: {str(e)}")

        # Fallback detection if model not available or error occurs
        return self._fallback_detect(text)

    def _normalize_language_code(self, primary_lang: str, confidence: float,
                                languages: list, confidences: list, text: str) -> Tuple[str, float]:
        """
        Normalize language codes to supported formats for Egypt Tourism.

        Args:
            primary_lang: Primary detected language
            confidence: Detection confidence
            languages: All detected languages
            confidences: All confidence scores
            text: Original text

        Returns:
            tuple: (normalized_language_code, confidence)
        """
        # Check if Arabic is detected (primary or secondary)
        if primary_lang == 'ar' or ('ar' in languages and confidences[languages.index('ar')] > 0.5):
            # Check for Egyptian dialect if Arabic detected
            if self._is_egyptian_dialect(text):
                return "ar_eg", confidence
            return "ar", confidence

        # Handle other Arabic variants
        if primary_lang in ['ar-eg', 'ar_EG', 'arz']:  # Egyptian Arabic variants
            return "ar_eg", confidence

        # Normalize to supported languages
        if primary_lang in self.supported_languages:
            return primary_lang, confidence

        # Default fallback based on script detection
        if self._contains_arabic_script(text):
            if self._is_egyptian_dialect(text):
                return "ar_eg", 0.7
            return "ar", 0.8

        return "en", confidence
    
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
    
    def _contains_arabic_script(self, text: str) -> bool:
        """
        Check if text contains Arabic script characters.

        Args:
            text (str): Text to analyze

        Returns:
            bool: True if Arabic script detected
        """
        arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        return arabic_count > len(text) * 0.3  # More lenient threshold

    def _fallback_detect(self, text: str) -> Tuple[str, float]:
        """
        Enhanced fallback language detection using pattern matching and script analysis.

        Args:
            text (str): Text to analyze

        Returns:
            tuple: (language_code, confidence_score)
        """
        logger.debug(f"Using fallback detection for: '{text[:50]}...'")

        # Check for Arabic script (Unicode ranges)
        if self._contains_arabic_script(text):
            # Check for Egyptian dialect
            if self._is_egyptian_dialect(text):
                logger.debug("Detected Egyptian Arabic dialect in fallback")
                return "ar_eg", 0.7
            logger.debug("Detected Standard Arabic in fallback")
            return "ar", 0.8

        # Check for common English patterns
        english_patterns = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'was', 'on', 'are']
        text_lower = text.lower()
        english_matches = sum(1 for pattern in english_patterns if pattern in text_lower)

        if english_matches > 0:
            confidence = min(0.6 + (english_matches * 0.1), 0.9)
            logger.debug(f"Detected English in fallback (confidence: {confidence:.3f})")
            return "en", confidence

        # Default to English with low confidence
        logger.debug("Defaulting to English in fallback")
        return "en", 0.5