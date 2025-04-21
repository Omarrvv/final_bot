def fix_duplicated_database_methods():
    file_path = "src/knowledge/database.py"
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # 1. Make a backup of the original file
    with open(f"{file_path}.bak", 'w') as backup:
        backup.write(content)
        print(f"✅ Created backup at {file_path}.bak")
    
    # 2. Fix duplicate _create_sqlite_fts_tables method
    # Count occurrences to verify duplication
    fts_count = content.count("def _create_sqlite_fts_tables")
    print(f"Found {fts_count} instances of '_create_sqlite_fts_tables'")
    
    if fts_count > 1:
        # Keep only the first definition
        first_occurrence = content.find("def _create_sqlite_fts_tables")
        next_occurrence = content.find("def _create_sqlite_fts_tables", first_occurrence + 10)
        
        if next_occurrence > 0:
            # Find the end of the first method
            next_def_after_first = content.find("\n    def ", first_occurrence + 10)
            # Find the beginning of the method after the duplicate
            next_def_after_duplicate = content.find("\n    def ", next_occurrence + 10)
            
            if next_def_after_first > 0 and next_def_after_duplicate > 0:
                # Remove the duplicate method
                content = content[:next_occurrence] + content[next_def_after_duplicate:]
                print("✅ Removed duplicate '_create_sqlite_fts_tables' method")
    
    # 3. Fix duplicate full_text_search method
    search_count = content.count("def full_text_search")
    print(f"Found {search_count} instances of 'full_text_search'")
    
    if search_count > 1:
        # Keep only the first definition
        first_occurrence = content.find("def full_text_search")
        next_occurrence = content.find("def full_text_search", first_occurrence + 10)
        
        if next_occurrence > 0:
            # Find the end of the first method
            next_def_after_first = content.find("\n    def ", first_occurrence + 10)
            # Find the beginning of the method after the duplicate
            next_def_after_duplicate = content.find("\n    def ", next_occurrence + 10)
            
            if next_def_after_first > 0 and next_def_after_duplicate > 0:
                # Remove the duplicate method
                content = content[:next_occurrence] + content[next_def_after_duplicate:]
                print("✅ Removed duplicate 'full_text_search' method")
    
    # 4. Fix duplicate log_analytics_event method
    analytics_count = content.count("def log_analytics_event")
    print(f"Found {analytics_count} instances of 'log_analytics_event'")
    
    if analytics_count > 1:
        # Keep only the final complete implementation
        first_occurrence = content.find("def log_analytics_event")
        
        # Find all occurrences and keep the most complete one (the last one)
        occurrences = []
        pos = first_occurrence
        while pos >= 0:
            occurrences.append(pos)
            pos = content.find("def log_analytics_event", pos + 10)
        
        # Keep the last implementation and remove others
        if len(occurrences) > 1:
            keep_pos = occurrences[-1]
            
            # Build new content
            new_content = content[:first_occurrence]
            new_content += content[keep_pos:]
            
            content = new_content
            print(f"✅ Removed {len(occurrences)-1} duplicate 'log_analytics_event' methods")
    
    # 5. Remove any incomplete method fragments
    if "        Returns:" in content:
        # Find all dangling Returns: statements
        pos = content.find("        Returns:")
        while pos >= 0:
            # Check if it's a standalone fragment
            next_def = content.find("\n    def ", pos)
            if next_def > 0:
                fragment_start = content.rfind("\n\n", 0, pos)
                if fragment_start > 0:
                    # Remove the fragment
                    content = content[:fragment_start] + content[next_def:]
                    print("✅ Removed incomplete method fragment")
            
            # Look for next occurrence
            pos = content.find("        Returns:", pos + 10)
    
    # Write the fixed content back to the file
    with open(file_path, 'w') as file:
        file.write(content)
        print(f"✅ Updated {file_path}")
    
    return True

if __name__ == "__main__":
    fix_duplicated_database_methods()
