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
