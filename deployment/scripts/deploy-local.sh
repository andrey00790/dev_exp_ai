#!/bin/bash

# =============================================================================
# AI Assistant - Local Deployment Script
# Deploy everything in one command with persistent data
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "All requirements met!"
}

# Create necessary directories for persistent data
create_directories() {
    print_status "Creating data directories..."
    
    mkdir -p data/{redis,qdrant,app,prometheus,grafana}
    mkdir -p logs
    
    # Set proper permissions
    chmod 755 data logs
    chmod -R 755 data/*
    
    print_success "Data directories created!"
}

# Clean up any existing containers
cleanup_existing() {
    print_status "Cleaning up existing containers..."
    
    # Stop and remove existing containers
    docker-compose -f docker-compose.prod.yml down --remove-orphans >/dev/null 2>&1 || true
    
    print_success "Cleanup completed!"
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Build images
    print_status "Building application images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start core services first
    print_status "Starting core services (Redis, Qdrant)..."
    docker-compose -f docker-compose.prod.yml up -d redis qdrant
    
    # Wait for core services to be healthy
    print_status "Waiting for core services to be ready..."
    sleep 30
    
    # Start application
    print_status "Starting AI Assistant application..."
    docker-compose -f docker-compose.prod.yml up -d app
    
    # Wait for app to be ready
    print_status "Waiting for application to be ready..."
    sleep 45
    
    # Initialize data
    print_status "Initializing vector collections..."
    docker-compose -f docker-compose.prod.yml up data-init
    
    # Start frontend
    print_status "Starting frontend..."
    docker-compose -f docker-compose.prod.yml up -d frontend
    
    print_success "All services started!"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for all services to be healthy..."
    
    # Wait for app health check
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Backend is healthy!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Backend failed to become healthy after $max_attempts attempts"
            print_error "Check logs with: docker-compose -f docker-compose.prod.yml logs app"
            exit 1
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting for backend..."
        sleep 5
        ((attempt++))
    done
    
    # Wait for frontend
    attempt=1
    while [ $attempt -le 30 ]; do
        if curl -sf http://localhost:3000 >/dev/null 2>&1; then
            print_success "Frontend is healthy!"
            break
        fi
        
        if [ $attempt -eq 30 ]; then
            print_warning "Frontend not responding, but continuing..."
            break
        fi
        
        print_status "Attempt $attempt/30 - waiting for frontend..."
        sleep 3
        ((attempt++))
    done
}

# Display deployment information
show_deployment_info() {
    echo ""
    echo "================================================================================"
    echo -e "${GREEN}🚀 AI Assistant Deployed Successfully!${NC}"
    echo "================================================================================"
    echo ""
    echo "📋 Service URLs:"
    echo -e "   • Frontend:           ${BLUE}http://localhost:3000${NC}"
    echo -e "   • Backend API:        ${BLUE}http://localhost:8000${NC}"
    echo -e "   • API Documentation:  ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "   • Health Check:       ${BLUE}http://localhost:8000/health${NC}"
    echo -e "   • Qdrant Dashboard:   ${BLUE}http://localhost:6333/dashboard${NC}"
    echo ""
    echo "🗂️  Data Persistence:"
    echo -e "   • Redis data:         ${YELLOW}./data/redis${NC}"
    echo -e "   • Qdrant data:        ${YELLOW}./data/qdrant${NC}"
    echo -e "   • Application data:   ${YELLOW}./data/app${NC}"
    echo -e "   • Logs:               ${YELLOW}./logs${NC}"
    echo ""
    echo "🔧 Management Commands:"
    echo -e "   • View logs:          ${YELLOW}docker-compose -f docker-compose.prod.yml logs -f${NC}"
    echo -e "   • Stop services:      ${YELLOW}docker-compose -f docker-compose.prod.yml down${NC}"
    echo -e "   • Restart services:   ${YELLOW}docker-compose -f docker-compose.prod.yml restart${NC}"
    echo -e "   • Update and restart: ${YELLOW}./deploy-local.sh${NC}"
    echo ""
    echo "📊 Optional Monitoring (add --profile monitoring):"
    echo -e "   • Prometheus:         ${BLUE}http://localhost:9090${NC}"
    echo -e "   • Grafana:            ${BLUE}http://localhost:3001${NC} (admin/admin)"
    echo ""
    echo "================================================================================"
}

# Test the deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Test health endpoint
    if curl -sf http://localhost:8000/health >/dev/null; then
        print_success "✅ Health check passed"
    else
        print_error "❌ Health check failed"
        return 1
    fi
    
    # Test collections endpoint
    if curl -sf http://localhost:8000/api/v1/vector-search/collections >/dev/null; then
        print_success "✅ Vector search API accessible"
    else
        print_warning "⚠️  Vector search API not responding"
    fi
    
    # Test LLM providers endpoint
    if curl -sf http://localhost:8000/api/v1/llm/providers >/dev/null; then
        print_success "✅ LLM providers API accessible"
    else
        print_warning "⚠️  LLM providers API not responding"
    fi
    
    print_success "Deployment test completed!"
}

# Main deployment function
main() {
    echo "================================================================================"
    echo -e "${BLUE}🚀 AI Assistant - Local Deployment${NC}"
    echo "================================================================================"
    echo ""
    
    check_requirements
    create_directories
    cleanup_existing
    deploy_services
    wait_for_services
    test_deployment
    show_deployment_info
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    "--monitoring")
        export COMPOSE_PROFILES=monitoring
        print_status "Enabling monitoring stack..."
        ;;
    "--help"|"-h")
        echo "Usage: $0 [--monitoring] [--help]"
        echo ""
        echo "Options:"
        echo "  --monitoring    Enable Prometheus and Grafana monitoring"
        echo "  --help, -h      Show this help message"
        exit 0
        ;;
esac

# Run main function
main "$@" 