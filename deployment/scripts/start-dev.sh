#!/bin/bash
echo "🚀 Starting AI Assistant Development Environment..."
docker-compose down --remove-orphans
docker-compose build
docker-compose up -d
echo "✅ Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
