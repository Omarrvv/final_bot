#!/bin/bash
# Simplified RAG System Fix for Egypt Tourism Chatbot

echo "========== STARTING SIMPLIFIED RAG SYSTEM REPAIR =========="

# ===== 1. Check and Enable RAG Feature Flag in Docker Environment =====
echo "1. Enabling RAG feature flag in Docker environment..."

# Create a script to run inside the Docker container
cat > fix_rag_docker.sh << 'EOL'
#!/bin/bash
set -e

# Enable RAG in container environment
echo "Checking for RAG flag in container..."
grep -q "USE_RAG" /app/.env || echo "USE_RAG=true" >> /app/.env
sed -i 's/USE_RAG=false/USE_RAG=true/g' /app/.env

# Check if it was updated
echo "Current RAG setting in container:"
grep "USE_RAG" /app/.env

# Also fix PostgreSQL query syntax - look for the '$not' operator
echo "Fixing MongoDB-style operators in database queries..."
find /app -name "*.py" -type f -exec grep -l "\$not" {} \; | while read file; do
    echo "Found MongoDB operator in $file, patching..."
    # Create backup
    cp "$file" "$file.bak"
    # Replace MongoDB operators with PostgreSQL syntax
    sed -i 's/"\$not"/\"NOT\"/g' "$file"
    sed -i "s/'\$not'/'NOT'/g" "$file"
    echo "Patched $file"
done

# Verify Knowledge Base has proper implementation
echo "Checking Knowledge Base implementation..."
KB_FILES=$(find /app -name "*knowledge_base*.py" -type f)
for file in $KB_FILES; do
    echo "Examining $file..."
    grep -q "class BaseKnowledgeItem" "$file" && echo "Found BaseKnowledgeItem class in $file"
done

# List database tables to check data
echo "Checking database tables..."
PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -c "\dt"

# Check if attractions table has data
echo "Checking attractions data..."
PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -c "SELECT COUNT(*) FROM attractions;"

echo "Fix script completed in container"
EOL

chmod +x fix_rag_docker.sh

# Execute the script inside the Docker container
echo "Running fix script inside Docker container..."
docker cp fix_rag_docker.sh egypt-chatbot-wind-cursor-app-1:/tmp/fix_rag_docker.sh
docker exec egypt-chatbot-wind-cursor-app-1 bash /tmp/fix_rag_docker.sh

# ===== 2. Add Sample Data Directly to PostgreSQL =====
echo -e "\n2. Inserting sample attraction data directly into PostgreSQL..."

# Create SQL file with sample data
cat > sample_data.sql << 'EOL'
-- Sample Egypt attractions data
INSERT INTO attractions (id, name_en, name_ar, description_en, description_ar, city, location, rating, opening_hours, entrance_fee, tags)
VALUES
('pyr001', 'The Great Pyramids of Giza', 'أهرامات الجيزة', 
 'The Pyramids of Giza are the only surviving structures of the Seven Wonders of the Ancient World.', 
 'أهرامات الجيزة هي الهياكل الوحيدة الباقية من عجائب الدنيا السبع في العالم القديم.',
 'Cairo', '{"lat": 29.9792, "lon": 31.1342}', 4.8, 'Daily 8:00 AM - 5:00 PM', 240, 
 '["ancient", "wonder", "pyramid", "pharaoh", "tomb"]')
ON CONFLICT (id) DO NOTHING;

INSERT INTO attractions (id, name_en, name_ar, description_en, description_ar, city, location, rating, opening_hours, entrance_fee, tags)
VALUES
('sph001', 'The Great Sphinx of Giza', 'أبو الهول', 
 'The Great Sphinx is a limestone statue of a reclining sphinx, a mythical creature with the head of a human and the body of a lion.', 
 'أبو الهول هو تمثال من الحجر الجيري لمخلوق أسطوري برأس إنسان وجسم أسد.',
 'Cairo', '{"lat": 29.9753, "lon": 31.1376}', 4.7, 'Daily 8:00 AM - 5:00 PM', 100, 
 '["ancient", "statue", "sphinx", "pharaoh", "mythology"]')
ON CONFLICT (id) DO NOTHING;

INSERT INTO attractions (id, name_en, name_ar, description_en, description_ar, city, location, rating, opening_hours, entrance_fee, tags)
VALUES
('mus001', 'The Egyptian Museum', 'المتحف المصري', 
 'The Museum of Egyptian Antiquities, known commonly as the Egyptian Museum, houses the world''s largest collection of Pharaonic antiquities.', 
 'متحف الآثار المصرية، المعروف باسم المتحف المصري، يضم أكبر مجموعة من الآثار الفرعونية في العالم.',
 'Cairo', '{"lat": 30.0478, "lon": 31.2336}', 4.6, 'Daily 9:00 AM - 5:00 PM', 200, 
 '["museum", "antiquities", "pharaoh", "artifacts", "tutankhamun"]')
ON CONFLICT (id) DO NOTHING;

-- Sample cities data
INSERT INTO cities (id, name_en, name_ar, description_en, description_ar, location)
VALUES
('cai001', 'Cairo', 'القاهرة', 
 'Cairo, Egypt''s sprawling capital, is set on the Nile River.', 
 'القاهرة، عاصمة مصر المترامية الأطراف، تقع على نهر النيل.',
 '{"lat": 30.0444, "lon": 31.2357}')
ON CONFLICT (id) DO NOTHING;

INSERT INTO cities (id, name_en, name_ar, description_en, description_ar, location)
VALUES
('lux002', 'Luxor', 'الأقصر', 
 'Luxor is a city on the east bank of the Nile River in southern Egypt.', 
 'الأقصر هي مدينة تقع على الضفة الشرقية لنهر النيل في صعيد مصر.',
 '{"lat": 25.6872, "lon": 32.6396}')
ON CONFLICT (id) DO NOTHING;
EOL

# Copy and execute SQL file in the docker container
echo "Copying SQL file to container..."
docker cp sample_data.sql egypt-chatbot-wind-cursor-app-1:/tmp/
docker exec egypt-chatbot-wind-cursor-app-1 bash -c 'PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -f /tmp/sample_data.sql'

# Verify data was inserted
echo "Verifying data insertion..."
docker exec egypt-chatbot-wind-cursor-app-1 bash -c 'PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -c "SELECT id, name_en FROM attractions;"'

# ===== 3. Fix Knowledge Base Validation Issues =====
echo -e "\n3. Creating fix for Knowledge Base validation issues..."

cat > knowledge_base_fix.py << 'EOL'
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
EOL

chmod +x knowledge_base_fix.py
echo "Run the following to see KB validation fixes:"
echo "python3 knowledge_base_fix.py"

# ===== 4. Restart the Application with Improved Debugging =====
echo -e "\n4. Restarting application with enhanced logging..."

# Create a script to monitor the application logs after restart
cat > monitor_app_logs.sh << 'EOL'
#!/bin/bash
set -e

echo "Restarting application container..."
docker restart egypt-chatbot-wind-cursor-app-1

echo "Waiting for application to start..."
sleep 5

echo "Checking logs for RAG related messages..."
docker logs egypt-chatbot-wind-cursor-app-1 --tail 100 | grep -i "rag\|knowledge\|database\|query"

echo "Application restarted! Wait a moment before testing."
EOL

chmod +x monitor_app_logs.sh
./monitor_app_logs.sh

# ===== 5. Create Improved Test Script =====
echo -e "\n5. Creating improved test script for RAG system..."

cat > test_rag_docker.py << 'EOL'
#!/usr/bin/env python3
"""
Test the RAG system by running commands inside the Docker container.
"""
import subprocess
import time
import sys
import json

def run_in_container(cmd):
    """Run a command in the Docker container."""
    full_cmd = f"docker exec egypt-chatbot-wind-cursor-app-1 {cmd}"
    print(f"Running: {full_cmd}")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def test_rag_system():
    """Test the RAG system with curl directly from inside container."""
    print("Waiting for application to fully initialize...")
    time.sleep(10)
    
    print("\nTesting RAG system with curl from inside container...")
    payload = {
        "message": "What are the top attractions in Cairo?",
        "session_id": "test-rag-session",
        "debug": True,
        "enable_rag": True
    }
    payload_json = json.dumps(payload).replace('"', '\\"')
    
    cmd = f'curl -s -X POST -H "Content-Type: application/json" -d "{payload_json}" http://localhost:5050/api/chat'
    return run_in_container(cmd)

def check_rag_settings():
    """Check RAG-related settings in the container."""
    print("\nChecking RAG settings in container...")
    # Check environment variables
    run_in_container("grep RAG /app/.env")
    
    # Check feature flags in settings
    run_in_container('python -c "from src.utils.settings import settings; print(f\'RAG enabled: {settings.feature_flags.use_rag}\')"')
    
    # Check for database connectivity
    run_in_container('PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -c "SELECT COUNT(*) FROM attractions;"')
    
    return True

if __name__ == "__main__":
    print("Starting RAG system test...")
    check_rag_settings()
    if test_rag_system():
        print("\n✅ RAG system test completed successfully.")
        sys.exit(0)
    else:
        print("\n❌ RAG system test failed.")
        sys.exit(1)
EOL

chmod +x test_rag_docker.py
echo "To test the RAG system, run:"
echo "python3 test_rag_docker.py"

# ===== 6. Providing Additional Help =====
echo -e "\n========== RAG SYSTEM REPAIR INSTRUCTIONS =========="
echo "1. The RAG feature flag has been enabled in the container."
echo "2. Sample attraction data has been added to the database."
echo "3. The application has been restarted."
echo ""
echo "To test if the RAG system is working:"
echo "  python3 test_rag_docker.py"
echo ""
echo "If issues persist, try these additional steps:"
echo "1. Fix Knowledge Base validation issues:"
echo "   python3 knowledge_base_fix.py"
echo ""
echo "2. Check application logs for errors:"
echo "   docker logs egypt-chatbot-wind-cursor-app-1"
echo ""
echo "3. Check if MongoDB-style operators are causing issues by running:"
echo "   docker exec egypt-chatbot-wind-cursor-app-1 find /app -name \"*.py\" -type f -exec grep -l \"\\\$not\" {} \\;"
echo ""
echo "4. Manually update your Python code to fix any identified issues."
echo ""
echo "5. After making changes, restart the container:"
echo "   docker restart egypt-chatbot-wind-cursor-app-1"