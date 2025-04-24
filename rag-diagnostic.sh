#!/bin/bash
# RAG Pipeline Diagnostic Script for Egypt Tourism Chatbot
# This script investigates why the chatbot isn't using database information for queries

echo "========== CHATBOT RAG PIPELINE DIAGNOSTICS =========="
echo "Running comprehensive diagnostics on the system's retrieval components..."
echo ""

# === 1. Knowledge Base Configuration ===
echo "===== Knowledge Base Configuration ====="
echo "Checking knowledge base configuration files..."
grep -r "KnowledgeBase\|knowledge_base\|embedding\|vector" --include="*.py" src/

echo -e "\nChecking environment variables related to knowledge base..."
grep -r "KNOWLEDGE_BASE\|VECTOR\|EMBEDDING\|USE_RAG\|RAG_ENABLED" --include="*.env*" .

echo -e "\nLooking at knowledge base implementation..."
find src -type f -name "*knowledge_base*.py" -o -name "*vector*.py" | xargs cat

# === 2. Intent and Entity Recognition ===
echo -e "\n\n===== Intent and Entity Recognition ====="
echo "Checking NLU components for location recognition..."
grep -r "entity\|intent\|classifier\|location\|city" --include="*.py" src/nlu/

echo -e "\nChecking for any intent/entity mapping configuration..."
find src -name "*intent*.py" -o -name "*entity*.py" | xargs cat

# === 3. RAG Pipeline Flow ===
echo -e "\n\n===== RAG Pipeline Flow ====="
echo "Checking how requests flow through the system..."
find src -name "main.py" -o -name "chatbot.py" -o -name "*router*.py" -o -name "*handler*.py" | xargs cat

# === 4. Database Integration ===
echo -e "\n\n===== Database Integration ====="
echo "Checking how the database connects to the chat flow..."
grep -r "search_attractions\|search_restaurants\|search_accommodations" --include="*.py" src/

# === 5. Test Direct Query Bypassing NLU ===
echo -e "\n\n===== Testing Direct Knowledge Base Query ====="
echo "Creating Python script to directly test knowledge retrieval..."

cat > test_direct_retrieval.py << 'EOL'
#!/usr/bin/env python3
"""
Direct test of the knowledge base retrieval without going through the API.
This bypasses the NLU and tests the knowledge base directly.
"""
import os
import sys
import importlib.util
import json
import traceback

# Add the project root to the path
sys.path.append('.')

def find_module_path(module_name, search_paths):
    """Find the path to a module file."""
    for path in search_paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file == f"{module_name}.py" or file == f"{module_name}/__init__.py":
                    return os.path.join(root, file)
    return None

def load_module(module_name, file_path):
    """Dynamically load a module from its file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_knowledge_base():
    """Test the knowledge base retrieval directly."""
    print("Testing direct knowledge base retrieval...")
    
    # Find relevant modules
    kb_file = find_module_path("knowledge_base", ["src", "src/knowledge"])
    db_file = find_module_path("database", ["src", "src/knowledge", "src/utils"])
    
    if not kb_file:
        print("⚠️ Knowledge base module not found!")
        return False
    
    print(f"Found knowledge base module: {kb_file}")
    
    if db_file:
        print(f"Found database module: {db_file}")
    
    try:
        # Try to import knowledge base module
        kb_module_name = os.path.basename(kb_file).replace(".py", "")
        kb_module = load_module(kb_module_name, kb_file)
        print(f"Successfully loaded {kb_module_name} module")
        
        # Find KnowledgeBase class
        knowledge_base_class = None
        for name in dir(kb_module):
            obj = getattr(kb_module, name)
            if isinstance(obj, type) and "knowledge" in name.lower():
                knowledge_base_class = obj
                print(f"Found knowledge base class: {name}")
                break
        
        if not knowledge_base_class:
            print("⚠️ Couldn't find KnowledgeBase class!")
            return False
        
        # Instantiate knowledge base
        try:
            kb_instance = knowledge_base_class()
            print(f"Successfully created knowledge base instance: {kb_instance}")
        except Exception as e:
            print(f"⚠️ Error creating knowledge base instance: {e}")
            # Try to find factory or initialize method
            factory_functions = [name for name in dir(kb_module) if "factory" in name.lower() or "get_" in name.lower() or "create_" in name.lower()]
            if factory_functions:
                print(f"Found potential factory functions: {factory_functions}")
                for func_name in factory_functions:
                    try:
                        factory_func = getattr(kb_module, func_name)
                        kb_instance = factory_func()
                        print(f"Created knowledge base using {func_name}: {kb_instance}")
                        break
                    except Exception as e:
                        print(f"Error using {func_name}: {e}")
            
            if not 'kb_instance' in locals():
                # Last resort: look for any instance variable in the module
                for name in dir(kb_module):
                    obj = getattr(kb_module, name)
                    if not name.startswith("__") and not callable(obj) and hasattr(obj, "query") or hasattr(obj, "search"):
                        kb_instance = obj
                        print(f"Found potential knowledge base instance: {name}")
                        break
        
        if not 'kb_instance' in locals():
            print("⚠️ Couldn't create knowledge base instance!")
            return False
        
        # Test query methods
        query_methods = [name for name in dir(kb_instance) if "query" in name.lower() or "search" in name.lower() or "retrieve" in name.lower()]
        if not query_methods:
            print("⚠️ No query/search methods found in knowledge base!")
            return False
        
        print(f"Found query methods: {query_methods}")
        
        # Test with specific queries
        test_queries = [
            "pyramids of giza",
            "egyptian museum cairo",
            "attractions in cairo"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            
            for method_name in query_methods:
                try:
                    method = getattr(kb_instance, method_name)
                    print(f"Trying method: {method_name}")
                    result = method(query)
                    print(f"Result from {method_name}: {result}")
                    if result:
                        print(f"✅ Query successful using {method_name}!")
                        return True
                except Exception as e:
                    print(f"Error using {method_name}: {e}")
        
        print("⚠️ All query attempts failed!")
        return False
    
    except Exception as e:
        print(f"Error testing knowledge base: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    if test_knowledge_base():
        print("\n✅ Knowledge base retrieval test succeeded!")
        sys.exit(0)
    else:
        print("\n❌ Knowledge base retrieval test failed!")
        sys.exit(1)
EOL

chmod +x test_direct_retrieval.py
echo "Created test_direct_retrieval.py"

# === 6. Test Anthropic API Integration ===
echo -e "\n\n===== Anthropic API Integration ====="
echo "Checking how the LLM is integrated with the RAG pipeline..."
grep -r "anthropic\|claude\|llm\|generate_response" --include="*.py" src/

# === 7. Analysis of Application Logs ===
echo -e "\n\n===== Application Logs ====="
echo "Checking recent application logs for RAG-related messages..."
find . -name "*.log" | xargs grep -i "knowledge\|database\|retrieval\|rag\|embedding\|query" 2>/dev/null || echo "No relevant log entries found"

# === 8. Check for Debug/Feature Flags ===
echo -e "\n\n===== Debug and Feature Flags ====="
echo "Checking for any debug or feature flags that might be disabling RAG..."
grep -r "debug\|feature_flag\|USE_" --include="*.py" --include="*.env*" .

# === 9. Check for Proper Requests in Tests ===
echo -e "\n\n===== Creating Test for Direct API with Debug Info ====="
cat > test_api_with_debug.py << 'EOL'
#!/usr/bin/env python3
"""
Test the chat API with debug info to see what's happening inside the RAG pipeline.
"""
import requests
import json
import sys

def test_chat_api_with_debug():
    """Test the chat API with debug mode enabled."""
    # Base URL for your API
    base_url = "http://localhost:5050"
    
    # Chat endpoint
    chat_endpoint = f"{base_url}/api/chat"
    
    # Test queries
    test_queries = [
        {
            "message": "What are the top attractions in Cairo?",
            "session_id": "test-debug-123",
            "debug": True
        },
        {
            "message": "Tell me about the Egyptian Museum",
            "session_id": "test-debug-123",
            "debug": True,
            "enable_rag": True  # Try to force RAG if supported
        }
    ]
    
    for payload in test_queries:
        query = payload["message"]
        print(f"\n🔍 Testing query with debug: \"{query}\"")
        
        try:
            # Send request to the API
            response = requests.post(
                chat_endpoint, 
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Got response with debug info:")
                print(json.dumps(result, indent=2))
                
                # Check if debug info contains any retrieval data
                debug_info = result.get("debug_info", {})
                if debug_info and any(k in str(debug_info).lower() for k in ["retriev", "knowledge", "database", "rag"]):
                    print("✅ Debug info contains retrieval information!")
                    return True
            else:
                print(f"❌ ERROR: API returned status code {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing chat API with debug info...")
    if test_chat_api_with_debug():
        print("\n✅ API debug test passed! Found retrieval information.")
        sys.exit(0)
    else:
        print("\n❌ API debug test passed but no retrieval information found.")
        sys.exit(1)
EOL

chmod +x test_api_with_debug.py
echo "Created test_api_with_debug.py for debug-enabled API testing"

# Run the most important tests
echo -e "\n\n===== Running Direct Knowledge Base Test ====="
python test_direct_retrieval.py

echo -e "\n\n===== Running API Debug Test ====="
python test_api_with_debug.py

echo -e "\n\n========== DIAGNOSTICS COMPLETE =========="
echo "Check the output above for clues about why RAG isn't working."
echo "The most likely issues are:"
echo "1. Knowledge base is not properly connected to the database"
echo "2. NLU is not recognizing entities correctly"
echo "3. RAG pipeline is disabled by a feature flag"
echo "4. Integration between retrieval and LLM generation is broken"