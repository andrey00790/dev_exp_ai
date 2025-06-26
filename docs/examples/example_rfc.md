---
title: "TinyURL Service High Scalability Design"
author: "System Architect Team"
status: "draft"
created: "2025-06-12"
rfc_number: "RFC-001"
---

# TinyURL Service High Scalability Design

## Problem Statement

We need to design a URL shortening service similar to TinyURL that can handle 100 million URLs per day while maintaining high availability, low latency, and data consistency.

### Current Challenges
- High traffic volume (100M URLs/day)
- Sub-100ms response time requirement
- Global distribution needs
- Analytics and tracking requirements

## System Requirements

### Functional Requirements
- Shorten long URLs to compact format
- Redirect shortened URLs to original URLs
- Custom alias support
- URL expiration functionality
- Basic analytics (click count, geographic data)

### Non-Functional Requirements
- **Availability**: 99.9% uptime
- **Scalability**: 100M URLs/day (~1,200 requests/second)
- **Performance**: <100ms response time
- **Durability**: No data loss
- **Security**: Prevent malicious URL injection

## High-Level Architecture

```
[Load Balancer] → [API Gateway] → [Application Servers]
                                       ↓
[Cache Layer (Redis)] ← → [Database Cluster]
                                       ↓
                              [Analytics Service]
```

### Key Components
1. **Load Balancer**: Distributes traffic across multiple regions
2. **API Gateway**: Rate limiting, authentication, routing
3. **Application Layer**: URL shortening/expansion logic
4. **Caching Layer**: Redis for hot URL lookups
5. **Database**: Distributed storage for URL mappings
6. **Analytics**: Real-time and batch processing

## Database Design

### URL Mapping Table
```sql
CREATE TABLE url_mappings (
    short_code VARCHAR(10) PRIMARY KEY,
    original_url TEXT NOT NULL,
    user_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    click_count BIGINT DEFAULT 0,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

### Sharding Strategy
- Shard by short_code hash
- 1000 shards initially
- Auto-scaling based on storage utilization

## API Design

### Core Endpoints

#### Shorten URL
```
POST /api/v1/shorten
{
    "url": "https://example.com/very/long/url",
    "custom_alias": "optional",
    "expires_in": 86400
}

Response:
{
    "short_url": "https://tiny.ly/abc123",
    "short_code": "abc123",
    "expires_at": "2025-06-13T19:00:00Z"
}
```

#### Redirect
```
GET /{short_code}
→ 302 Redirect to original URL
```

## Caching Strategy

### Redis Configuration
- **Hot Data**: Recently accessed URLs (80/20 rule)
- **TTL**: 24 hours for URL mappings
- **Eviction**: LRU policy
- **Replication**: Master-slave setup per region

### Cache Patterns
- **Write-through**: Update cache on URL creation
- **Cache-aside**: Load on cache miss
- **Refresh-ahead**: Proactive cache refresh for hot URLs

## Security Considerations

### Input Validation
- URL format validation
- Malicious URL detection
- Rate limiting per IP/user
- CAPTCHA for suspicious activity

### Access Control
- API key authentication
- User-based URL management
- Admin endpoints protection

## Monitoring & Observability

### Key Metrics
- **Throughput**: Requests per second
- **Latency**: P50, P95, P99 response times
- **Error Rate**: 4xx/5xx responses
- **Cache Hit Ratio**: Redis performance
- **Database Performance**: Query latency

### Alerting
- Response time > 100ms
- Error rate > 0.1%
- Cache hit ratio < 80%
- Database connection pool exhaustion

## Implementation Plan

### Phase 1: Core Service (Week 1-2)
- Basic URL shortening/expansion
- Single database setup
- Simple caching layer

### Phase 2: Scalability (Week 3-4)
- Database sharding
- Redis cluster setup
- Load balancer configuration

### Phase 3: Advanced Features (Week 5-6)
- Analytics service
- Custom aliases
- URL expiration

### Phase 4: Production Hardening (Week 7-8)
- Security implementation
- Monitoring setup
- Performance optimization

## Risk Assessment

### High Risk
- **Database hotspots**: Mitigated by proper sharding
- **Cache invalidation**: Handled by TTL and refresh strategies
- **Security vulnerabilities**: Addressed by input validation

### Medium Risk
- **Third-party dependencies**: Circuit breakers implemented
- **Regional failures**: Multi-region deployment

### Low Risk
- **Algorithm efficiency**: Base62 encoding is well-tested
- **URL collision**: 62^7 combinations provide sufficient space 