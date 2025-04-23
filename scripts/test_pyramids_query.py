#!/usr/bin/env python
"""
Test script to verify the Knowledge Base can properly retrieve information about the Pyramids of Giza.
This script tests both legacy and new Knowledge Base implementations with different feature flag settings.
"""

import os
import sys
import json
import uuid
import logging
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.utils.database import DatabaseManager
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase
from src.nlu.engine import NLUEngine
from src.dialog.manager import DialogManager
from src.response.generator import ResponseGenerator
from src.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_pyramids_query')

# Test queries about the Pyramids
TEST_QUERIES = [
    "Tell me about the Pyramids of Giza",
    "What are the Pyramids of Giza?",
    "Where are the Pyramids located?",
    "When were the Pyramids built?",
    "How tall is the Great Pyramid?",
    "What can I see at the Pyramids complex?",
    "How much does it cost to visit the Pyramids?",
    "What are the opening hours for the Pyramids?",
    "Tell me some facts about the Pyramids",
    "What should I know before visiting the Pyramids?"
]

def save_results(results: Dict[str, Any], filename: str = "pyramids_query_results.json"):
    """Save test results to a JSON file."""
    os.makedirs("test_results", exist_ok=True)
    filepath = os.path.join("test_results", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to {filepath}")

def get_original_settings():
    """Get the original feature flag settings to restore later."""
    return {
        "use_new_kb": settings.use_new_kb,
        "use_postgres": settings.use_postgres,
        "use_new_nlu": settings.use_new_nlu,
        "use_new_dialog": settings.use_new_dialog,
        "use_rag": settings.use_rag
    }

def restore_settings(original_settings):
    """Restore original feature flag settings."""
    for key, value in original_settings.items():
        setattr(settings, key, value)
    logger.info("Restored original settings")

def setup_knowledge_base(use_new_kb: bool = True, use_postgres: bool = False) -> KnowledgeBase:
    """Set up the Knowledge Base with appropriate settings."""
    # Override settings
    settings.use_new_kb = use_new_kb
    settings.use_postgres = use_postgres
    
    # Create database manager based on settings
    if use_postgres:
        db_manager = PostgresqlDatabaseManager()
    else:
        db_manager = DatabaseManager()
    
    # Create and return Knowledge Base
    return KnowledgeBase(db_manager)

def test_knowledge_base_direct():
    """Test the Knowledge Base component directly for Pyramids queries."""
    results = {}
    
    # Test with SQLite
    logger.info("\n--- Testing Knowledge Base with SQLite ---")
    settings.use_postgres = False
    kb_sqlite = setup_knowledge_base(use_new_kb=True, use_postgres=False)
    
    sqlite_results = {
        "lookup": {},
        "search": {},
        "errors": []
    }
    
    # Test direct lookup
    try:
        logger.info("Testing direct lookup for 'pyramids_giza'...")
        attraction = kb_sqlite.get_attraction_by_id("pyramids_giza")
        sqlite_results["lookup"]["by_id"] = {
            "found": attraction is not None,
            "name": attraction.get("name_en") if attraction else None
        }
    except Exception as e:
        logger.error(f"Error in direct lookup: {str(e)}")
        sqlite_results["errors"].append(f"lookup_error: {str(e)}")
    
    # Test attraction lookup by name
    try:
        logger.info("Testing lookup_attraction for 'Pyramids of Giza'...")
        attraction = kb_sqlite.lookup_attraction("Pyramids of Giza", "en")
        sqlite_results["lookup"]["by_name"] = {
            "found": attraction is not None,
            "name": attraction.get("name_en") if attraction else None
        }
    except Exception as e:
        logger.error(f"Error in lookup_attraction: {str(e)}")
        sqlite_results["errors"].append(f"lookup_attraction_error: {str(e)}")
    
    # Test search attractions
    try:
        logger.info("Testing search_attractions for 'pyramid'...")
        attractions = kb_sqlite.search_attractions("pyramid", {}, "en", 5)
        sqlite_results["search"]["results"] = [
            {"id": a.get("id"), "name": a.get("name_en")} 
            for a in attractions
        ] if attractions else []
    except Exception as e:
        logger.error(f"Error in search_attractions: {str(e)}")
        sqlite_results["errors"].append(f"search_error: {str(e)}")
    
    results["sqlite"] = sqlite_results
    
    # Test with PostgreSQL if enabled
    if os.environ.get("USE_POSTGRES", "").lower() == "true" or settings.use_postgres:
        logger.info("\n--- Testing Knowledge Base with PostgreSQL ---")
        kb_postgres = setup_knowledge_base(use_new_kb=True, use_postgres=True)
        
        postgres_results = {
            "lookup": {},
            "search": {},
            "errors": []
        }
        
        # Test direct lookup
        try:
            logger.info("Testing direct lookup for 'pyramids_giza'...")
            attraction = kb_postgres.get_attraction_by_id("pyramids_giza")
            postgres_results["lookup"]["by_id"] = {
                "found": attraction is not None,
                "name": attraction.get("name_en") if attraction else None
            }
        except Exception as e:
            logger.error(f"Error in direct lookup: {str(e)}")
            postgres_results["errors"].append(f"lookup_error: {str(e)}")
        
        # Test attraction lookup by name
        try:
            logger.info("Testing lookup_attraction for 'Pyramids of Giza'...")
            attraction = kb_postgres.lookup_attraction("Pyramids of Giza", "en")
            postgres_results["lookup"]["by_name"] = {
                "found": attraction is not None,
                "name": attraction.get("name_en") if attraction else None
            }
        except Exception as e:
            logger.error(f"Error in lookup_attraction: {str(e)}")
            postgres_results["errors"].append(f"lookup_attraction_error: {str(e)}")
        
        # Test search attractions
        try:
            logger.info("Testing search_attractions for 'pyramid'...")
            attractions = kb_postgres.search_attractions("pyramid", {}, "en", 5)
            postgres_results["search"]["results"] = [
                {"id": a.get("id"), "name": a.get("name_en")} 
                for a in attractions
            ] if attractions else []
        except Exception as e:
            logger.error(f"Error in search_attractions: {str(e)}")
            postgres_results["errors"].append(f"search_error: {str(e)}")
        
        results["postgres"] = postgres_results
    
    return results

def simulate_nlu_processing(query: str, language: str = "en"):
    """Simulate the NLU processing of a query."""
    logger.info(f"\nSimulating NLU processing for query: '{query}'")
    
    # Create NLU Engine
    try:
        # Create Knowledge Base first (needed by NLU)
        db_manager = DatabaseManager() if not settings.use_postgres else PostgresqlDatabaseManager()
        kb = KnowledgeBase(db_manager)
        
        # Create NLU Engine
        nlu = NLUEngine(kb)
        
        # Process query
        session_id = str(uuid.uuid4())
        result = nlu.process(query, session_id, language)
        
        # Log detected intent and entities
        logger.info(f"Detected intent: {result.get('intent')}")
        logger.info(f"Detected entities: {result.get('entities')}")
        
        return result
    except Exception as e:
        logger.error(f"Error in NLU processing: {str(e)}")
        return {"error": str(e)}

def simulate_full_chat_flow(query: str, language: str = "en"):
    """Simulate the full chat flow including NLU, Dialog, and Response."""
    logger.info(f"\nSimulating full chat flow for query: '{query}'")
    
    try:
        # Set up components
        db_manager = DatabaseManager() if not settings.use_postgres else PostgresqlDatabaseManager()
        kb = KnowledgeBase(db_manager)
        nlu = NLUEngine(kb)
        dialog_manager = DialogManager(kb, nlu)
        response_generator = ResponseGenerator()
        
        # Process through the pipeline
        session_id = str(uuid.uuid4())
        
        # 1. NLU Processing
        logger.info("Step 1: NLU Processing")
        nlu_result = nlu.process(query, session_id, language)
        logger.info(f"NLU Result: Intent={nlu_result.get('intent')}, Entities={nlu_result.get('entities')}")
        
        # 2. Dialog Management
        logger.info("Step 2: Dialog Management")
        dialog_state = dialog_manager.process(nlu_result, session_id)
        logger.info(f"Dialog State: {dialog_state}")
        
        # 3. Response Generation
        logger.info("Step 3: Response Generation")
        response = response_generator.generate(dialog_state, language)
        logger.info(f"Response: {response}")
        
        return {
            "nlu_result": nlu_result,
            "dialog_state": dialog_state,
            "response": response
        }
    except Exception as e:
        logger.error(f"Error in chat flow simulation: {str(e)}")
        return {"error": str(e)}

def compare_legacy_vs_new(query: str):
    """Compare responses from legacy and new Knowledge Base implementations."""
    logger.info(f"\nComparing legacy vs. new KB for query: '{query}'")
    
    # Store original settings
    original_settings = get_original_settings()
    
    results = {
        "query": query,
        "legacy": {},
        "new": {}
    }
    
    try:
        # Test with legacy KB
        logger.info("Testing with legacy KB...")
        settings.use_new_kb = False
        legacy_response = simulate_full_chat_flow(query)
        results["legacy"] = {
            "response": legacy_response.get("response", ""),
            "error": legacy_response.get("error", "")
        }
        
        # Test with new KB
        logger.info("Testing with new KB...")
        settings.use_new_kb = True
        new_response = simulate_full_chat_flow(query)
        results["new"] = {
            "response": new_response.get("response", ""),
            "error": new_response.get("error", "")
        }
    except Exception as e:
        logger.error(f"Error in comparison: {str(e)}")
        results["error"] = str(e)
    finally:
        # Restore original settings
        restore_settings(original_settings)
    
    return results

def run_batch_tests():
    """Run a series of test queries and compile results."""
    logger.info("\nRunning batch tests...")
    
    # Store original settings
    original_settings = get_original_settings()
    
    results = {
        "kb_test": test_knowledge_base_direct(),
        "queries": {}
    }
    
    try:
        # Test each query with both legacy and new KB
        for query in TEST_QUERIES:
            results["queries"][query] = compare_legacy_vs_new(query)
    except Exception as e:
        logger.error(f"Error in batch tests: {str(e)}")
        results["error"] = str(e)
    finally:
        # Restore original settings
        restore_settings(original_settings)
    
    # Save results to file
    save_results(results)
    return results

def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(description="Test Pyramids of Giza queries in the chatbot.")
    parser.add_argument('--query', type=str, help='Single query to test')
    parser.add_argument('--batch', action='store_true', help='Run batch tests for all queries')
    parser.add_argument('--compare', action='store_true', help='Compare legacy vs. new KB')
    parser.add_argument('--kb-only', action='store_true', help='Test only the Knowledge Base component')
    parser.add_argument('--language', type=str, default='en', help='Language for queries (en, ar)')
    args = parser.parse_args()
    
    # If no arguments provided, run batch tests
    if len(sys.argv) == 1:
        logger.info("No arguments provided, running batch tests...")
        run_batch_tests()
        return
    
    # Test Knowledge Base directly
    if args.kb_only:
        logger.info("Testing Knowledge Base component directly...")
        results = test_knowledge_base_direct()
        save_results(results, "kb_test_results.json")
        return
    
    # Test single query
    if args.query:
        if args.compare:
            logger.info(f"Comparing legacy vs. new KB for query: '{args.query}'")
            results = compare_legacy_vs_new(args.query)
        else:
            logger.info(f"Processing query: '{args.query}'")
            results = simulate_full_chat_flow(args.query, args.language)
        
        save_results({"query": args.query, "results": results}, "single_query_results.json")
        return
    
    # Run batch tests
    if args.batch:
        run_batch_tests()

if __name__ == "__main__":
    main() 