#!/usr/bin/env python3
# populate_data.py - Main script to populate the Egypt tourism chatbot database

import os
import json
import importlib.util
import subprocess
import time
from datetime import datetime

def log_message(message):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        log_message(f"Created directory: {directory}")

def run_script(script_name):
    """Run a Python script and return its output"""
    log_message(f"Running {script_name}...")
    
    try:
        # Use subprocess to run the script
        result = subprocess.run(['python', f'./scripts/data_population/{script_name}'], 
                               capture_output=True, text=True, check=True)
        
        log_message(f"Successfully completed {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Error running {script_name}: {e}")
        log_message(f"Output: {e.output}")
        log_message(f"Error: {e.stderr}")
        return False

def create_index_file():
    """Create an index file with metadata about all available data"""
    log_message("Creating data index file...")
    
    index = {
        "last_updated": datetime.now().isoformat(),
        "categories": {},
        "entity_count": 0
    }
    
    # Scan all directories in the data folder
    for category in os.listdir("./data"):
        category_path = os.path.join("./data", category)
        
        # Skip if not a directory or hidden
        if not os.path.isdir(category_path) or category.startswith('.') or category == "sessions":
            continue
        
        # Create category entry
        index["categories"][category] = {
            "count": 0,
            "entities": []
        }
        
        # Scan all files in the category
        for filename in os.listdir(category_path):
            if not filename.endswith('.json') or filename.startswith('.'):
                continue
                
            file_path = os.path.join(category_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract entity info
                entity_info = {
                    "id": data.get("id", filename.replace(".json", "")),
                    "name": data.get("name", {}).get("en", "Unknown"),
                    "file": filename,
                    "type": data.get("type", "unknown")
                }
                
                # Add to index
                index["categories"][category]["entities"].append(entity_info)
                index["categories"][category]["count"] += 1
                index["entity_count"] += 1
                
            except Exception as e:
                log_message(f"Error processing {file_path}: {e}")
    
    # Write index file
    with open("./data/index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    log_message(f"Index file created with {index['entity_count']} entities across {len(index['categories'])} categories")
    return index

def main():
    """Main function to execute data population"""
    start_time = time.time()
    log_message("Starting Egypt Tourism Chatbot data population")
    
    # Create the data population directory if it doesn't exist
    ensure_dir("./scripts/data_population")
    
    # Create necessary data directories
    data_directories = [
        "./data/schemas",
        "./data/attractions",
        "./data/attractions/historical",
        "./data/attractions/cultural",
        "./data/attractions/religious",
        "./data/attractions/natural",
        "./data/attractions/modern",
        "./data/attractions/shopping",
        "./data/cities",
        "./data/accommodations",
        "./data/restaurants",
        "./data/transportation",
        "./data/tours",
        "./data/practical_info",
        "./data/events",
        "./data/media"
    ]
    
    for directory in data_directories:
        ensure_dir(directory)
    
    # List of scripts to run
    scripts = [
        "populate_cities.py",
        "populate_attractions.py",
        "populate_restaurants.py",
        "populate_accommodations.py",
        "populate_transportation.py"
    ]
    
    # Run each script
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
    
    # Create index file
    index = create_index_file()
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    log_message(f"Data population completed in {duration:.2f} seconds")
    log_message(f"Successfully ran {success_count}/{len(scripts)} scripts")
    log_message(f"Created {index['entity_count']} entities across {len(index['categories'])} categories")
    
    # Instructions for next steps
    log_message("\nNext steps:")
    log_message("1. Check the data directories for accuracy")
    log_message("2. Update your chatbot to use the new data")
    log_message("3. Consider adding more data to improve coverage")
    log_message("4. Implement database migration if needed")

if __name__ == "__main__":
    main()
