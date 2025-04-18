#!/usr/bin/env python3
"""
Comprehensive linting script for the Egypt Tourism Chatbot project.
This script performs:
- PEP8 style checking using flake8
- Import validation
- Type hint verification
- JSON/YAML configuration validation
- Docstring completeness checking
- Consistent naming conventions
"""

import os
import sys
import json
import subprocess
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set, Optional
import yaml  # You might need to pip install pyyaml
from colorama import init, Fore, Style  # You might need to pip install colorama

# Initialize colorama
init()

# Project directories to scan
DIRECTORIES_TO_SCAN = [
    "src",
    "tests",
    "configs"
]

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    r".*\.pyc$",
    r".*\.git.*",
    r".*__pycache__.*",
    r".*\.pytest_cache.*",
    r".*\.venv.*",
    r".*\.env.*"
]

# Maximum line length for code
MAX_LINE_LENGTH = 100

# Minimum required docstring coverage percentage
MIN_DOCSTRING_COVERAGE = 70



def find_python_files() -> List[str]:
    """Find all Python files in the project directories."""
    python_files = []
    
    for directory in DIRECTORIES_TO_SCAN:
        if not os.path.exists(directory):
            print(f"{Fore.YELLOW}Warning: Directory {directory} does not exist{Style.RESET_ALL}")
            continue
            
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Check if file should be excluded
                    exclude = False
                    for pattern in EXCLUDE_PATTERNS:
                        if re.match(pattern, file_path):
                            exclude = True
                            break
                    
                    if not exclude:
                        python_files.append(file_path)
    
    return python_files

def run_flake8(files: List[str]) -> List[Dict[str, Any]]:
    """Run flake8 on the given Python files."""
    flake8_issues = []
    
    try:
        cmd = [
            "flake8",
            "--max-line-length", str(MAX_LINE_LENGTH),
            "--format=%(path)s:%(row)d:%(col)d:%(code)s:%(text)s"
        ] + files
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Parse flake8 output
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                    
                try:
                    file_path, line_num, column, code, message = line.split(':', 4)
                    flake8_issues.append({
                        "file": file_path,
                        "line": int(line_num),
                        "column": int(column),
                        "code": code,
                        "message": message.strip(),
                        "type": "style"
                    })
                except ValueError:
                    print(f"{Fore.YELLOW}Warning: Could not parse flake8 output: {line}{Style.RESET_ALL}")
    
    except FileNotFoundError:
        print(f"{Fore.RED}Error: flake8 not found. Install with 'pip install flake8'{Style.RESET_ALL}")
    
    return flake8_issues


def validate_json_configs() -> List[Dict[str, Any]]:
    """Validate all JSON configuration files in the project."""
    json_issues = []
    
    # Find all JSON files
    json_files = []
    for directory in DIRECTORIES_TO_SCAN:
        if not os.path.exists(directory):
            continue
            
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    json_files.append(file_path)
    
    # Validate each JSON file
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            json_issues.append({
                "file": file_path,
                "line": e.lineno,
                "column": e.colno,
                "code": "JSON",
                "message": f"JSON decode error: {str(e)}",
                "type": "error"
            })
    
    return json_issues

def validate_yaml_configs() -> List[Dict[str, Any]]:
    """Validate all YAML configuration files in the project."""
    yaml_issues = []
    
    # Find all YAML files
    yaml_files = []
    for directory in DIRECTORIES_TO_SCAN:
        if not os.path.exists(directory):
            continue
            
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    yaml_files.append(file_path)
    
    # Validate each YAML file
    for file_path in yaml_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            yaml_issues.append({
                "file": file_path,
                "line": getattr(e, 'problem_mark', {}).get('line', 1),
                "column": getattr(e, 'problem_mark', {}).get('column', 1),
                "code": "YAML",
                "message": f"YAML error: {str(e)}",
                "type": "error"
            })
    
    return yaml_issues

def check_import_errors(files: List[str]) -> List[Dict[str, Any]]:
    """Check for import errors in Python files."""
    import_issues = []
    
    for file_path in files:
        # Get the module name from the file path
        module_path = os.path.splitext(file_path)[0].replace(os.path.sep, '.')
        if module_path.startswith('.'):
            module_path = module_path[1:]
            
        # Try to import the module
        try:
            # Use a subprocess to avoid affecting the current process
            cmd = [sys.executable, '-c', f"import {module_path}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Extract error message
                error_msg = result.stderr.strip()
                match = re.search(r'File ".*", line (\d+)', error_msg)
                line_num = int(match.group(1)) if match else 1
                
                import_issues.append({
                    "file": file_path,
                    "line": line_num,
                    "column": 1,
                    "code": "IMP",
                    "message": f"Import error: {error_msg.split('Error: ')[1] if 'Error: ' in error_msg else error_msg}",
                    "type": "error"
                })
        except Exception as e:
            import_issues.append({
                "file": file_path,
                "line": 1,
                "column": 1,
                "code": "IMP",
                "message": f"Error checking imports: {str(e)}",
                "type": "error"
            })
    
    return import_issues

def check_type_hints(files: List[str]) -> List[Dict[str, Any]]:
    """Check type hints using mypy."""
    type_issues = []
    
    try:
        cmd = ["mypy"] + files
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Parse mypy output
            for line in result.stdout.splitlines():
                if not line.strip() or ': error:' not in line:
                    continue
                
                try:
                    file_path, rest = line.split(':', 1)
                    line_num, rest = rest.split(':', 1)
                    message = rest.strip()
                    
                    type_issues.append({
                        "file": file_path,
                        "line": int(line_num),
                        "column": 1,  # mypy doesn't always provide column info
                        "code": "TYPE",
                        "message": message,
                        "type": "type"
                    })
                except ValueError:
                    print(f"{Fore.YELLOW}Warning: Could not parse mypy output: {line}{Style.RESET_ALL}")
    
    except FileNotFoundError:
        print(f"{Fore.YELLOW}Warning: mypy not found. Install with 'pip install mypy'{Style.RESET_ALL}")
    
    return type_issues

def check_docstring_coverage(files: List[str]) -> List[Dict[str, Any]]:
    """Check docstring coverage for classes and functions."""
    docstring_issues = []
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all function and class definitions
        func_class_pattern = r'(def|class)\s+(\w+)'
        matches = re.finditer(func_class_pattern, content)
        
        for match in matches:
            def_type, name = match.groups()
            start_pos = match.start()
            
            # Get line number
            line_num = content[:start_pos].count('\n') + 1
            
            # Check for docstring
            # Find the end of the definition line
            end_of_def_line = content.find(':', start_pos)
            if end_of_def_line == -1:
                continue
                
            # Look for a docstring after the definition
            next_lines = content[end_of_def_line:end_of_def_line + 100]  # Examine next 100 chars
            has_docstring = '"""' in next_lines[:next_lines.find('\n\n') if '\n\n' in next_lines else len(next_lines)]
            
            if not has_docstring:
                docstring_issues.append({
                    "file": file_path,
                    "line": line_num,
                    "column": 1,
                    "code": "DOC",
                    "message": f"Missing docstring for {def_type} {name}",
                    "type": "docstring"
                })
    
    return docstring_issues

def main():
    """Run the linting process."""
    parser = argparse.ArgumentParser(description='Lint the Egypt Tourism Chatbot project')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print more detailed output')
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}Starting linting for Egypt Tourism Chatbot project...{Style.RESET_ALL}")
    
    # Find all Python files
    print("Finding Python files...")
    python_files = find_python_files()
    print(f"Found {len(python_files)} Python files to analyze")
    
    all_issues = []
    
    # Run flake8
    print("Running flake8 style checks...")
    flake8_issues = run_flake8(python_files)
    all_issues.extend(flake8_issues)
    print(f"Found {len(flake8_issues)} style issues")
    
    # Validate JSON configs
    print("Validating JSON configuration files...")
    json_issues = validate_json_configs()
    all_issues.extend(json_issues)
    print(f"Found {len(json_issues)} JSON issues")
    
    # Validate YAML configs
    print("Validating YAML configuration files...")
    yaml_issues = validate_yaml_configs()
    all_issues.extend(yaml_issues)
    print(f"Found {len(yaml_issues)} YAML issues")
    
    # Check imports
    print("Checking for import errors...")
    import_issues = check_import_errors(python_files)
    all_issues.extend(import_issues)
    print(f"Found {len(import_issues)} import issues")
    
    # Check type hints
    print("Checking type hints...")
    type_issues = check_type_hints(python_files)
    all_issues.extend(type_issues)
    print(f"Found {len(type_issues)} type hint issues")
    
    # Check docstring coverage
    print("Checking docstring coverage...")
    docstring_issues = check_docstring_coverage(python_files)
    all_issues.extend(docstring_issues)
    print(f"Found {len(docstring_issues)} docstring issues")
    
    # Calculate docstring coverage
    total_functions = 0
    functions_with_docstrings = 0
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        func_class_matches = re.finditer(r'(def|class)\s+(\w+)', content)
        for match in func_class_matches:
            total_functions += 1
            
            start_pos = match.start()
            end_of_def_line = content.find(':', start_pos)
            if end_of_def_line != -1:
                next_lines = content[end_of_def_line:end_of_def_line + 100]
                if '"""' in next_lines[:next_lines.find('\n\n') if '\n\n' in next_lines else len(next_lines)]:
                    functions_with_docstrings += 1

    coverage = (functions_with_docstrings / total_functions * 100) if total_functions > 0 else 100
    print(f"Docstring coverage: {coverage:.1f}% (minimum required: {MIN_DOCSTRING_COVERAGE}%)")

    if coverage < MIN_DOCSTRING_COVERAGE:
        print(f"{Fore.RED}⚠ Docstring coverage below minimum threshold!{Style.RESET_ALL}")
    
    # Group issues by file
    issues_by_file = {}
    for issue in all_issues:
        file_path = issue["file"]
        if file_path not in issues_by_file:
            issues_by_file[file_path] = []
        issues_by_file[file_path].append(issue)
    
    # Print issues
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}LINT RESULTS{Style.RESET_ALL}")
    print("=" * 80)
    
    if not all_issues:
        print(f"{Fore.GREEN}No issues found! Your code is looking good.{Style.RESET_ALL}")
    else:
        for file_path, issues in sorted(issues_by_file.items()):
            print(f"\n{Fore.BLUE}{file_path}{Style.RESET_ALL}:")
            
            # Sort issues by line number
            for issue in sorted(issues, key=lambda x: (x["line"], x["column"])):
                line = issue["line"]
                message = issue["message"]
                code = issue["code"]
                
                if issue["type"] == "error":
                    color = Fore.RED
                elif issue["type"] == "style":
                    color = Fore.YELLOW
                else:
                    color = Fore.MAGENTA
                
                print(f"  {line}:{color}{code}{Style.RESET_ALL} - {message}")
    
    if args.verbose:
        print(f"\n{Fore.CYAN}Detailed information for issues:{Style.RESET_ALL}")
        for issue in all_issues:
            print(f"{Fore.BLUE}{issue['file']}:{issue['line']}:{issue['column']}{Style.RESET_ALL} - "
                  f"{issue['code']}: {issue['message']}")
    
    # Print summary
    print("\n" + "-" * 80)
    total_issues = len(all_issues)
    if total_issues > 0:
        print(f"{Fore.RED}Found {total_issues} issues{Style.RESET_ALL}")
        
        # Calculate issue counts by type
        issue_types = {}
        for issue in all_issues:
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        for issue_type, count in issue_types.items():
            print(f"  - {count} {issue_type} issues")
            
        # Attempt to fix issues if --fix flag is provided
        if args.fix:
            print(f"\n{Fore.CYAN}Attempting to fix issues...{Style.RESET_ALL}")
            fix_issues(all_issues)
    else:
        print(f"{Fore.GREEN}No issues found! Your code is looking good.{Style.RESET_ALL}")
    
    # Exit with appropriate code
    return 1 if total_issues > 0 else 0

def fix_issues(issues: List[Dict[str, Any]]) -> None:
    """Attempt to fix some of the issues automatically."""
    # Group issues by file
    issues_by_file = {}
    for issue in issues:
        file_path = issue["file"]
        if file_path not in issues_by_file:
            issues_by_file[file_path] = []
        issues_by_file[file_path].append(issue)
    
    for file_path, file_issues in issues_by_file.items():
        # Only try to fix style issues for now
        style_issues = [i for i in file_issues if i["type"] == "style"]
        if not style_issues:
            continue
            
        print(f"Fixing style issues in {file_path}...")
        
        # Use autopep8 to fix style issues
        try:
            subprocess.run(["autopep8", "--in-place", file_path], check=True)
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Applied autopep8 fixes")
        except (subprocess.SubprocessError, FileNotFoundError):
            print(f"  {Fore.YELLOW}⚠{Style.RESET_ALL} Failed to run autopep8. Install with 'pip install autopep8'")
        
        # In fix_issues(), expand to handle docstrings:
        # Add docstring templates for missing docstrings
        docstring_issues = [i for i in file_issues if i["type"] == "docstring"]
        if docstring_issues and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.readlines()
                    
                modified = False
                for issue in docstring_issues:
                    line_num = issue["line"] - 1  # 0-based indexing
                    if line_num < len(content):
                        indent = re.match(r'(\s*)', content[line_num]).group(1)
                        if 'def ' in content[line_num]:
                            docstring = f'{indent}    """TODO: Add function description here."""\n'
                            content.insert(line_num + 1, docstring)
                            modified = True
                        elif 'class ' in content[line_num]:
                            docstring = f'{indent}    """TODO: Add class description here."""\n'
                            content.insert(line_num + 1, docstring)
                            modified = True
                            
                if modified:
                    with open(file_path, 'w') as f:
                        f.writelines(content)
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Added docstring templates")
                        
            except Exception as e:
                print(f"  {Fore.YELLOW}⚠{Style.RESET_ALL} Failed to add docstrings: {str(e)}")

if __name__ == "__main__":
    sys.exit(main())



# import os
# import sys
# import json
# import subprocess
# import argparse
# import re
# from pathlib import Path
# from typing import Dict, List, Tuple, Any, Set, Optional
# import yaml  # You might need to pip install pyyaml
# from colorama import init, Fore, Style  # You might need to pip install colorama
#
# # Initialize colorama
# init()
#
# # Project directories to scan
# DIRECTORIES_TO_SCAN = [
#     "src",
#     "tests",
#     "configs"
# ]
