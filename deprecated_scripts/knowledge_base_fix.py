#!/usr/bin/env python3
"""
Fix BaseKnowledgeItem validation issues by making fields optional.
"""
import importlib
import inspect
import sys
import os

def patch_kb_class():
    """Attempt to find and patch the knowledge base classes."""
    # Try to import the knowledge base module
    module_paths = [
        'src.knowledge.knowledge_base',
        'src.models.knowledge_base',
        'knowledge_base'
    ]
    
    kb_module = None
    for path in module_paths:
        try:
            kb_module = importlib.import_module(path)
            print(f"Found knowledge base module: {path}")
            break
        except ImportError:
            continue
    
    if not kb_module:
        print("Could not import knowledge base module. Make sure your PYTHONPATH is set correctly.")
        return False
    
    # Find the problematic classes
    for name, obj in inspect.getmembers(kb_module):
        if inspect.isclass(obj) and hasattr(obj, '__init__') and name.endswith('Item'):
            print(f"Found knowledge base item class: {name}")
            
            # Look at the class __init__ method to see if it's using strict validation
            try:
                # Try to create an instance with empty values
                instance = obj()
                print(f"✅ Class {name} can be instantiated with defaults")
            except TypeError as e:
                print(f"⚠️ Class {name} has initialization errors: {e}")
                # The class is likely missing default values
                print("This class needs default values for required fields")
            except Exception as e:
                print(f"⚠️ Class {name} has other errors: {e}")
    
    print("\nTo fix BaseKnowledgeItem validation issues, add the following code to your module:")
    print("\nModify your BaseKnowledgeItem or similar class to make fields optional or provide defaults:")
    print("""
class BaseKnowledgeItem:
    def __init__(self, id=None, name=None, description=None, **kwargs):
        self.id = id or "placeholder_id"
        self.name = name or "placeholder_name"
        self.description = description or "placeholder_description"
        # Add other fields with defaults
        for key, value in kwargs.items():
            setattr(self, key, value)
    """)
    
    return True

if __name__ == "__main__":
    patch_kb_class()
