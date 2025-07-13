#!/bin/bash

# AI Assistant API Testing Script
# Version: 1.0.0
# Usage: ./test_api.sh [base_url]

set -e

# Configuration
API_BASE="${1:-http://localhost:8000}"
API_V1="$API_BASE/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"
    local expect_status="${5:-200}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "  Testing $name... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "%{http_code}" -X POST "$url" \
                   -H "Content-Type: application/json" \
                   -d "$data" 2>/dev/null)
    else
        response=$(curl -s -w "%{http_code}" "$url" 2>/dev/null)
    fi
    
    # Extract HTTP status code (last 3 characters)
    status_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$status_code" = "$expect_status" ]; then
        echo -e "${GREEN}✅ OK${NC} (${status_code})"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        
        # Try to format JSON response
        if command -v jq >/dev/null 2>&1; then
            echo "    $(echo "$response_body" | jq -c '.' 2>/dev/null | head -c 80)..."
        else
            echo "    $(echo "$response_body" | head -c 80)..."
        fi
    else
        echo -e "${RED}❌ FAILED${NC} (Expected: $expect_status, Got: $status_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "    Response: $(echo "$response_body" | head -c 100)..."
    fi
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${RED}❌ curl is not installed${NC}"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  jq is not installed (optional, for pretty JSON)${NC}"
        echo "   Install with: brew install jq (macOS) or apt install jq (Ubuntu)"
    fi
    
    echo -e "${GREEN}✅ Dependencies OK${NC}"
}

test_server_connectivity() {
    print_section "Server Connectivity"
    
    echo -n "  Checking server connectivity... "
    if curl -s --connect-timeout 5 "$API_BASE" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is reachable${NC}"
    else
        echo -e "${RED}❌ Server is not reachable${NC}"
        echo -e "${RED}Make sure the server is running on $API_BASE${NC}"
        exit 1
    fi
}

# Main testing functions
test_health_endpoints() {
    print_section "Health Endpoints"
    
    test_endpoint "Basic Health" "$API_BASE/health"
    test_endpoint "API Health" "$API_BASE/api/health"
    test_endpoint "API v1 Health" "$API_V1/health"
}

test_auth_endpoints() {
    print_section "Authentication Endpoints"
    
    test_endpoint "SSO Providers" "$API_V1/auth/sso/providers"
    test_endpoint "Auth Verify" "$API_V1/auth/verify"
}

test_mock_endpoints() {
    print_section "Mock Endpoints (No Auth Required)"
    
    test_endpoint "Generate Mock" "$API_V1/generate" "POST" '{"query": "Hello AI"}'
    test_endpoint "Optimize Mock" "$API_V1/optimize" "POST" '{"target": "performance"}'
}

test_data_endpoints() {
    print_section "Data Endpoints"
    
    test_endpoint "Users List" "$API_V1/users"
    test_endpoint "Data Sources" "$API_V1/data-sources"
}

test_documentation() {
    print_section "API Documentation"
    
    test_endpoint "OpenAPI Spec" "$API_BASE/openapi.json"
    test_endpoint "Swagger UI" "$API_BASE/docs"
    test_endpoint "ReDoc" "$API_BASE/redoc"
}

test_infrastructure() {
    print_section "Infrastructure Services"
    
    # Test database connection through health endpoint
    echo -n "  Testing database connectivity... "
    health_response=$(curl -s "$API_BASE/health" 2>/dev/null || echo "")
    if echo "$health_response" | grep -q "healthy"; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
    
    # Test vector database (Qdrant)
    echo -n "  Testing Qdrant (port 6333)... "
    if curl -s --connect-timeout 2 "http://localhost:6333" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${YELLOW}⚠️  Not accessible${NC}"
    fi
    
    # Test Redis Commander
    echo -n "  Testing Redis Commander (port 8081)... "
    if curl -s --connect-timeout 2 "http://localhost:8081" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${YELLOW}⚠️  Not accessible${NC}"
    fi
    
    # Test Ollama
    echo -n "  Testing Ollama (port 11434)... "
    if curl -s --connect-timeout 2 "http://localhost:11434/api/version" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${YELLOW}⚠️  Not accessible${NC}"
    fi
}

show_summary() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}         TEST SUMMARY${NC}"
    echo -e "${BLUE}================================${NC}"
    echo -e "Total tests: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    else
        echo -e "Failed: $TESTS_FAILED"
    fi
    
    success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    echo -e "Success rate: $success_rate%"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All tests passed! API is working correctly.${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
    fi
    
    echo -e "\n${BLUE}Quick Links:${NC}"
    echo -e "  • API Docs: $API_BASE/docs"
    echo -e "  • Health: $API_BASE/health"
    echo -e "  • OpenAPI: $API_BASE/openapi.json"
}

# Main execution
main() {
    print_header "🧪 AI Assistant API Testing Tool"
    
    # Parse arguments correctly
    local base_url="http://localhost:8000"
    local performance_test=false
    
    # Check for --performance flag
    for arg in "$@"; do
        if [ "$arg" = "--performance" ]; then
            performance_test=true
        elif [[ "$arg" =~ ^https?:// ]]; then
            base_url="$arg"
        fi
    done
    
    echo "Testing API at: $base_url"
    echo "Timestamp: $(date)"
    echo ""
    
    # Update global variables
    API_BASE="$base_url"
    API_V1="$base_url/api/v1"
    
    check_dependencies
    test_server_connectivity
    test_health_endpoints
    test_auth_endpoints  
    test_mock_endpoints
    test_data_endpoints
    test_documentation
    test_infrastructure
    
    if [ "$performance_test" = true ]; then
        performance_test_func
    fi
    
    show_summary
}

# Performance test function (renamed)
performance_test_func() {
    print_section "Performance Test"
    
    echo -n "  Testing health endpoint response time... "
    
    # Run 10 requests and measure average time
    total_time=0
    count=10
    
    for i in $(seq 1 $count); do
        time_taken=$(curl -s -w "%{time_total}" -o /dev/null "$API_BASE/health" 2>/dev/null)
        total_time=$(echo "$total_time + $time_taken" | bc -l 2>/dev/null || echo "0")
    done
    
    if command -v bc >/dev/null 2>&1; then
        avg_time=$(echo "scale=3; $total_time / $count" | bc -l)
        echo -e "${GREEN}✅ Average: ${avg_time}s${NC}"
        
        if (( $(echo "$avg_time < 0.1" | bc -l) )); then
            echo -e "    ${GREEN}Excellent performance! (<100ms)${NC}"
        elif (( $(echo "$avg_time < 0.2" | bc -l) )); then
            echo -e "    ${YELLOW}Good performance (100-200ms)${NC}"
        else
            echo -e "    ${RED}Slow performance (>200ms)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  bc not available for calculations${NC}"
    fi
}

# Help function
show_help() {
    echo "AI Assistant API Testing Script"
    echo ""
    echo "Usage:"
    echo "  $0 [base_url] [--performance]"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Test localhost:8000"
    echo "  $0 http://localhost:8000              # Test specific URL"
    echo "  $0 http://localhost:8000 --performance # Include performance tests"
    echo ""
    echo "Options:"
    echo "  --performance    Run additional performance tests"
    echo "  --help           Show this help message"
}

# Check for help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Run main function
main "$1" "$2" 