#!/usr/bin/env python3
"""
Script to test entity extraction for attractions, specifically focusing on 'pyramids'.
This will help diagnose and improve the NLU entity extraction capabilities.
"""

import os
import sys
import logging
import json
import uuid
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Set environment variables for testing
os.environ["USE_NEW_KB"] = "true"
os.environ["USE_POSTGRES"] = "true"
os.environ["USE_NEW_NLU"] = "true"  # Enable new NLU engine

# Import components
from src.utils.factory import component_factory
from src.nlu.engine import NLUEngine
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager

def initialize_components():
    """Initialize the required components for testing."""
    logger.info("Initializing components...")
    try:
        # Initialize component factory
        component_factory.initialize()
        
        # Create a KnowledgeBase instance
        db_manager = DatabaseManager()
        knowledge_base = KnowledgeBase(db_manager)
        
        # Create an NLUEngine instance directly
        logger.info("Creating new NLU Engine instance")
        models_config = os.path.join(project_root, "configs/models.json")
        nlu_engine = NLUEngine(models_config=models_config, knowledge_base=knowledge_base)
        
        logger.info("Components initialized successfully")
        return knowledge_base, nlu_engine, db_manager
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        raise

def test_attraction_entity_extraction(nlu_engine, test_queries):
    """
    Test attraction entity extraction for a set of queries.
    
    Args:
        nlu_engine: The NLUEngine instance
        test_queries: List of test queries
    
    Returns:
        List of results with entities extracted
    """
    logger.info("Testing attraction entity extraction...")
    results = []
    
    # Create a unique session ID for testing
    session_id = str(uuid.uuid4())
    
    for query in test_queries:
        try:
            logger.info(f"Processing query: {query}")
            
            # Process the query with NLU engine
            nlu_result = nlu_engine.process(query, session_id=session_id, language="en")
            
            # Extract attractions entities
            attraction_entities = [
                entity for entity in nlu_result.entities 
                if entity.entity_type == "attraction"
            ]
            
            result = {
                "query": query,
                "entities": [
                    {"type": entity.entity_type, "value": entity.value, "confidence": entity.confidence}
                    for entity in nlu_result.entities
                ],
                "attraction_entities": [
                    {"value": entity.value, "confidence": entity.confidence}
                    for entity in attraction_entities
                ],
                "intent": nlu_result.intent,
                "intent_confidence": nlu_result.intent_confidence
            }
            
            results.append(result)
            logger.info(f"Extracted entities: {result['entities']}")
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            results.append({"query": query, "error": str(e)})
    
    return results

def search_attractions_in_db(db_manager, search_terms):
    """
    Search for attractions directly in the database.
    
    Args:
        db_manager: The DatabaseManager instance
        search_terms: List of search terms
    
    Returns:
        Dictionary mapping search terms to attraction results
    """
    logger.info("Searching for attractions in database...")
    results = {}
    
    for term in search_terms:
        try:
            logger.info(f"Searching for: {term}")
            
            # Execute direct database query
            conn = db_manager.pg_pool.getconn()
            cursor = conn.cursor()
            
            # Search in name_en, name_ar, and description_en
            cursor.execute("""
                SELECT id, name_en, name_ar, description_en 
                FROM attractions 
                WHERE 
                    name_en ILIKE %s OR 
                    name_ar ILIKE %s OR 
                    description_en ILIKE %s
            """, (f"%{term}%", f"%{term}%", f"%{term}%"))
            
            db_results = cursor.fetchall()
            db_manager.pg_pool.putconn(conn)
            
            results[term] = [
                {
                    "id": row[0],
                    "name_en": row[1],
                    "name_ar": row[2],
                    "description_snippet": row[3][:100] + "..." if row[3] and len(row[3]) > 100 else row[3]
                }
                for row in db_results
            ]
            
            logger.info(f"Found {len(results[term])} attractions for '{term}'")
            
        except Exception as e:
            logger.error(f"Error searching for '{term}': {e}")
            results[term] = {"error": str(e)}
    
    return results

def enhance_attraction_recognition(nlu_engine, knowledge_base):
    """
    Enhance attraction entity recognition by adding common terms.
    
    Args:
        nlu_engine: The NLUEngine instance
        knowledge_base: The KnowledgeBase instance
    """
    logger.info("Enhancing attraction entity recognition...")
    
    # Add common synonyms for attractions
    attraction_synonyms = {
        "pyramids": ["pyramid", "pyramids", "giza pyramids", "great pyramid", "pyramids of giza"],
        "sphinx": ["sphinx", "great sphinx", "sphinx of giza"],
        "luxor temple": ["luxor temple", "temple of luxor", "luxor temples"],
        "karnak": ["karnak", "karnak temple", "temples of karnak"],
        "valley of the kings": ["valley of the kings", "kings valley"],
        "egyptian museum": ["egyptian museum", "cairo museum", "museum of egyptian antiquities"],
        "khan el khalili": ["khan el khalili", "khan el-khalili", "khan al-khalili", "khan bazaar"]
    }
    
    try:
        # Directly add patterns to entity extractors if available
        for lang in nlu_engine.entity_extractors:
            logger.info(f"Adding attraction patterns for language: {lang}")
            entity_extractor = nlu_engine.entity_extractors.get(lang)
            
            if entity_extractor and hasattr(entity_extractor, 'add_pattern'):
                for main_term, synonyms in attraction_synonyms.items():
                    for synonym in synonyms:
                        entity_extractor.add_pattern('attraction', synonym, confidence=0.9)
                logger.info(f"Added {sum(len(syns) for syns in attraction_synonyms.values())} attraction patterns to {lang} entity extractor")
            else:
                logger.warning(f"Entity extractor for {lang} does not support adding patterns")
                
    except Exception as e:
        logger.error(f"Error enhancing attraction recognition: {e}")
        
    # Fetch actual attractions from database
    try:
        # Connect to database
        conn = knowledge_base.db_manager.pg_pool.getconn()
        cursor = conn.cursor()
        
        # Get attraction names
        cursor.execute("""
            SELECT name_en, name_ar 
            FROM attractions 
            WHERE name_en IS NOT NULL OR name_ar IS NOT NULL
        """)
        
        rows = cursor.fetchall()
        knowledge_base.db_manager.pg_pool.putconn(conn)
        
        # Process attraction names
        attraction_names = []
        for row in rows:
            if row[0]:  # name_en
                attraction_names.append(row[0])
            if row[1]:  # name_ar
                attraction_names.append(row[1])
                
        logger.info(f"Found {len(attraction_names)} attraction names in database")
        
        # Try to add attraction names to entity extractors
        for lang in nlu_engine.entity_extractors:
            entity_extractor = nlu_engine.entity_extractors.get(lang)
            if entity_extractor and hasattr(entity_extractor, 'add_entities'):
                entity_extractor.add_entities('attraction', attraction_names)
                logger.info(f"Added {len(attraction_names)} attraction names to {lang} entity extractor")
            
    except Exception as e:
        logger.error(f"Error fetching attractions from database: {e}")
    
    return attraction_synonyms

def main():
    """Main function to run the tests."""
    test_results = {}
    db_results = {}
    
    try:
        knowledge_base, nlu_engine, db_manager = initialize_components()
        
        # Define test queries focusing on attractions, especially pyramids
        test_queries = [
            "Tell me about the pyramids",
            "How old are the pyramids?",
            "I want to visit the pyramids of Giza",
            "What can you tell me about the Great Pyramid?",
            "Are the pyramids in Cairo?",
            "Where can I find the Sphinx?",
            "What is the history of Luxor Temple?",
            "How do I get to the Valley of the Kings?",
            "Tell me about Egyptian landmarks",
            "What are the best attractions in Egypt?",
            "Is Khan el Khalili worth visiting?",
            "What should I see in Luxor?",
            "Where is the Egyptian Museum located?",
            "Tell me about the Karnak Temple",
        ]
        
        # Test before enhancement
        logger.info("Testing entity extraction before enhancement...")
        test_results["before_enhancement"] = test_attraction_entity_extraction(nlu_engine, test_queries)
        
        # Search for attractions in database
        search_terms = ["pyramid", "giza", "sphinx", "luxor", "karnak", "king", "museum", "khan"]
        db_results = search_attractions_in_db(db_manager, search_terms)
        
        # Enhance attraction recognition
        enhance_attraction_recognition(nlu_engine, knowledge_base)
        
        # Test after enhancement
        logger.info("Testing entity extraction after enhancement...")
        test_results["after_enhancement"] = test_attraction_entity_extraction(nlu_engine, test_queries)
        
        # Export results to JSON file
        output_file = os.path.join(project_root, "entity_extraction_results.json")
        with open(output_file, "w") as f:
            json.dump({
                "test_results": test_results,
                "db_results": db_results
            }, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 