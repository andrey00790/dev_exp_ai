#!/bin/bash

# =============================================================================
# AI Assistant - Simple Local Deployment
# One command to deploy everything locally with persistent data
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.yaml"

echo -e "${BLUE}🚀 Starting AI Assistant locally...${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f $COMPOSE_FILE down >/dev/null 2>&1 || true

# Clean up old containers
docker container prune -f >/dev/null 2>&1 || true

# Build and start services
echo -e "${BLUE}🔨 Building and starting services...${NC}"
ENVIRONMENT=development docker-compose -f $COMPOSE_FILE up -d --build

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL..."
for i in {1..60}; do
    if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    sleep 2
    echo -n "."
    if [ $i -eq 60 ]; then
        echo -e " ${YELLOW}⚠️ PostgreSQL not ready, continuing...${NC}"
    fi
done

# Wait for Qdrant
echo -n "Waiting for Qdrant..."
for i in {1..60}; do
    if curl -sf http://localhost:6333/readyz >/dev/null 2>&1; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    sleep 2
    echo -n "."
    if [ $i -eq 60 ]; then
        echo -e " ${YELLOW}⚠️ Qdrant not ready, continuing...${NC}"
    fi
done

# Wait for Backend
echo -n "Waiting for Backend..."
for i in {1..120}; do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    sleep 3
    echo -n "."
    if [ $i -eq 120 ]; then
        echo -e " ${RED}❌ Backend failed to start${NC}"
        echo "Check logs with: docker-compose -f $COMPOSE_FILE logs app"
        exit 1
    fi
done

# Initialize Qdrant collections
echo -e "${BLUE}🔧 Initializing vector collections...${NC}"
sleep 5
docker-compose -f $COMPOSE_FILE exec -T app python3 -c "
import asyncio
import sys
sys.path.append('/app')
from adapters.vectorstore.collections import initialize_collections
try:
    asyncio.run(initialize_collections())
    print('✅ Collections initialized successfully!')
except Exception as e:
    print(f'⚠️  Collections initialization: {e}')
" || echo -e "${YELLOW}⚠️  Collections initialization skipped${NC}"

# Wait for Frontend
echo -n "Waiting for Frontend..."
for i in {1..60}; do
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    sleep 3
    echo -n "."
    if [ $i -eq 60 ]; then
        echo -e " ${YELLOW}⚠️ Frontend not ready, continuing...${NC}"
    fi
done

# Show status
echo ""
echo "================================================================================"
echo -e "${GREEN}🎉 AI Assistant deployed successfully!${NC}"
echo "================================================================================"
echo ""
echo "📋 Service URLs:"
echo -e "   • Frontend:           ${BLUE}http://localhost:3000${NC}"
echo -e "   • Backend API:        ${BLUE}http://localhost:8000${NC}"
echo -e "   • API Documentation:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   • Health Check:       ${BLUE}http://localhost:8000/health${NC}"
echo -e "   • Qdrant Dashboard:   ${BLUE}http://localhost:6333/dashboard${NC}"
echo -e "   • PostgreSQL:         ${BLUE}localhost:5432${NC}"
echo -e "   • Ollama:             ${BLUE}http://localhost:11434${NC}"
echo ""
echo "🔧 Management Commands:"
echo -e "   • View logs:          ${YELLOW}docker-compose logs -f${NC}"
echo -e "   • Stop services:      ${YELLOW}docker-compose down${NC}"
echo -e "   • Restart:            ${YELLOW}./start-local.sh${NC}"
echo ""
echo "💾 Data Persistence:"
echo "   All data (PostgreSQL, Qdrant, Ollama, logs) will persist between restarts"
echo ""

# Test basic functionality
echo -e "${BLUE}🧪 Testing basic functionality...${NC}"

# Test health
if curl -sf http://localhost:8000/health | grep -q "healthy"; then
    echo -e "   ✅ Health check: ${GREEN}PASSED${NC}"
else
    echo -e "   ❌ Health check: ${RED}FAILED${NC}"
fi

# Test vector collections
if curl -sf http://localhost:8000/api/v1/vector-search/collections >/dev/null 2>&1; then
    echo -e "   ✅ Vector search: ${GREEN}ACCESSIBLE${NC}"
else
    echo -e "   ⚠️  Vector search: ${YELLOW}NOT READY${NC}"
fi

# Test LLM providers
if curl -sf http://localhost:8000/api/v1/llm/providers >/dev/null 2>&1; then
    echo -e "   ✅ LLM providers: ${GREEN}ACCESSIBLE${NC}"
else
    echo -e "   ⚠️  LLM providers: ${YELLOW}NOT READY${NC}"
fi

echo ""
echo "================================================================================"
echo -e "${GREEN}🚀 Ready to use! Open http://localhost:3000 in your browser${NC}"
echo "================================================================================" 