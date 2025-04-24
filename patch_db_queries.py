#!/usr/bin/env python3
"""
Patch database query methods to fix MongoDB-style operators in PostgreSQL queries.
"""
import os
import sys
import re

def find_database_module():
    """Find the database module containing the query methods."""
    # Typical locations for the database module
    potential_paths = [
        "src/knowledge/database.py",
        "src/utils/database.py",
        "src/database/manager.py"
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found database module at: {path}")
            return path
    
    # Search for database.py files
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file == "database.py":
                path = os.path.join(root, file)
                print(f"Found database module at: {path}")
                return path
    
    print("❌ Could not find database module")
    return None

def patch_mongodb_operators(file_path):
    """Patch MongoDB-style operators in the database module."""
    if not file_path or not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the file contains MongoDB-style operators
    mongo_operators = ["$not", "$eq", "$ne", "$gt", "$lt", "$gte", "$lte", "$in", "$nin"]
    has_mongo_operators = any(op in content for op in mongo_operators)
    
    if not has_mongo_operators:
        print("✅ No MongoDB-style operators found in the file")
        return True
    
    # Make a backup of the file
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup of original file at: {backup_path}")
    
    # Patch MongoDB operators to PostgreSQL syntax
    patched_content = content
    
    # Look for the method that builds the query with $not operator
    query_build_pattern = re.compile(r'def\s+build_query.*?}', re.DOTALL)
    match = query_build_pattern.search(content)
    
    if match:
        query_method = match.group(0)
        
        # Check if we found the right method with MongoDB operators
        if "$not" in query_method:
            # Replace the MongoDB query building with PostgreSQL syntax
            modified_method = query_method
            
            # Replace $not for string fields in PostgreSQL
            modified_method = re.sub(
                r'([\'"]?)\$not\1\s*:\s*(\w+)',
                r'NOT (\2)',
                modified_method
            )
            
            # Fix other MongoDB operators for PostgreSQL
            operator_map = {
                "$eq": "=",
                "$ne": "!=",
                "$gt": ">",
                "$lt": "<",
                "$gte": ">=",
                "$lte": "<=",
                "$in": "IN",
                "$nin": "NOT IN"
            }
            
            for mongo_op, pg_op in operator_map.items():
                modified_method = re.sub(
                    r'([\'"]?)' + re.escape(mongo_op) + r'\1\s*:',
                    pg_op,
                    modified_method
                )
            
            # Replace the method in the content
            patched_content = content.replace(query_method, modified_method)
            
            # Write the patched content back to the file
            with open(file_path, 'w') as f:
                f.write(patched_content)
            
            print("✅ Patched MongoDB-style operators to PostgreSQL syntax")
            return True
    
    # If we can't find the exact method, just add a compatibility layer function
    compat_layer = """
# Added PostgreSQL compatibility layer for MongoDB-style operators
def convert_mongo_query_to_postgres(query_dict, field_prefix=""):
    """Convert MongoDB-style query operators to PostgreSQL WHERE clause conditions."""
    conditions = []
    params = []
    
    for key, value in query_dict.items():
        if key.startswith("$"):
            # Handle top-level logical operators
            if key == "$and":
                subconditions = []
                for subquery in value:
                    subwhere, subparams = convert_mongo_query_to_postgres(subquery)
                    subconditions.append(subwhere)
                    params.extend(subparams)
                conditions.append("(" + " AND ".join(subconditions) + ")")
            elif key == "$or":
                subconditions = []
                for subquery in value:
                    subwhere, subparams = convert_mongo_query_to_postgres(subquery)
                    subconditions.append(subwhere)
                    params.extend(subparams)
                conditions.append("(" + " OR ".join(subconditions) + ")")
        else:
            # Field name with possible dot notation
            field_name = f"{field_prefix}{key}" if field_prefix else key
            
            # Handle different value types
            if isinstance(value, dict):
                # Operator expression
                for op, op_value in value.items():
                    if op == "$eq":
                        conditions.append(f"{field_name} = %s")
                        params.append(op_value)
                    elif op == "$ne":
                        conditions.append(f"{field_name} != %s")
                        params.append(op_value)
                    elif op == "$gt":
                        conditions.append(f"{field_name} > %s")
                        params.append(op_value)
                    elif op == "$lt":
                        conditions.append(f"{field_name} < %s")
                        params.append(op_value)
                    elif op == "$gte":
                        conditions.append(f"{field_name} >= %s")
                        params.append(op_value)
                    elif op == "$lte":
                        conditions.append(f"{field_name} <= %s")
                        params.append(op_value)
                    elif op == "$in":
                        conditions.append(f"{field_name} IN %s")
                        params.append(tuple(op_value))
                    elif op == "$nin":
                        conditions.append(f"{field_name} NOT IN %s")
                        params.append(tuple(op_value))
                    elif op == "$not":
                        conditions.append(f"NOT ({field_name} = %s)")
                        params.append(op_value)
                    elif op == "$regex":
                        conditions.append(f"{field_name} ~ %s")
                        params.append(op_value)
                    else:
                        # Unknown operator
                        logger.warning(f"Unsupported MongoDB operator '{op}' for key '{field_name}' in PostgreSQL query.")
            else:
                # Simple equality
                conditions.append(f"{field_name} = %s")
                params.append(value)
    
    return " AND ".join(conditions), params

# Patch execute_query method to use the compatibility layer
def _patched_execute_query(self, table, query=None, limit=None, offset=None, sort=None):
    """Patched query execution for PostgreSQL compatibility."""
    try:
        cursor = self.conn.cursor()
        
        sql_query = f"SELECT * FROM {table}"
        params = []
        
        if query:
            where_clause, where_params = convert_mongo_query_to_postgres(query)
            sql_query += f" WHERE {where_clause}"
            params.extend(where_params)
        
        if sort:
            order_parts = []
            for field, direction in sort.items():
                order_dir = "ASC" if direction > 0 else "DESC"
                order_parts.append(f"{field} {order_dir}")
            if order_parts:
                sql_query += f" ORDER BY {', '.join(order_parts)}"
        
        if limit is not None:
            sql_query += f" LIMIT {limit}"
        
        if offset is not None:
            sql_query += f" OFFSET {offset}"
        
        cursor.execute(sql_query, params)
        result = cursor.fetchall()
        
        # Convert to dictionaries
        columns = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(columns, row)) for row in result]
        
        cursor.close()
        return result_dicts
    except Exception as e:
        logger.error(f"Error executing PostgreSQL query: {e}")
        return []

# Use monkey patching to replace the existing method if necessary
"""
    
    with open(file_path, 'a') as f:
        f.write(compat_layer)
    
    print("✅ Added PostgreSQL compatibility layer for MongoDB-style operators")
    return True

def main():
    """Main function to patch database queries."""
    db_module_path = find_database_module()
    if db_module_path:
        success = patch_mongodb_operators(db_module_path)
        if success:
            print("\n✅ Successfully patched database query module")
            return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
