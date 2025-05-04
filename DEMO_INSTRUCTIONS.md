# Egypt Tourism Chatbot - Demo Instructions

This document provides instructions for running and demonstrating the Egypt Tourism Chatbot.

## Quick Start

### Running with Docker (Recommended)

1. Make sure Docker and Docker Compose are installed on your system.

2. Start the chatbot and its dependencies:
   ```bash
   docker-compose up
   ```

3. The chatbot API will be available at http://localhost:5050/api

4. Access the web interface at http://localhost:5050

### Testing the Chatbot

1. Run the test queries script to verify the chatbot can answer tourism questions:
   ```bash
   python test_queries.py
   ```

2. This will send a series of tourism-related questions to the chatbot and display the responses.

## Demo Queries

Here are some example queries you can use to demonstrate the chatbot's capabilities:

### General Information
- "Tell me about Egypt"
- "What's the best time to visit Egypt?"
- "Do I need a visa to visit Egypt?"

### Attractions
- "What are the must-see attractions in Egypt?"
- "Tell me about the Pyramids of Giza"
- "What can I see in Luxor?"
- "Is Alexandria worth visiting?"

### Practical Information
- "What currency is used in Egypt?"
- "Is Egypt safe for tourists?"
- "What should I wear when visiting Egypt?"
- "How do I get around in Egypt?"

### Culture and History
- "Tell me about ancient Egyptian history"
- "What kind of food can I try in Egypt?"
- "What is koshari?"
- "What are some Egyptian cultural customs I should know about?"

### Activities
- "What activities can I do in Egypt?"
- "Can I go diving in the Red Sea?"
- "Tell me about Nile cruises"
- "What's special about the White Desert?"

## Troubleshooting

### Docker Issues

If you encounter issues with Docker:

1. Stop any running containers:
   ```bash
   docker-compose down
   ```

2. Remove any existing containers and volumes:
   ```bash
   docker-compose down -v
   ```

3. Rebuild and start the containers:
   ```bash
   docker-compose up --build
   ```

### API Connection Issues

If the test script cannot connect to the API:

1. Verify the API is running by visiting http://localhost:5050/api/health in your browser
2. Check that the port 5050 is not being used by another application
3. Ensure your firewall is not blocking the connection

## Notes for the Demo

- The chatbot has been enhanced with comprehensive tourism knowledge about Egypt
- It can answer questions about attractions, history, culture, practical travel information, and more
- The responses are generated based on a knowledge base, not by calling external APIs
- The chatbot maintains context within a conversation session
