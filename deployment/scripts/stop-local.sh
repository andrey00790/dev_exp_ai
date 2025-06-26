#!/bin/bash

# =============================================================================
# AI Assistant - Stop Local Services
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.yaml"

echo -e "${BLUE}🛑 Stopping AI Assistant services...${NC}"

# Stop services
docker-compose -f $COMPOSE_FILE down

echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo "💾 Data is preserved in Docker volumes:"
echo "   • PostgreSQL data"
echo "   • Qdrant vector data"
echo "   • Ollama models"
echo "   • Application logs"
echo ""
echo "🚀 To start again: ./start-local.sh" 