"""
Tests for the NLU engine.
"""
import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# Import test framework
from tests.test_framework import BaseTestCase, MockKnowledgeBase

# Import modules to test
from src.nlu.engine import NLUEngine
from src.nlu.intent import IntentClassifier
from src.nlu.entity import EntityExtractor
from src.nlu.language import LanguageDetector

class TestLanguageDetector(BaseTestCase):
    """Tests for the language detector."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Mock the fasttext model
        self.fasttext_patcher = patch('src.nlu.language.fasttext')
        self.mock_fasttext = self.fasttext_patcher.start()
        
        # Set up mock model
        self.mock_model = MagicMock()
        self.mock_fasttext.load_model.return_value = self.mock_model
        
        # Create language detector
        self.detector = LanguageDetector(model_path="dummy_path.bin")
    
    def tearDown(self):
        """Clean up after tests."""
        self.fasttext_patcher.stop()
        super().tearDown()
    
    def test_detect_english(self):
        """Test detecting English text."""
        # Set up mock model response
        self.mock_model.predict.return_value = (["__label__en"], [0.95])
        
        # Test detection
        language, confidence = self.detector.detect("Hello, how are you?")
        
        # Verify results
        self.assertEqual(language, "en")
        self.assertAlmostEqual(confidence, 0.95)
        
        # Verify model was called
        self.mock_model.predict.assert_called_once_with("Hello, how are you?", k=3)
    
    def test_detect_arabic(self):
        """Test detecting Arabic text."""
        # Set up mock model response
        self.mock_model.predict.return_value = (["__label__ar"], [0.98])
        
        # Test detection
        language, confidence = self.detector.detect("مرحبا، كيف حالك؟")
        
        # Verify results
        self.assertEqual(language, "ar")
        self.assertAlmostEqual(confidence, 0.98)
        
        # Verify model was called
        self.mock_model.predict.assert_called_once_with("مرحبا، كيف حالك؟", k=3)
    
    def test_detect_egyptian_dialect(self):
        """Test detecting Egyptian Arabic dialect."""
        # Set up mock model response
        self.mock_model.predict.return_value = (["__label__ar"], [0.98])
        
        # Mock the dialect detection method
        original_is_egyptian = self.detector._is_egyptian_dialect
        self.detector._is_egyptian_dialect = MagicMock(return_value=True)
        
        # Test detection
        language, confidence = self.detector.detect("إزيك عامل إيه؟")
        
        # Verify results
        self.assertEqual(language, "ar_eg")
        self.assertAlmostEqual(confidence, 0.98)
        
        # Restore original method
        self.detector._is_egyptian_dialect = original_is_egyptian
    
    def test_fallback_detection(self):
        """Test fallback detection when model is not available."""
        # Simulate model not available
        self.detector.model = None
        
        # Test English detection
        language, confidence = self.detector.detect("Hello, how are you?")
        self.assertEqual(language, "en")
        
        # Test Arabic detection
        language, confidence = self.detector.detect("مرحبا، كيف حالك؟")
        self.assertEqual(language, "ar")
    
    def test_is_egyptian_dialect(self):
        """Test Egyptian dialect detection."""
        # Test text with Egyptian dialect markers
        self.assertTrue(self.detector._is_egyptian_dialect("إزيك عامل إيه دلوقتي"))
        
        # Test text without Egyptian dialect markers
        self.assertFalse(self.detector._is_egyptian_dialect("مرحبا كيف حالك"))


class TestIntentClassifier(BaseTestCase):
    """Tests for the intent classifier."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Create mock embedding model that returns different vectors
        def mock_embedding_model(texts, language=None):
            embeddings = []
            # Ensure input is a list
            if isinstance(texts, str):
                texts = [texts]
            for text in texts:
                # Generate a simple deterministic vector based on text hash
                # Normalize to simulate unit vectors used in cosine similarity
                hash_val = hash(text)
                vec = np.array([hash_val % 100 / 100.0, 
                                (hash_val >> 8) % 100 / 100.0, 
                                (hash_val >> 16) % 100 / 100.0]) # Simple 3D vector
                norm = np.linalg.norm(vec)
                if norm == 0:
                     norm = 1 # Avoid division by zero
                normalized_vec = vec / norm
                embeddings.append(normalized_vec)
            # Return as a 2D numpy array [n_texts, embedding_dim]
            return np.array(embeddings)
        
        # Create mock knowledge base
        self.knowledge_base = MockKnowledgeBase()
        
        # Create intent classifier with mocked embedding model
        self.classifier = IntentClassifier(
            config={"intents_file": os.path.join(self.temp_dir, "configs", "intents.json")},
            embedding_model=mock_embedding_model,
            knowledge_base=self.knowledge_base
        )
    
    def test_load_intents(self):
        """Test loading intents from file."""
        # Verify intents were loaded
        self.assertIn("greeting", self.classifier.intents)
        self.assertIn("farewell", self.classifier.intents)
        self.assertIn("attraction_info", self.classifier.intents)
    
    @patch('src.nlu.intent.cosine_similarity') # Patch cosine_similarity for precise control
    def test_classify_greeting(self, mock_cosine_similarity):
        """Test classifying a greeting message."""
        # Store the original mock embedding function from setUp
        original_embedding_model = self.classifier.embedding_model
        
        # --- Mock cosine_similarity setup (as before) ---
        def side_effect_func(embedding1, embedding2):
            example_hash = hash(self.classifier.intent_examples["greeting"][0]) # Hash of first greeting example
            example_vec_hash = np.array([example_hash % 100 / 100.0, (example_hash >> 8) % 100 / 100.0, (example_hash >> 16) % 100 / 100.0])
            norm = np.linalg.norm(example_vec_hash)
            if norm == 0: norm = 1
            normalized_example_vec_hash = example_vec_hash / norm
            if np.allclose(embedding2[0], normalized_example_vec_hash): 
                return np.array([[0.9]])
            else:
                return np.array([[0.6]])
        mock_cosine_similarity.side_effect = side_effect_func

        # --- Mock embedding generation for the specific input "hello there" ---
        input_hash = hash("hello there")
        input_vec = np.array([input_hash % 100 / 100.0, (input_hash >> 8) % 100 / 100.0, (input_hash >> 16) % 100 / 100.0])
        input_norm = np.linalg.norm(input_vec)
        if input_norm == 0: input_norm = 1
        normalized_input_vec = input_vec / input_norm
        
        # --- Define a side_effect for the embedding_model patch ---
        def embedding_side_effect(texts, language=None):
            if texts == ["hello there"]:
                # Return the precalculated embedding for the input
                return np.array([normalized_input_vec]) 
            else:
                # For intent examples, call the ORIGINAL mock function
                return original_embedding_model(texts, language=language)

        # --- Patch the classifier's embedding_model for this specific test ---
        with patch.object(self.classifier, 'embedding_model', side_effect=embedding_side_effect) as mock_emb_call:
            result = self.classifier.classify("hello there", language="en")

        # --- Assertions (as before) ---
        self.assertEqual(result["intent"], "greeting")
        self.assertAlmostEqual(result["confidence"], 0.9) 
        mock_cosine_similarity.assert_called()
    
    def test_classify_farewell(self):
        """Test classifying a farewell message."""
        result = self.classifier.classify("goodbye", language="en")
        
        self.assertEqual(result["intent"], "farewell")
        self.assertGreater(result["confidence"], 0.5)
    
    def test_classify_attraction_info(self):
        """Test classifying an attraction info message."""
        result = self.classifier.classify("tell me about the pyramids", language="en")
        
        self.assertEqual(result["intent"], "attraction_info")
        self.assertGreater(result["confidence"], 0.5)
    
    def test_classify_with_pattern(self):
        """Test classifying using regex patterns."""
        # Add regex patterns to intents
        self.classifier.intents["test_pattern"] = {
            "patterns": [r"test\s+pattern"],
            "responses": ["test_pattern"]
        }
        
        # Compile regex patterns
        self.classifier.regex_patterns = self.classifier._compile_regex_patterns()
        
        # Test classification with pattern
        result = self.classifier.classify("this is a test pattern message", language="en")
        
        self.assertEqual(result["intent"], "test_pattern")
        self.assertGreater(result["confidence"], 0.9)
    
    def test_apply_context(self):
        """Test applying conversation context to intent classification."""
        # Create a context with previous intent
        context = {
            "last_intent": "attraction_info",
            "entities": {
                "attraction": [{"value": "pyramids", "confidence": 0.9}]
            }
        }
        
        # Create a follow-up question result
        follow_up_result = {
            "intent": "general_query",
            "confidence": 0.4,
            "match_type": "similarity",
            "metadata": {
                "top_examples": [("tell me more", 0.4)]
            }
        }
        
        # Apply context
        result = self.classifier._apply_context(follow_up_result, context)
        
        # Verify intent was adjusted based on context
        self.assertEqual(result["intent"], "attraction_info")
        self.assertGreater(result["confidence"], 0.4)


class TestEntityExtractor(BaseTestCase):
    """Tests for the entity extractor."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up mock model that behaves like a SpaCy model
        self.mock_nlp_model = MagicMock()
        
        # Mock NER results
        self.mock_doc = MagicMock()
        # Adjust mock entity text to be more precise
        mock_loc_ent = MagicMock(label_="GPE", text="Cairo") 
        mock_fac_ent = MagicMock(label_="FAC", text="Egyptian Museum")
        self.mock_doc.ents = [mock_loc_ent, mock_fac_ent]
        self.mock_nlp_model.return_value = self.mock_doc
        
        # Create mock knowledge base
        self.knowledge_base = MockKnowledgeBase()
        
        # Mock attraction lookup
        self.knowledge_base.lookup_attraction = MagicMock(return_value={
            "id": "egyptian_museum",
            "name": {"en": "Egyptian Museum", "ar": "المتحف المصري"},
            "canonical_name": "Egyptian Museum"
        })
        
        # Create entity extractor
        self.extractor = EntityExtractor(
            language="en",
            config={},
            nlp_model=self.mock_nlp_model,
            knowledge_base=self.knowledge_base
        )
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
    
    def test_extract_location(self):
        """Test extracting location entities."""
        result = self.extractor.extract("I want to visit Cairo", intent="travel")
        
        self.assertIn("location", result["entities"])
        self.assertEqual(result["entities"]["location"][0]["value"], "Cairo")
    
    def test_extract_attraction(self):
        """Test extracting attraction entities."""
        result = self.extractor.extract("Tell me about the Egyptian Museum", intent="attraction_info")
        
        self.assertIn("attraction", result["entities"])
        self.assertEqual(result["entities"]["attraction"][0]["value"], "Egyptian Museum")
    
    def test_resolve_entities(self):
        """Test resolving entities using knowledge base."""
        # Set up entities and confidence scores
        entities = {
            "location": ["Cairo"],
            "attraction": ["Egyptian Museum"]
        }
        confidence_scores = {
            "location": [0.8],
            "attraction": [0.9]
        }
        
        # Call resolve entities method
        self.extractor._resolve_entities(entities, confidence_scores, "attraction_info", {})
        
        # Verify attraction was resolved
        self.assertEqual(entities["attraction"][0], "Egyptian Museum")
        self.assertGreater(confidence_scores["attraction"][0], 0.9)
        
        # Verify knowledge base was called
        self.knowledge_base.lookup_attraction.assert_called_once_with(
            "Egyptian Museum", "en", "Cairo"
        )


class TestNLUEngine(BaseTestCase):
    """Tests for the NLU engine."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up mock return values (Keep these)
        self.mock_language_detector_instance = MagicMock()
        self.mock_language_detector_instance.detect.return_value = ("en", 0.95)
    
        self.mock_intent_classifier_instance = MagicMock()
        self.mock_intent_classifier_instance.classify.return_value = {
            "intent": "greeting",
            "confidence": 0.9,
            "match_type": "similarity"
        }
    
        self.mock_entity_extractor_instance = MagicMock()
        self.mock_entity_extractor_instance.extract.return_value = {
            "entities": {}
        }
        
        # Create mock knowledge base
        self.knowledge_base = MockKnowledgeBase()
        
        # --- Initialize REAL NLU engine --- 
        # Patch spacy/transformers loading within NLUEngine.__init__ to avoid downloads/errors
        with patch('src.nlu.engine.spacy.load', MagicMock()) as mock_spacy_load, \
             patch('src.nlu.engine.spacy.cli.download', MagicMock()), \
             patch('src.nlu.engine.AutoTokenizer.from_pretrained', MagicMock()) as mock_tokenizer_load, \
             patch('src.nlu.engine.AutoModel.from_pretrained', MagicMock()) as mock_model_load:
            
            self.nlu_engine = NLUEngine(
                models_config=os.path.join(self.temp_dir, "configs", "models.json"),
                knowledge_base=self.knowledge_base
            )
        
        # --- REPLACE internal components with mocks AFTER init --- 
        self.nlu_engine.language_detector = self.mock_language_detector_instance
        self.nlu_engine.intent_classifier = self.mock_intent_classifier_instance
        # Replace all language-specific entity extractors with the same mock instance
        for lang in self.nlu_engine.entity_extractors.keys():
            self.nlu_engine.entity_extractors[lang] = self.mock_entity_extractor_instance
        # We don't need to mock _get_embedding_model if we mock the classifier that uses it

    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
    
    def test_process_english(self):
        """Test processing an English message."""
        result = self.nlu_engine.process(
            text="Hello, how are you?",
            session_id="test_session",
            language="en",
            context={}
        )
        
        # Verify result structure
        self.assertEqual(result["text"], "Hello, how are you?")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["intent"], "greeting")
        self.assertEqual(result["intent_confidence"], 0.9)
        self.assertIn("entities", result)
        self.assertEqual(result["session_id"], "test_session")
        
        # Verify components were called
        self.mock_intent_classifier_instance.classify.assert_called_once()
        self.mock_entity_extractor_instance.extract.assert_called_once()
    
    def test_process_with_language_detection(self):
        """Test processing with language detection."""
        result = self.nlu_engine.process(
            text="مرحبا، كيف حالك؟",
            session_id="test_session",
            language=None,
            context={}
        )
        
        # Verify language detection was used
        self.mock_language_detector_instance.detect.assert_called_once_with("مرحبا، كيف حالك؟")
        
        # Verify detected language was used
        self.assertEqual(result["language"], "en")  # Mock returns "en"
        self.assertEqual(result["language_confidence"], 0.95)
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        # Test default preprocessing (lowercase, strip)
        processed = self.nlu_engine._preprocess_text("  Hello, World!  ", "en")
        self.assertEqual(processed, "hello, world!")
    
    def test_get_embedding_model(self):
        """Test the embedding model getter."""
        # Mock _get_embedding_model directly to avoid complex setup
        self.nlu_engine._get_embedding_model = MagicMock(return_value=np.ones((1, 10)))
        
        # Process a message
        result = self.nlu_engine.process(
            text="Hello, how are you?",
            session_id="test_session",
            language="en",
            context={}
        )
        
        # Verify embedding model was called
        self.nlu_engine._get_embedding_model.assert_called_once_with("hello, how are you?", "en")


if __name__ == "__main__":
    pytest.main()