#!/usr/bin/env python3
"""
Fix the Knowledge Base implementation to handle initialization issues.
"""
import os
import sys
import re

def find_knowledge_base_module():
    """Find the knowledge base module."""
    # Typical locations for the knowledge base module
    potential_paths = [
        "src/knowledge/knowledge_base.py",
        "src/models/knowledge_base.py",
        "src/kb.py"
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found knowledge base module at: {path}")
            return path
    
    # Search for knowledge base related files
    for root, dirs, files in os.walk("src"):
        for file in files:
            if "knowledge" in file.lower() and file.endswith(".py"):
                path = os.path.join(root, file)
                print(f"Found potential knowledge base module at: {path}")
                return path
    
    print("❌ Could not find knowledge base module")
    return None

def fix_knowledge_base_class(file_path):
    """Fix the knowledge base class initialization issues."""
    if not file_path or not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Make a backup of the file
    backup_path = f"{file_path}.bak"
    with open(file_path, 'r') as f:
        original_content = f.read()
    
    with open(backup_path, 'w') as f:
        f.write(original_content)
    print(f"Created backup of original file at: {backup_path}")
    
    # Find the BaseKnowledgeItem class or similar
    class_pattern = re.compile(r'class\s+(BaseKnowledgeItem|KnowledgeItem|BaseItem).*?:.*?(?=class|\Z)', re.DOTALL)
    match = class_pattern.search(original_content)
    
    if not match:
        print("❌ Could not find the knowledge item class definition")
        return False
    
    class_def = match.group(0)
    class_name = re.search(r'class\s+(\w+)', class_def).group(1)
    
    # Check if the class has validation issues for required fields
    has_validation_issues = any(field in class_def for field in ["id", "name", "description"])
    
    if has_validation_issues:
        print(f"Found {class_name} class with potential validation issues")
        
        # Modify the class to make fields optional or provide defaults
        modified_class = class_def
        
        # Make id field optional with default factory
        modified_class = re.sub(
            r'id\s*:\s*(\w+)',
            r'id: Optional[\1] = None',
            modified_class
        )
        
        # Make name field optional with default factory
        modified_class = re.sub(
            r'name\s*:\s*(\w+)',
            r'name: Optional[\1] = None',
            modified_class
        )
        
        # Make description field optional with default factory
        modified_class = re.sub(
            r'description\s*:\s*(\w+)',
            r'description: Optional[\1] = None',
            modified_class
        )
        
        # Add Optional import if not already present
        import_optional = "from typing import Optional, "
        if "Optional" not in original_content:
            if "from typing import " in original_content:
                # Add to existing import
                modified_content = re.sub(
                    r'from typing import (.*)',
                    r'from typing import Optional, \1',
                    original_content
                )
            else:
                # Add new import line
                modified_content = import_optional + "\n" + original_content
        else:
            modified_content = original_content
        
        # Replace the original class with the modified one
        modified_content = modified_content.replace(class_def, modified_class)
        
        # Write the modified content back to the file
        with open(file_path, 'w') as f:
            f.write(modified_content)
        
        print(f"✅ Fixed validation issues in {class_name} class")
        return True
    else:
        print("✅ No validation issues found in knowledge item class")
        return True

def main():
    """Main function to fix knowledge base implementation."""
    kb_module_path = find_knowledge_base_module()
    if kb_module_path:
        success = fix_knowledge_base_class(kb_module_path)
        if success:
            print("\n✅ Successfully fixed knowledge base implementation")
            return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
