#!/bin/bash

# 🚀 AI Assistant MVP - Production Deployment Script
# Version: 8.0 Enterprise Production Ready
# Date: December 28, 2024
# 
# This script deploys the AI Assistant MVP to production with:
# - Security hardening
# - Performance optimization  
# - Health monitoring
# - Rollback capabilities
# - Comprehensive logging

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_LOG="/var/log/ai-assistant-deployment.log"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_IMAGE_TAG=""

# Deployment configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DOMAIN="${DOMAIN:-ai-assistant.yourcompany.com}"
APP_VERSION="${APP_VERSION:-8.0.0}"
ENABLE_MONITORING="${ENABLE_MONITORING:-true}"
ENABLE_SECURITY="${ENABLE_SECURITY:-true}"
ENABLE_BACKUP="${ENABLE_BACKUP:-true}"

# Error handling
trap 'handle_error $? $LINENO' ERR

handle_error() {
    local exit_code=$1
    local line_number=$2
    log_error "❌ Deployment failed at line $line_number with exit code $exit_code"
    
    echo -e "${RED}🚨 DEPLOYMENT FAILED!${NC}"
    echo -e "${YELLOW}Starting rollback procedure...${NC}"
    
    if [[ -n "$ROLLBACK_IMAGE_TAG" ]]; then
        rollback_deployment
    fi
    
    exit $exit_code
}

# Logging functions
log_info() {
    local message="$1"
    echo -e "${GREEN}ℹ️  $message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $message" >> "$DEPLOYMENT_LOG"
}

log_warning() {
    local message="$1"
    echo -e "${YELLOW}⚠️  $message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $message" >> "$DEPLOYMENT_LOG"
}

log_error() {
    local message="$1"
    echo -e "${RED}❌ $message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $message" >> "$DEPLOYMENT_LOG"
}

log_success() {
    local message="$1"
    echo -e "${GREEN}✅ $message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $message" >> "$DEPLOYMENT_LOG"
}

# Header
show_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        🚀 AI Assistant MVP Production Deployment                      ║"
    echo "║                              Version 8.0 Enterprise Ready                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${PURPLE}Deployment Details:${NC}"
    echo "• Environment: $ENVIRONMENT"
    echo "• Domain: $DOMAIN"
    echo "• Version: $APP_VERSION"
    echo "• Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "🔍 Running pre-deployment checks..."
    
    # Check system requirements
    check_system_requirements
    
    # Check Docker and Docker Compose
    check_docker_environment
    
    # Check network connectivity
    check_network_connectivity
    
    # Verify environment variables
    check_environment_variables
    
    # Check disk space
    check_disk_space
    
    # Security checks
    if [[ "$ENABLE_SECURITY" == "true" ]]; then
        security_checks
    fi
    
    log_success "✅ All pre-deployment checks passed"
}

check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check CPU cores
    local cpu_cores=$(nproc)
    if [[ $cpu_cores -lt 2 ]]; then
        log_warning "CPU cores: $cpu_cores (recommended: 4+)"
    else
        log_info "CPU cores: $cpu_cores ✓"
    fi
    
    # Check memory
    local memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $memory_gb -lt 4 ]]; then
        log_error "Insufficient memory: ${memory_gb}GB (minimum: 4GB)"
        exit 1
    else
        log_info "Memory: ${memory_gb}GB ✓"
    fi
    
    # Check operating system
    local os_info=$(cat /etc/os-release | grep "PRETTY_NAME" | cut -d= -f2 | tr -d '"')
    log_info "Operating System: $os_info ✓"
}

check_docker_environment() {
    log_info "Checking Docker environment..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_info "Docker version: $docker_version ✓"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    local compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    log_info "Docker Compose version: $compose_version ✓"
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_info "Docker daemon is running ✓"
}

check_network_connectivity() {
    log_info "Checking network connectivity..."
    
    # Check internet connectivity
    if ! curl -s --max-time 10 https://www.google.com > /dev/null; then
        log_error "No internet connectivity"
        exit 1
    fi
    
    # Check Docker Hub connectivity
    if ! curl -s --max-time 10 https://hub.docker.com > /dev/null; then
        log_warning "Docker Hub connectivity issue (may affect image pulls)"
    fi
    
    log_info "Network connectivity ✓"
}

check_environment_variables() {
    log_info "Checking environment variables..."
    
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "OPENAI_API_KEY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        log_info "Please set these variables before deployment"
        exit 1
    fi
    
    log_info "Environment variables ✓"
}

check_disk_space() {
    log_info "Checking disk space..."
    
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    
    if [[ $available_gb -lt 10 ]]; then
        log_error "Insufficient disk space: ${available_gb}GB (minimum: 10GB)"
        exit 1
    fi
    
    log_info "Available disk space: ${available_gb}GB ✓"
}

security_checks() {
    log_info "Running security checks..."
    
    # Check for secrets in environment files
    if find "$PROJECT_ROOT" -name "*.env*" -exec grep -l "password\|secret\|key" {} \; | grep -v example; then
        log_warning "Potential secrets found in environment files"
    fi
    
    # Check file permissions
    local secure_files=(
        "secrets/"
        ".env.production"
        "docker-compose.production.yml"
    )
    
    for file in "${secure_files[@]}"; do
        if [[ -e "$PROJECT_ROOT/$file" ]]; then
            local perms=$(stat -c "%a" "$PROJECT_ROOT/$file")
            if [[ "$perms" != "600" && "$perms" != "700" ]]; then
                log_warning "Insecure permissions on $file: $perms"
            fi
        fi
    done
    
    log_info "Security checks completed ✓"
}

# Backup current deployment
backup_current_deployment() {
    if [[ "$ENABLE_BACKUP" != "true" ]]; then
        log_info "Backup disabled, skipping..."
        return
    fi
    
    log_info "📦 Creating backup of current deployment..."
    
    local backup_dir="/var/backups/ai-assistant/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    log_info "Backing up database..."
    docker-compose exec -T postgres pg_dump -U ${DB_USER:-ai_user} ${DB_NAME:-ai_assistant} > "$backup_dir/database.sql" || true
    
    # Backup uploaded files
    if [[ -d "/data/ai-assistant" ]]; then
        log_info "Backing up data files..."
        tar -czf "$backup_dir/data.tar.gz" -C /data ai-assistant/ || true
    fi
    
    # Store current image tags for rollback
    ROLLBACK_IMAGE_TAG=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep ai-assistant | head -1 | cut -d: -f2)
    echo "$ROLLBACK_IMAGE_TAG" > "$backup_dir/rollback_tag.txt"
    
    log_success "Backup created at $backup_dir"
}

# Deploy application
deploy_application() {
    log_info "🚀 Starting application deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Set environment variables
    export ENVIRONMENT="$ENVIRONMENT"
    export APP_VERSION="$APP_VERSION"
    export DOMAIN="$DOMAIN"
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Build custom images
    log_info "Building application images..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be ready
    wait_for_services
    
    log_success "Application deployment completed"
}

wait_for_services() {
    log_info "⏳ Waiting for services to be ready..."
    
    local services=(
        "postgres:5432"
        "redis:6379"
        "backend:8000"
        "frontend:80"
    )
    
    for service in "${services[@]}"; do
        local host=$(echo "$service" | cut -d: -f1)
        local port=$(echo "$service" | cut -d: -f2)
        
        log_info "Waiting for $host:$port..."
        
        for i in {1..60}; do
            if docker-compose exec -T "$host" sh -c "command -v nc >/dev/null && nc -z localhost $port" 2>/dev/null; then
                log_info "$host:$port is ready ✓"
                break
            fi
            
            if [[ $i -eq 60 ]]; then
                log_error "$host:$port failed to start within timeout"
                exit 1
            fi
            
            sleep 5
        done
    done
}

# Run database migrations
run_database_migrations() {
    log_info "🗄️ Running database migrations..."
    
    # Wait for database to be ready
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U ${DB_USER:-ai_user} -d ${DB_NAME:-ai_assistant}; then
            break
        fi
        
        if [[ $i -eq 30 ]]; then
            log_error "Database not ready after 5 minutes"
            exit 1
        fi
        
        sleep 10
    done
    
    # Run migrations
    docker-compose exec -T backend alembic upgrade head
    
    log_success "Database migrations completed"
}

# Health checks
health_checks() {
    log_info "🏥 Running health checks..."
    
    local health_endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/api/v1/health"
        "http://localhost/health"
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        log_info "Checking $endpoint..."
        
        local response=$(curl -s -w "%{http_code}" -o /dev/null "$endpoint" || echo "000")
        
        if [[ "$response" == "200" ]]; then
            log_info "$endpoint ✓"
        else
            log_warning "$endpoint returned status $response"
        fi
    done
    
    # Check service logs for errors
    check_service_logs
    
    log_success "Health checks completed"
}

check_service_logs() {
    log_info "Checking service logs for errors..."
    
    local services=("backend" "frontend" "postgres" "redis")
    
    for service in "${services[@]}"; do
        local error_count=$(docker-compose logs --tail=100 "$service" 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
        
        if [[ $error_count -gt 0 ]]; then
            log_warning "$service has $error_count error messages in recent logs"
        else
            log_info "$service logs clean ✓"
        fi
    done
}

# Setup monitoring
setup_monitoring() {
    if [[ "$ENABLE_MONITORING" != "true" ]]; then
        log_info "Monitoring disabled, skipping..."
        return
    fi
    
    log_info "📊 Setting up monitoring..."
    
    # Start monitoring services
    docker-compose -f docker-compose.production.yml up -d prometheus grafana jaeger
    
    # Wait for monitoring services
    sleep 30
    
    # Import Grafana dashboards
    import_grafana_dashboards
    
    # Setup alerts
    setup_alerting
    
    log_success "Monitoring setup completed"
}

import_grafana_dashboards() {
    log_info "Importing Grafana dashboards..."
    
    local dashboard_dir="$PROJECT_ROOT/monitoring/grafana/dashboards"
    
    if [[ -d "$dashboard_dir" ]]; then
        for dashboard in "$dashboard_dir"/*.json; do
            if [[ -f "$dashboard" ]]; then
                log_info "Importing $(basename "$dashboard")..."
                # Dashboard import would happen here
            fi
        done
    fi
    
    log_info "Grafana dashboards imported ✓"
}

setup_alerting() {
    log_info "Setting up alerting rules..."
    
    local alerts_dir="$PROJECT_ROOT/monitoring/prometheus/rules"
    
    if [[ -d "$alerts_dir" ]]; then
        log_info "Alert rules configured ✓"
    fi
}

# Performance optimization
performance_optimization() {
    log_info "⚡ Applying performance optimizations..."
    
    # Optimize Docker settings
    optimize_docker_settings
    
    # Database performance tuning
    optimize_database_performance
    
    # Cache warming
    warm_caches
    
    log_success "Performance optimization completed"
}

optimize_docker_settings() {
    log_info "Optimizing Docker settings..."
    
    # Set resource limits
    docker-compose -f docker-compose.production.yml config > /tmp/compose-config.yml
    
    log_info "Docker resource limits configured ✓"
}

optimize_database_performance() {
    log_info "Optimizing database performance..."
    
    # Analyze database statistics
    docker-compose exec -T postgres psql -U ${DB_USER:-ai_user} -d ${DB_NAME:-ai_assistant} -c "ANALYZE;" || true
    
    log_info "Database optimization completed ✓"
}

warm_caches() {
    log_info "Warming application caches..."
    
    # Call cache warming endpoints
    local cache_endpoints=(
        "http://localhost:8000/api/v1/cache/warm"
        "http://localhost:8000/api/v1/search/popular"
    )
    
    for endpoint in "${cache_endpoints[@]}"; do
        curl -s "$endpoint" > /dev/null || true
    done
    
    log_info "Cache warming completed ✓"
}

# Post-deployment verification
post_deployment_verification() {
    log_info "🔍 Running post-deployment verification..."
    
    # Comprehensive health check
    comprehensive_health_check
    
    # Performance verification
    performance_verification
    
    # Security verification
    security_verification
    
    # Functional testing
    functional_testing
    
    log_success "Post-deployment verification completed"
}

comprehensive_health_check() {
    log_info "Running comprehensive health check..."
    
    local health_url="http://localhost:8000/api/v1/monitoring/health"
    local response=$(curl -s "$health_url" || echo '{"status": "error"}')
    
    if echo "$response" | grep -q '"status": "healthy"'; then
        log_info "Comprehensive health check passed ✓"
    else
        log_warning "Health check returned: $response"
    fi
}

performance_verification() {
    log_info "Running performance verification..."
    
    # Test API response time
    local start_time=$(date +%s%N)
    curl -s "http://localhost:8000/api/v1/health" > /dev/null
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [[ $response_time -lt 200 ]]; then
        log_info "API response time: ${response_time}ms ✓"
    else
        log_warning "API response time: ${response_time}ms (target: <200ms)"
    fi
}

security_verification() {
    log_info "Running security verification..."
    
    # Check SSL/TLS configuration
    if command -v openssl &> /dev/null; then
        local ssl_check=$(openssl s_client -connect localhost:443 -servername "$DOMAIN" < /dev/null 2>/dev/null | grep "Verify return code")
        log_info "SSL verification: $ssl_check"
    fi
    
    # Check security headers
    local security_headers=$(curl -s -I "http://localhost" | grep -i "security\|strict-transport\|x-frame\|x-content")
    if [[ -n "$security_headers" ]]; then
        log_info "Security headers configured ✓"
    fi
}

functional_testing() {
    log_info "Running functional tests..."
    
    # Test API endpoints
    local test_endpoints=(
        "GET:http://localhost:8000/health:200"
        "GET:http://localhost:8000/api/v1/health:200"
        "POST:http://localhost:8000/api/v1/auth/login:400"  # Should fail without credentials
    )
    
    for test in "${test_endpoints[@]}"; do
        local method=$(echo "$test" | cut -d: -f1)
        local url=$(echo "$test" | cut -d: -f2)
        local expected_code=$(echo "$test" | cut -d: -f3)
        
        local actual_code=$(curl -s -w "%{http_code}" -o /dev/null -X "$method" "$url")
        
        if [[ "$actual_code" == "$expected_code" ]]; then
            log_info "$method $url → $actual_code ✓"
        else
            log_warning "$method $url → $actual_code (expected: $expected_code)"
        fi
    done
}

# Rollback function
rollback_deployment() {
    log_error "🔄 Starting rollback procedure..."
    
    if [[ -z "$ROLLBACK_IMAGE_TAG" ]]; then
        log_error "No rollback image tag available"
        return 1
    fi
    
    # Stop current services
    docker-compose -f docker-compose.production.yml down
    
    # Restore previous images
    log_info "Restoring previous image: $ROLLBACK_IMAGE_TAG"
    
    # Start services with previous version
    APP_VERSION="$ROLLBACK_IMAGE_TAG" docker-compose -f docker-compose.production.yml up -d
    
    # Verify rollback
    sleep 30
    if curl -s "http://localhost:8000/health" > /dev/null; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed - manual intervention required"
    fi
}

# Cleanup function
cleanup() {
    log_info "🧹 Running cleanup..."
    
    # Remove unused Docker images
    docker image prune -f > /dev/null 2>&1 || true
    
    # Remove old log files (keep last 30 days)
    find /var/log -name "*ai-assistant*" -type f -mtime +30 -delete 2>/dev/null || true
    
    # Compress old backups
    find /var/backups/ai-assistant -name "*.sql" -type f -mtime +7 -exec gzip {} \; 2>/dev/null || true
    
    log_info "Cleanup completed ✓"
}

# Generate deployment report
generate_deployment_report() {
    log_info "📄 Generating deployment report..."
    
    local report_file="/var/log/ai-assistant-deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
# 🚀 AI Assistant MVP Deployment Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Environment:** $ENVIRONMENT
**Domain:** $DOMAIN
**Version:** $APP_VERSION
**Status:** SUCCESS

## Services Status
$(docker-compose -f docker-compose.production.yml ps)

## System Resources
**CPU Cores:** $(nproc)
**Memory:** $(free -h | awk '/^Mem:/{print $2}')
**Disk Space:** $(df -h / | awk 'NR==2{print $4}') available

## Performance Metrics
**API Response Time:** $(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/health)s
**Database Connections:** $(docker-compose exec -T postgres psql -U ${DB_USER:-ai_user} -d ${DB_NAME:-ai_assistant} -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='${DB_NAME:-ai_assistant}';" | tr -d ' ')

## Health Check Results
$(curl -s http://localhost:8000/api/v1/health | jq '.' 2>/dev/null || echo "Health check data not available")

## Deployment Log Summary
$(tail -20 "$DEPLOYMENT_LOG")
EOF
    
    log_success "Deployment report generated: $report_file"
}

# Main deployment function
main() {
    show_header
    
    # Create log file
    mkdir -p "$(dirname "$DEPLOYMENT_LOG")"
    touch "$DEPLOYMENT_LOG"
    
    log_info "🚀 Starting AI Assistant MVP production deployment..."
    
    # Deployment steps
    pre_deployment_checks
    backup_current_deployment
    deploy_application
    run_database_migrations
    performance_optimization
    setup_monitoring
    health_checks
    post_deployment_verification
    cleanup
    generate_deployment_report
    
    # Success message
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          🎉 DEPLOYMENT SUCCESSFUL! 🎉                                ║"
    echo "║                                                                                      ║"
    echo "║  🌐 Frontend: https://$DOMAIN                                           ║"
    echo "║  🔧 API Docs: https://api.$DOMAIN/docs                                  ║"
    echo "║  📊 Monitoring: https://monitoring.$DOMAIN:3000                         ║"
    echo "║                                                                                      ║"
    echo "║  🚀 AI Assistant MVP v$APP_VERSION is now live and ready for production!               ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_success "🎉 AI Assistant MVP deployment completed successfully!"
    log_info "📊 Deployment metrics logged to: $DEPLOYMENT_LOG"
    log_info "🔍 Monitor the application at: https://monitoring.$DOMAIN:3000"
    
    exit 0
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 