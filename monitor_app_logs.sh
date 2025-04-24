#!/bin/bash
set -e

echo "Restarting application container..."
docker restart egypt-chatbot-wind-cursor-app-1

echo "Waiting for application to start..."
sleep 5

echo "Checking logs for RAG related messages..."
docker logs egypt-chatbot-wind-cursor-app-1 --tail 100 | grep -i "rag\|knowledge\|database\|query"

echo "Application restarted! Wait a moment before testing."
