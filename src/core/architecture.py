"""
Architectural layer definitions and import rules for Egypt Tourism Chatbot.

This module defines the clean architecture layers and validation rules
established in Phase 0C of the dependency untangling process.

LAYER HIERARCHY (dependencies flow downward only):
1. API Layer (src/api/) - HTTP endpoints, request/response handling
2. Service Layer (src/services/) - Business logic, orchestration  
3. Core Layer (src/core/) - Domain models, interfaces, business rules
4. Infrastructure Layer (src/knowledge/, src/session/, src/nlu/) - External systems
5. Utility Layer (src/utils/) - Pure utilities, no business logic

IMPORT RULES:
- Higher layers can import lower layers
- Lower layers CANNOT import higher layers
- Same layer imports are allowed
- Cross-cutting concerns (logging, config) allowed everywhere
"""

import os
import ast
import sys
from typing import List, Dict, Set, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Define architectural layers
ARCHITECTURAL_LAYERS = {
    'api': {
        'level': 1,
        'description': 'HTTP endpoints, request/response handling',
        'directories': ['src/api/'],
        'can_import_from': ['services', 'core', 'infrastructure', 'utils']
    },
    'services': {
        'level': 2, 
        'description': 'Business logic, orchestration',
        'directories': ['src/services/'],
        'can_import_from': ['core', 'infrastructure', 'utils']
    },
    'core': {
        'level': 3,
        'description': 'Domain models, interfaces, business rules',
        'directories': ['src/core/'],
        'can_import_from': ['utils']  # Core should be independent
    },
    'infrastructure': {
        'level': 4,
        'description': 'External systems, databases, NLU, knowledge management',
        'directories': ['src/knowledge/', 'src/session/', 'src/nlu/', 'src/repositories/', 'src/dialog/', 'src/response/', 'src/rag/', 'src/integration/'],
        'can_import_from': ['core', 'utils']
    },
    'utils': {
        'level': 5,
        'description': 'Pure utilities, no business logic',
        'directories': ['src/utils/'],
        'can_import_from': []  # Pure utilities - no business dependencies
    }
}

# Cross-cutting concerns allowed everywhere
CROSS_CUTTING_MODULES = {
    'logging', 'time', 'datetime', 'json', 'os', 'sys', 'typing',
    'collections', 'functools', 'itertools', 'uuid', 'hashlib',
    'threading', 'asyncio', 'concurrent.futures'
}

class ImportViolation:
    """Represents an architectural import violation"""
    
    def __init__(self, file_path: str, import_statement: str, 
                 from_layer: str, to_layer: str, violation_type: str):
        self.file_path = file_path
        self.import_statement = import_statement
        self.from_layer = from_layer
        self.to_layer = to_layer
        self.violation_type = violation_type
    
    def __str__(self):
        return f"{self.violation_type}: {self.file_path} -> {self.import_statement} ({self.from_layer} -> {self.to_layer})"

def get_layer_for_path(file_path: str) -> str:
    """Determine which architectural layer a file belongs to"""
    normalized_path = file_path.replace('\\', '/').replace('./', '')
    
    for layer_name, layer_info in ARCHITECTURAL_LAYERS.items():
        for directory in layer_info['directories']:
            if normalized_path.startswith(directory):
                return layer_name
    
    # Special cases
    if normalized_path.startswith('src/chatbot.py') or normalized_path.startswith('src/main.py'):
        return 'api'  # Main entry points
    elif normalized_path.startswith('src/config'):
        return 'core'  # Configuration
    elif normalized_path.startswith('src/models/'):
        return 'core'  # Domain models
    elif normalized_path.startswith('src/handlers/'):
        return 'infrastructure'  # Event handlers
    elif normalized_path.startswith('src/middleware/'):
        return 'infrastructure'  # Middleware
    
    return 'unknown'

def extract_imports_from_file(file_path: str) -> List[str]:
    """Extract all import statements from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    except Exception as e:
        logger.warning(f"Failed to parse imports from {file_path}: {e}")
        return []

def is_allowed_import(from_layer: str, import_statement: str) -> bool:
    """Check if an import is allowed based on architectural rules"""
    # Allow cross-cutting concerns
    root_module = import_statement.split('.')[0]
    if root_module in CROSS_CUTTING_MODULES:
        return True
    
    # Allow external libraries (not starting with 'src')
    if not import_statement.startswith('src'):
        return True
    
    # Determine target layer
    # Convert import to file path approximation
    import_path = import_statement.replace('.', '/') + '.py'
    to_layer = get_layer_for_path(import_path)
    
    if to_layer == 'unknown':
        return True  # Allow unknown imports for now
    
    # Check if import is allowed based on layer rules
    from_layer_info = ARCHITECTURAL_LAYERS.get(from_layer, {})
    allowed_layers = from_layer_info.get('can_import_from', [])
    
    return to_layer in allowed_layers or from_layer == to_layer

def validate_import_structure() -> List[ImportViolation]:
    """Validate that import structure follows architectural rules"""
    violations = []
    src_path = Path('src')
    
    if not src_path.exists():
        logger.error("src directory not found")
        return violations
    
    # Scan all Python files in src
    for py_file in src_path.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        file_path = str(py_file)
        from_layer = get_layer_for_path(file_path)
        
        if from_layer == 'unknown':
            continue
        
        imports = extract_imports_from_file(file_path)
        
        for import_stmt in imports:
            if not is_allowed_import(from_layer, import_stmt):
                import_path = import_stmt.replace('.', '/') + '.py'
                to_layer = get_layer_for_path(import_path)
                
                violation = ImportViolation(
                    file_path=file_path,
                    import_statement=import_stmt,
                    from_layer=from_layer,
                    to_layer=to_layer,
                    violation_type="LAYER_VIOLATION"
                )
                violations.append(violation)
    
    return violations

def generate_layer_report() -> Dict:
    """Generate a report of the current layer structure"""
    src_path = Path('src')
    layer_stats = {layer: {'files': 0, 'lines': 0} for layer in ARCHITECTURAL_LAYERS.keys()}
    layer_stats['unknown'] = {'files': 0, 'lines': 0}
    
    for py_file in src_path.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        file_path = str(py_file)
        layer = get_layer_for_path(file_path)
        
        layer_stats[layer]['files'] += 1
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                layer_stats[layer]['lines'] += len(f.readlines())
        except Exception:
            pass
    
    return layer_stats

def print_architectural_summary():
    """Print a summary of the architectural layers"""
    print("🏗️  ARCHITECTURAL LAYERS:")
    print("=" * 50)
    
    for layer_name, layer_info in ARCHITECTURAL_LAYERS.items():
        print(f"{layer_info['level']}. {layer_name.upper()} LAYER")
        print(f"   📁 {', '.join(layer_info['directories'])}")
        print(f"   📋 {layer_info['description']}")
        can_import = layer_info['can_import_from']
        if can_import:
            print(f"   ⬇️  Can import from: {', '.join(can_import)}")
        else:
            print(f"   ⬇️  Can import from: none (leaf layer)")
        print()

if __name__ == '__main__':
    print_architectural_summary()
    
    violations = validate_import_structure()
    if violations:
        print(f"❌ Found {len(violations)} import violations:")
        for violation in violations[:10]:  # Show first 10
            print(f"   {violation}")
        if len(violations) > 10:
            print(f"   ... and {len(violations) - 10} more")
    else:
        print("✅ No import violations found")
    
    layer_report = generate_layer_report()
    print("\n📊 LAYER STATISTICS:")
    for layer, stats in layer_report.items():
        if stats['files'] > 0:
            print(f"   {layer}: {stats['files']} files, {stats['lines']} lines") 