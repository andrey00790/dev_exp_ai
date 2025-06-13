# Reporting Service

Reporting Service microservice for the enterprise platform.

## Architecture Overview
This service implements reporting service functionality using:
- FastAPI (Python) or Express.js (Node.js)
- PostgreSQL or MongoDB for data storage
- Redis for caching
- Docker for containerization

## Features
- RESTful API endpoints
- Async processing capabilities  
- Comprehensive error handling
- Health check endpoints
- Metrics and monitoring
- Authentication and authorization

## Quick Start
```bash
# Using Docker
docker-compose up -d

# Or locally
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Documentation
- OpenAPI/Swagger UI: `/docs`
- ReDoc: `/redoc`
- Health check: `/health`

## Configuration
Environment variables:
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection for caching
- `JWT_SECRET`: Secret for JWT validation
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR)

## Testing
```bash
pytest tests/ -v --cov=app
```

## Deployment
See `deploy/` directory for Kubernetes manifests and Helm charts.
