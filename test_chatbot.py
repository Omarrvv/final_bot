# test_chatbot.py
import requests
import json
import csv
from datetime import datetime

class ChatbotTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = self.create_session()
        self.results = []
        
    def create_session(self):
        response = requests.post(f"{self.base_url}/api/reset")
        return response.json()["session_id"]
        
    def test_question(self, question, expected_keywords=None, category=None):
        """Test a single question and record results"""
        start_time = datetime.now()
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={"message": question, "session_id": self.session_id}
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        data = response.json()
        answer = data.get("message", "")
        success = True
        
        # Verify expected keywords are in response
        missing_keywords = []
        if expected_keywords:
            for keyword in expected_keywords:
                if keyword.lower() not in answer.lower():
                    missing_keywords.append(keyword)
                    success = False
        
        result = {
            "question": question,
            "category": category,
            "response": answer,
            "response_time": duration,
            "success": success,
            "missing_keywords": missing_keywords,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    def run_test_suite(self, test_file):
        """Run a full test suite from a CSV file"""
        with open(test_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keywords = row.get("expected_keywords", "").split(";")
                self.test_question(
                    row["question"], 
                    expected_keywords=keywords,
                    category=row.get("category")
                )
                
    def export_results(self, output_file="test_results.json"):
        """Export results to a JSON file"""
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "success_rate": sum(1 for r in self.results if r["success"]) / len(self.results),
                "results": self.results
            }, f, indent=2)

# Example usage
if __name__ == "__main__":
    tester = ChatbotTester()
    
    # Individual tests
    tester.test_question("Tell me about the pyramids", ["Giza", "pharaoh", "tomb"])
    
    # Or run a full test suite
    # tester.run_test_suite("test_cases.csv")
    
    tester.export_results()