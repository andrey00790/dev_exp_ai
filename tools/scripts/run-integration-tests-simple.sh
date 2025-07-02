#!/bin/bash

set -e

echo "🚀 Running Integration Tests with Existing Services"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Step 1: Setting up test environment variables...${NC}"

# Use existing services (already running in dev environment)
export TEST_DATABASE_URL="postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant"
export TEST_REDIS_URL="redis://localhost:6379/1"
export TEST_QDRANT_URL="http://localhost:6333"
export TESTING=true
export ENVIRONMENT=test

# PostgreSQL variables for compatibility
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=ai_assistant
export POSTGRES_USER=ai_user
export POSTGRES_PASSWORD=ai_password_dev

# Redis variables
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Qdrant variables
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

echo -e "${BLUE}📋 Step 2: Checking service availability...${NC}"

# Check PostgreSQL
if nc -z localhost 5432; then
    echo -e "${GREEN}✅ PostgreSQL available on port 5432${NC}"
else
    echo -e "${RED}❌ PostgreSQL not available on port 5432${NC}"
    exit 1
fi

# Check Redis
if nc -z localhost 6379; then
    echo -e "${GREEN}✅ Redis available on port 6379${NC}"
else
    echo -e "${RED}❌ Redis not available on port 6379${NC}"
    exit 1
fi

# Check Qdrant
if nc -z localhost 6333; then
    echo -e "${GREEN}✅ Qdrant available on port 6333${NC}"
else
    echo -e "${RED}❌ Qdrant not available on port 6333${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Step 3: Running integration tests...${NC}"

# Run integration tests with proper environment
python -m pytest tests/integration/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    -v \
    --tb=short \
    --color=yes \
    --durations=10

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}🎉 All integration tests passed!${NC}"
    echo -e "${GREEN}📊 Coverage report available in htmlcov/index.html${NC}"
else
    echo -e "${RED}❌ Some integration tests failed${NC}"
fi

exit $exit_code
