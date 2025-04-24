import os
import json

def initialize_project():
    """Initialize the project structure and configuration files."""
    # Create necessary directories
    directories = [
        "data",
        "data/sessions",
        "data/vector_db",
        "configs",
        "configs/response_templates"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create default configuration files if they don't exist
    if not os.path.exists("configs/models.json"):
        with open("configs/models.json", "w") as f:
            json.dump({
                "language_detection": {
                    "model_path": "lid.176.bin",
                    "confidence_threshold": 0.8
                },
                "nlp_models": {
                    "en": "en_core_web_md",
                    "ar": "xx_ent_wiki_sm"
                }
            }, f, indent=2)
            print("Created models.json")
    
    print("Initialization complete!")

if __name__ == "__main__":
    initialize_project()

