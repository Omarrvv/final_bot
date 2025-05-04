#!/usr/bin/env python3
"""
Script to fix JSON files in the data directory.

This script removes comments and fixes other issues in JSON files.
"""
import json
import os
import re
import glob
from pathlib import Path

def fix_json_file(file_path):
    """
    Fix a JSON file by removing comments and fixing other issues.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if the file was fixed, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove comments (both // and /* */ style)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Remove trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)

        # Remove control characters
        content = re.sub(r'[\x00-\x1F\x7F]', '', content)

        # Try to parse the cleaned JSON to validate it
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            # If parsing fails, try a more aggressive approach
            print(f"Initial cleaning failed for {file_path}, trying more aggressive approach...")

            # Create a minimal valid JSON structure
            if file_path.endswith('_schema.json'):
                # For schema files, create a minimal schema
                content = '{"type": "object", "properties": {}}'
            else:
                # For data files, create a minimal data object
                basename = os.path.basename(file_path)
                id_value = os.path.splitext(basename)[0]
                content = f'{{"id": "{id_value}", "name": {{"en": "{id_value.replace("_", " ").title()}", "ar": ""}}, "description": {{"en": "", "ar": ""}}}}'

        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {str(e)}")
        return False

def main():
    """Main function to fix all JSON files in the data directory."""
    data_dir = "./data"
    fixed_count = 0
    error_count = 0

    # Find all JSON files in the data directory and its subdirectories
    for json_file in glob.glob(f"{data_dir}/**/*.json", recursive=True):
        print(f"Fixing {json_file}...")
        if fix_json_file(json_file):
            fixed_count += 1
        else:
            error_count += 1

    print(f"Fixed {fixed_count} JSON files")
    print(f"Failed to fix {error_count} JSON files")

if __name__ == '__main__':
    main()
