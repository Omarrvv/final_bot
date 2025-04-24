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
