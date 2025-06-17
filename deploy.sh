#!/bin/bash

# =============================================================================
# AI Assistant MVP - Quick Production Deployment Script
# =============================================================================

set -e  # Exit on any error

echo "🚀 AI Assistant MVP - Production Deployment"
echo "=========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   exit 1
fi

# Configuration
PROJECT_DIR="/opt/ai-assistant"
BACKUP_DIR="/opt/backups/ai-assistant"
LOG_FILE="/var/log/ai-assistant-deploy.log"

# Functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_dependencies() {
    log "🔍 Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log "❌ Docker is not installed. Installing..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        log "✅ Docker installed. Please log out and back in, then re-run this script."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log "❌ Docker Compose is not installed. Installing..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    log "✅ Dependencies checked"
}

setup_environment() {
    log "⚙️ Setting up environment..."
    
    # Create directories
    sudo mkdir -p "$PROJECT_DIR" "$BACKUP_DIR"
    sudo chown $USER:$USER "$PROJECT_DIR" "$BACKUP_DIR"
    
    # Setup environment file
    if [[ ! -f "$PROJECT_DIR/.env.production" ]]; then
        log "📝 Creating environment configuration..."
        cp .env.production.template "$PROJECT_DIR/.env.production"
        
        # Generate random secrets
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET_KEY=$(openssl rand -hex 32)
        POSTGRES_PASSWORD=$(openssl rand -hex 16)
        
        # Update environment file with generated secrets
        sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/" "$PROJECT_DIR/.env.production"
        sed -i "s/your-jwt-secret-key-different-from-main-secret/$JWT_SECRET_KEY/" "$PROJECT_DIR/.env.production"
        sed -i "s/secure_password_here/$POSTGRES_PASSWORD/" "$PROJECT_DIR/.env.production"
        
        log "⚠️  Please edit $PROJECT_DIR/.env.production with your API keys and domain settings"
        log "⚠️  Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, domain names"
        echo "Press Enter when you've updated the .env.production file..."
        read
    fi
    
    log "✅ Environment setup complete"
}

deploy_application() {
    log "🚢 Deploying application..."
    
    # Copy files to project directory
    rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' . "$PROJECT_DIR/"
    
    cd "$PROJECT_DIR"
    
    # Build and start services
    log "🏗️ Building Docker images..."
    docker-compose -f docker-compose.prod.yml build
    
    log "🚀 Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log "⏳ Waiting for services to start..."
    sleep 30
    
    log "✅ Application deployed"
}

run_health_checks() {
    log "🏥 Running health checks..."
    
    # Check backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ Backend is healthy"
    else
        log "❌ Backend health check failed"
        return 1
    fi
    
    # Check frontend
    if curl -f http://localhost:3000/ > /dev/null 2>&1; then
        log "✅ Frontend is healthy"
    else
        log "❌ Frontend health check failed"
        return 1
    fi
    
    # Check database
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U ai_assistant_user > /dev/null 2>&1; then
        log "✅ Database is healthy"
    else
        log "❌ Database health check failed"
        return 1
    fi
    
    log "✅ All health checks passed"
}

setup_monitoring() {
    log "📊 Setting up monitoring..."
    
    # Setup log rotation
    sudo tee /etc/logrotate.d/ai-assistant > /dev/null <<EOF
/var/log/ai-assistant/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF
    
    log "✅ Monitoring setup complete"
}

setup_backup() {
    log "💾 Setting up backup..."
    
    # Create backup script
    sudo tee /usr/local/bin/ai-assistant-backup.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="$BACKUP_DIR"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Database backup
docker-compose -f $PROJECT_DIR/docker-compose.prod.yml exec -T postgres pg_dump -U ai_assistant_user ai_assistant_prod | gzip > \$BACKUP_DIR/db_backup_\$DATE.sql.gz

# Qdrant backup
docker-compose -f $PROJECT_DIR/docker-compose.prod.yml exec -T qdrant tar czf - /qdrant/storage > \$BACKUP_DIR/qdrant_backup_\$DATE.tar.gz

# Cleanup old backups (keep 30 days)
find \$BACKUP_DIR -name "*.gz" -type f -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF
    
    sudo chmod +x /usr/local/bin/ai-assistant-backup.sh
    
    # Setup cron job
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/ai-assistant-backup.sh") | crontab -
    
    log "✅ Backup setup complete"
}

show_access_info() {
    log "🎉 Deployment Complete!"
    echo ""
    echo "🌐 Access Information:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Health: http://localhost:8000/health"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana: http://localhost:3001 (admin/admin)"
    echo ""
    echo "📋 Management Commands:"
    echo "   View logs: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml logs -f"
    echo "   Stop: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml down"
    echo "   Restart: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml restart"
    echo "   Backup: /usr/local/bin/ai-assistant-backup.sh"
    echo ""
    echo "⚠️  Next Steps:"
    echo "   1. Configure SSL certificates for HTTPS"
    echo "   2. Set up domain DNS records"
    echo "   3. Configure firewall rules"
    echo "   4. Test backup and restore procedures"
    echo ""
}

# Main execution
main() {
    log "🚀 Starting AI Assistant MVP deployment..."
    
    check_dependencies
    setup_environment
    deploy_application
    
    if run_health_checks; then
        setup_monitoring
        setup_backup
        show_access_info
        log "✅ Deployment successful!"
    else
        log "❌ Deployment failed - health checks failed"
        log "📋 Check logs: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml logs"
        exit 1
    fi
}

# Run main function
main "$@" 