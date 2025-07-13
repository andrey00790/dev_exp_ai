# 🤖 VK Teams Integration Guide

## 📋 Overview

Complete guide for setting up and managing VK Teams bot integration with the AI Assistant platform. This integration allows users to interact with the AI Assistant directly through VK Teams chats.

## 🌟 Features

- **🔍 Semantic Search** - Find information across all connected data sources
- **📝 RFC Generation** - Create technical documents through chat commands
- **💬 Natural Language Processing** - Intelligent conversation handling
- **🔒 Access Control** - User and chat-based permissions
- **📊 Statistics & Analytics** - Usage tracking and performance metrics
- **🌐 Multi-language Support** - English and Russian interfaces

## 🏗️ Architecture

The VK Teams integration follows Clean Architecture principles:

```
infrastructure/vk_teams/
├── domain/          # Business logic and entities
├── application/     # Use cases and services  
├── infrastructure/  # External integrations and adapters
└── presentation/    # API endpoints and controllers
```

### Frontend Structure (Context7 Pattern)

```
frontend/src/infrastructure/vkTeams/
├── domain/         # Domain models and types
├── application/    # Context7 state management
├── infrastructure/ # API services and external integrations
└── presentation/   # React components and UI
```

## 🚀 Quick Start

### 1. Backend Setup

#### Environment Variables

Add the following to your `.env` file:

```env
# VK Teams Bot Configuration
VK_TEAMS_BOT_TOKEN=your_bot_token_here
VK_TEAMS_API_URL=https://api.internal.myteam.mail.ru/bot/v1
VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/vk-teams/webhook/events
VK_TEAMS_ENABLED=true

# VK OAuth (Optional - for access control)
VK_OAUTH_ENABLED=true
VK_OAUTH_CLIENT_ID=your_vk_app_id
VK_OAUTH_CLIENT_SECRET=your_vk_app_secret
VK_OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/auth/vk/callback
ALLOWED_VK_USERS=123456789,987654321
```

#### Install Dependencies

```bash
# Backend dependencies are already included in requirements.txt
pip install -r requirements.txt
```

#### Start the Application

```bash
# Development
python -m uvicorn app.main:app --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Create VK Teams Bot

1. **Find @MetaBot** in VK Teams
2. **Send command** `/newbot`
3. **Follow instructions** to create your bot
4. **Save the bot token** - you'll need it for configuration

### 3. Configure Bot via API

```bash
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "bot_token": "YOUR_BOT_TOKEN",
    "api_url": "https://api.internal.myteam.mail.ru/bot/v1",
    "webhook_url": "https://your-domain.com/api/v1/vk-teams/webhook/events",
    "auto_start": true,
    "allowed_users": ["123456789"],
    "allowed_chats": ["chat_id_1", "chat_id_2"]
  }'
```

### 4. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Environment Configuration

Add to `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VK_TEAMS_ENABLED=true
```

#### Add Context7 Providers

Update your `App.tsx`:

```tsx
import { AppProvider } from './contexts/AppContext';
import { VKTeamsProvider } from './infrastructure/vkTeams/application/VKTeamsContext';

function App() {
  return (
    <AppProvider>
      <VKTeamsProvider>
        {/* Your app components */}
      </VKTeamsProvider>
    </AppProvider>
  );
}
```

## 📚 API Reference

### Bot Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/vk-teams/bot/status` | GET | Get bot status |
| `/api/v1/vk-teams/bot/configure` | POST | Configure bot |
| `/api/v1/vk-teams/bot/start` | POST | Start bot |
| `/api/v1/vk-teams/bot/stop` | POST | Stop bot |
| `/api/v1/vk-teams/bot/stats` | GET | Get bot statistics |
| `/api/v1/vk-teams/bot/health` | GET | Health check |

### Webhook Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/vk-teams/webhook/events` | POST | Handle VK Teams events |
| `/api/v1/vk-teams/webhook/callback` | POST | Handle callback queries |

### Example Requests

#### Check Bot Status
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/vk-teams/bot/status
```

#### Get Bot Statistics
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/vk-teams/bot/stats
```

## 🎯 Bot Commands

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot interaction | `/start` |
| `/help` | Show available commands | `/help` |
| `/search <query>` | Search across data sources | `/search Docker deployment` |
| `/generate <description>` | Generate RFC document | `/generate API for user management` |
| `/status` | Show system status | `/status` |

### Advanced Commands

| Command | Description | Admin Only |
|---------|-------------|------------|
| `/settings` | Bot configuration | ✅ |
| `/analytics` | Usage analytics | ✅ |
| `/users` | Manage allowed users | ✅ |

### Natural Language

The bot also supports natural language queries:

- "Find documentation about Docker"
- "Generate an RFC for microservices architecture"
- "What's the current system status?"
- "Show me recent analytics"

## 🔒 Security & Access Control

### Authentication Methods

1. **VK OAuth Integration**
   - Users authenticate via VK account
   - Configurable user whitelist
   - Automatic user verification

2. **Chat-based Access**
   - Whitelist specific chats
   - Group/channel permissions
   - Admin-only commands

### Configuration Example

```json
{
  "allowed_users": ["123456789", "987654321"],
  "allowed_chats": ["chat_id_1", "group_id_2"],
  "vk_oauth_enabled": true,
  "admin_users": ["123456789"]
}
```

## 📊 Monitoring & Analytics

### Health Checks

Monitor bot health:

```bash
# Simple health check
curl http://localhost:8000/api/v1/vk-teams/bot/health

# Detailed status
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/vk-teams/bot/status
```

### Analytics Dashboard

The bot provides comprehensive analytics:

- **Message Statistics** - Total messages, response times
- **User Activity** - Active users, popular commands
- **Error Tracking** - Failed requests, error rates
- **Performance Metrics** - Response times, throughput

### Grafana Integration

Use the included Grafana dashboard:

```yaml
# monitoring/grafana/dashboards/vk-teams.json
{
  "title": "VK Teams Bot Metrics",
  "panels": [
    {
      "title": "Messages per Hour",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(vk_teams_messages_total[1h])"
        }
      ]
    }
  ]
}
```

## 🛠️ Development

### Local Development

```bash
# Start backend
python -m uvicorn app.main:app --reload

# Start frontend
cd frontend && npm start

# Run tests
pytest tests/integration/test_vk_teams_integration.py -v
```

### Testing

#### Unit Tests

```bash
# Backend tests
pytest tests/unit/test_vk_teams_bot.py

# Frontend tests
cd frontend && npm test
```

#### Integration Tests

```bash
# Test webhook processing
curl -X POST http://localhost:8000/api/v1/vk-teams/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test_event": "message", "test_data": {"text": "Hello Bot!"}}'
```

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

Check logs:

```bash
tail -f logs/app.log | grep "vk_teams"
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Use the included docker-compose.production.yml
docker-compose -f docker-compose.production.yml up -d
```

### Nginx Configuration

```nginx
# Add to your nginx.conf
location /api/v1/vk-teams/webhook/ {
    proxy_pass http://ai-assistant:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### SSL Certificate

VK Teams requires HTTPS for webhooks:

```bash
# Using Let's Encrypt
certbot --nginx -d your-domain.com
```

## 🔧 Troubleshooting

### Common Issues

#### Bot Not Responding

1. **Check bot token** - Verify in VK Teams
2. **Verify webhook URL** - Must be HTTPS and accessible
3. **Check permissions** - User must be in allowed list
4. **Review logs** - Look for error messages

```bash
# Check bot status
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/vk-teams/bot/status
```

#### Authentication Errors

1. **VK OAuth setup** - Verify app configuration
2. **User whitelist** - Check ALLOWED_VK_USERS
3. **JWT tokens** - Ensure valid authentication

#### Performance Issues

1. **Database performance** - Check query times
2. **AI API latency** - Monitor response times
3. **Resource usage** - CPU/memory consumption

### Debug Commands

```bash
# Test webhook manually
curl -X POST http://localhost:8000/api/v1/vk-teams/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check configuration
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/vk-teams/bot/status

# Health check
curl http://localhost:8000/api/v1/vk-teams/bot/health
```

## 📈 Performance Optimization

### Caching Strategy

```python
# Enable Redis caching for bot responses
REDIS_URL=redis://localhost:6379
CACHE_TTL=300  # 5 minutes
```

### Rate Limiting

```python
# Configure rate limits
RATE_LIMIT_MESSAGES_PER_MINUTE=20
RATE_LIMIT_COMMANDS_PER_MINUTE=10
```

### Resource Management

```yaml
# docker-compose.production.yml
services:
  ai-assistant:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## 🔄 Updates & Maintenance

### Version Updates

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update frontend
cd frontend && npm update
```

### Database Migrations

```bash
# Run migrations
alembic upgrade head
```

### Monitoring

Set up monitoring alerts:

```yaml
# monitoring/alertmanager/alerts.yml
groups:
  - name: vk-teams
    rules:
      - alert: VKTeamsBotDown
        expr: up{job="vk-teams-bot"} == 0
        for: 5m
        annotations:
          summary: "VK Teams bot is down"
```

## 📞 Support

- **📧 Email**: support@aiassistant.com
- **💬 Telegram**: @ai_assistant_support
- **🐛 Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **📖 Documentation**: [Full Documentation](https://docs.aiassistant.com/vk-teams)

## 🗺️ Roadmap

- [ ] **File Support** - Handle document uploads
- [ ] **Inline Buttons** - Interactive bot responses
- [ ] **Group Chat Features** - Enhanced group functionality
- [ ] **Push Notifications** - Proactive user notifications
- [ ] **Multi-language** - Additional language support
- [ ] **Advanced Analytics** - Conversation insights

---

**Status**: ✅ Production Ready  
**Version**: 2.0.0  
**Last Updated**: 2024-12-22 