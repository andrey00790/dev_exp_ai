#!/bin/bash

# AI Assistant MVP - Production Deployment Script
# Automated infrastructure and application deployment

set -euo pipefail

# Configuration
PROJECT_NAME="ai-assistant-mvp"
AWS_REGION="${AWS_REGION:-us-west-2}"
ENVIRONMENT="${ENVIRONMENT:-production}"
VERSION="${VERSION:-$(date +%Y%m%d-%H%M%S)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check dependencies
check_dependencies() {
    log_info "Checking deployment dependencies..."
    
    local deps=("aws" "terraform" "docker" "jq" "curl")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error_exit "$dep is not installed or not in PATH"
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error_exit "AWS credentials not configured or invalid"
    fi
    
    log_success "All dependencies are available"
}

# Validate environment variables
validate_env() {
    log_info "Validating environment variables..."
    
    local required_vars=(
        "AWS_REGION"
        "ENVIRONMENT"
        "DB_PASSWORD"
        "REDIS_AUTH_TOKEN"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    log_success "Environment variables validated"
}

# Build and push Docker images
build_and_push() {
    log_info "Building and pushing Docker images..."
    
    # Get ECR login
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Build backend image
    log_info "Building backend image..."
    docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VERSION="$VERSION" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        -t "$PROJECT_NAME-backend:$VERSION" \
        -f Dockerfile.prod .
    
    # Tag and push backend
    local ecr_backend="$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-backend"
    docker tag "$PROJECT_NAME-backend:$VERSION" "$ecr_backend:$VERSION"
    docker tag "$PROJECT_NAME-backend:$VERSION" "$ecr_backend:latest"
    docker push "$ecr_backend:$VERSION"
    docker push "$ecr_backend:latest"
    
    # Build frontend image
    log_info "Building frontend image..."
    cd frontend
    docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VERSION="$VERSION" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        --build-arg REACT_APP_API_URL="${REACT_APP_API_URL:-}" \
        --build-arg REACT_APP_WS_URL="${REACT_APP_WS_URL:-}" \
        -t "$PROJECT_NAME-frontend:$VERSION" \
        -f Dockerfile.prod .
    cd ..
    
    # Tag and push frontend
    local ecr_frontend="$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-frontend"
    docker tag "$PROJECT_NAME-frontend:$VERSION" "$ecr_frontend:$VERSION"
    docker tag "$PROJECT_NAME-frontend:$VERSION" "$ecr_frontend:latest"
    docker push "$ecr_frontend:$VERSION"
    docker push "$ecr_frontend:latest"
    
    log_success "Docker images built and pushed successfully"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init \
        -backend-config="bucket=${TERRAFORM_STATE_BUCKET}" \
        -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
        -backend-config="region=${AWS_REGION}"
    
    # Plan deployment
    terraform plan \
        -var="environment=${ENVIRONMENT}" \
        -var="aws_region=${AWS_REGION}" \
        -var="backend_image=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-backend:$VERSION" \
        -var="frontend_image=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-frontend:$VERSION" \
        -var="db_password=${DB_PASSWORD}" \
        -var="redis_auth_token=${REDIS_AUTH_TOKEN}" \
        -var="domain_name=${DOMAIN_NAME:-}" \
        -var="ssl_certificate_arn=${SSL_CERTIFICATE_ARN:-}" \
        -out=tfplan
    
    # Apply changes
    if [[ "${AUTO_APPROVE:-false}" == "true" ]]; then
        terraform apply -auto-approve tfplan
    else
        log_warning "Review the plan above. Type 'yes' to continue with deployment:"
        terraform apply tfplan
    fi
    
    # Save outputs
    terraform output -json > "../terraform-outputs.json"
    
    cd ..
    
    log_success "Infrastructure deployed successfully"
}

# Deploy application to ECS
deploy_application() {
    log_info "Deploying application to ECS..."
    
    # Get cluster name from Terraform outputs
    local cluster_name
    cluster_name=$(jq -r '.ecs_cluster_name.value' terraform-outputs.json)
    
    # Update backend service
    log_info "Updating backend service..."
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "${PROJECT_NAME}-${ENVIRONMENT}-backend" \
        --force-new-deployment \
        --desired-count 2 > /dev/null
    
    # Update frontend service
    log_info "Updating frontend service..."
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "${PROJECT_NAME}-${ENVIRONMENT}-frontend" \
        --force-new-deployment \
        --desired-count 2 > /dev/null
    
    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    aws ecs wait services-stable \
        --cluster "$cluster_name" \
        --services "${PROJECT_NAME}-${ENVIRONMENT}-backend" "${PROJECT_NAME}-${ENVIRONMENT}-frontend"
    
    log_success "Application deployed successfully"
}

# Run health checks
health_check() {
    log_info "Running health checks..."
    
    # Get ALB DNS name
    local alb_dns
    alb_dns=$(jq -r '.alb_dns_name.value' terraform-outputs.json)
    
    # Wait for ALB to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "Health check attempt $attempt/$max_attempts..."
        
        if curl -f -s "http://$alb_dns/health" > /dev/null; then
            log_success "Health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error_exit "Health check failed after $max_attempts attempts"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    
    local api_tests=(
        "/health"
        "/api/v1/health"
    )
    
    for endpoint in "${api_tests[@]}"; do
        if curl -f -s "http://$alb_dns$endpoint" > /dev/null; then
            log_success "✅ $endpoint - OK"
        else
            log_warning "⚠️ $endpoint - Failed"
        fi
    done
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Get cluster name and task definition
    local cluster_name
    cluster_name=$(jq -r '.ecs_cluster_name.value' terraform-outputs.json)
    
    local backend_task_def
    backend_task_def=$(jq -r '.backend_task_definition_arn.value' terraform-outputs.json)
    
    # Run migration task
    local task_arn
    task_arn=$(aws ecs run-task \
        --cluster "$cluster_name" \
        --task-definition "$backend_task_def" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$(jq -r '.private_subnet_ids.value[]' terraform-outputs.json | tr '\n' ',' | sed 's/,$//')],securityGroups=[$(jq -r '.ecs_security_group_id.value' terraform-outputs.json)],assignPublicIp=DISABLED}" \
        --overrides '{"containerOverrides":[{"name":"backend","command":["python","scripts/migrate.py"]}]}' \
        --query 'tasks[0].taskArn' \
        --output text)
    
    # Wait for migration to complete
    log_info "Waiting for migrations to complete..."
    aws ecs wait tasks-stopped --cluster "$cluster_name" --tasks "$task_arn"
    
    # Check if migration was successful
    local exit_code
    exit_code=$(aws ecs describe-tasks \
        --cluster "$cluster_name" \
        --tasks "$task_arn" \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)
    
    if [[ "$exit_code" == "0" ]]; then
        log_success "Database migrations completed successfully"
    else
        error_exit "Database migrations failed with exit code $exit_code"
    fi
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove old Docker images
    docker image prune -f || true
    
    # Clean up old ECS task definitions (keep last 5)
    aws ecs list-task-definitions \
        --family-prefix "${PROJECT_NAME}-${ENVIRONMENT}-backend" \
        --status INACTIVE \
        --sort DESC \
        --query 'taskDefinitionArns[5:]' \
        --output text | xargs -r aws ecs delete-task-definition --task-definition || true
    
    aws ecs list-task-definitions \
        --family-prefix "${PROJECT_NAME}-${ENVIRONMENT}-frontend" \
        --status INACTIVE \
        --sort DESC \
        --query 'taskDefinitionArns[5:]' \
        --output text | xargs -r aws ecs delete-task-definition --task-definition || true
    
    log_success "Cleanup completed"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."
    
    local report_file="deployment-report-${VERSION}.json"
    
    cat > "$report_file" << EOF
{
  "deployment": {
    "version": "$VERSION",
    "environment": "$ENVIRONMENT",
    "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "git_commit": "$(git rev-parse HEAD)",
    "git_branch": "$(git branch --show-current)"
  },
  "infrastructure": $(cat terraform-outputs.json),
  "images": {
    "backend": "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-backend:$VERSION",
    "frontend": "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-frontend:$VERSION"
  }
}
EOF
    
    log_success "Deployment report saved to $report_file"
}

# Main deployment function
main() {
    log_info "🚀 Starting AI Assistant MVP deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "Region: $AWS_REGION"
    
    # Deployment steps
    check_dependencies
    validate_env
    
    if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
        build_and_push
    fi
    
    deploy_infrastructure
    
    if [[ "${SKIP_MIGRATIONS:-false}" != "true" ]]; then
        run_migrations
    fi
    
    deploy_application
    health_check
    
    if [[ "${SKIP_CLEANUP:-false}" != "true" ]]; then
        cleanup
    fi
    
    generate_report
    
    log_success "🎉 Deployment completed successfully!"
    log_info "Application URL: $(jq -r '.environment_summary.value.application_url' terraform-outputs.json)"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 