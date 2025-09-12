# AI AdWords - Unified Ads Platform

## 🎯 Overview

A comprehensive cross-channel advertising platform with autonomous agents for Google Ads, Reddit Ads, and X/Twitter Ads. Built following the detailed AGENTS.md specification with full auth system, database integration, and API endpoints.

## ✨ Features

### 🔐 Authentication System
- **Email/Password Authentication** with Argon2id password hashing
- **Magic Link (Passwordless)** authentication 
- **Role-Based Access Control** (Admin, Analyst, Viewer)
- **Session Management** with secure HTTP-only cookies
- **JWT Support** for API access
- **Google OAuth** integration (ready to implement)

### 🤖 Agent Orchestration System
- **7 Autonomous Agents** covering the complete ads lifecycle
- **Multi-Platform Support** (Google Ads, Reddit Ads, X/Twitter Ads)
- **Dry-Run Mode** for safe testing and validation
- **Database Integration** for persistent state and metrics
- **CLI & API Interfaces** for manual and programmatic control

### 📊 Data Management
- **Unified Database Schema** for cross-platform metrics
- **Agent Execution Tracking** with detailed logging and metrics  
- **Campaign Performance Analysis** with CAC/ROAS optimization
- **Touchpoint Attribution** from events to conversions
- **External Keyword Integration** for research and expansion

### 🌐 Web API & Dashboard
- **RESTful API** with comprehensive auth and RBAC
- **Interactive API Documentation** (FastAPI/Swagger)
- **Agent Management Interface** for monitoring and control
- **Health Checks and Monitoring** for production readiness

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Poetry for dependency management

### Installation

```bash
# Clone and install
cd /path/to/ai-adwords
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your database and API credentials

# Start the application
poetry run python start_app.py
```

### First Steps

1. **Visit the Platform**: http://localhost:8000
2. **Create Admin Account**: 
   ```bash
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"securepassword123","name":"Admin User"}'
   ```
3. **Login and Get Session**:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"securepassword123"}'
   ```
4. **List Available Agents**:
   ```bash
   curl http://localhost:8000/agents/list -H "Cookie: sid=your_session_token"
   ```
5. **Run Agent Demo**:
   ```bash
   curl -X POST http://localhost:8000/agents/run \
     -H "Content-Type: application/json" \
     -H "Cookie: sid=your_session_token" \
     -d '{"agent":"budget-optimizer","dry_run":true}'
   ```

## 🤖 Agent System

### Available Agents

| Agent | Type | Function | Schedule |
|-------|------|----------|----------|
| **ingestor-google** | ETL | Pull Google Ads GAQL metrics | Every 2 hours |
| **ingestor-reddit** | ETL | Pull Reddit Ads metrics (mockable) | Every 2 hours |
| **ingestor-x** | ETL | Pull X/Twitter Ads metrics (mockable) | Every 2 hours |
| **touchpoint-extractor** | Transform | Extract click touchpoints from events | Every 10 minutes |
| **conversion-uploader** | Activation | Send conversions to platforms via CAPI | Nightly |
| **budget-optimizer** | Decision | Analyze CAC/ROAS and adjust budgets | Nightly |
| **keywords-hydrator** | Decision | Enrich keywords from external APIs | Weekly |

### Agent CLI

```bash
# List agents
poetry run python -m src.cli_agents list

# Run individual agent
poetry run python -m src.cli_agents run budget-optimizer --dry-run

# Demo workflow
poetry run python -m src.cli_agents demo

# Check status
poetry run python -m src.cli_agents status
```

### Agent API

```bash
# List agents
GET /agents/list

# Run agent
POST /agents/run
{
  "agent": "budget-optimizer",
  "window": {"start": "2025-01-01", "end": "2025-01-10"},
  "dry_run": true
}

# Get status
GET /agents/status

# Get run details
GET /agents/runs/{run_id}
```

## 📊 Database Schema

### Core Tables

- **users** - User accounts with RBAC
- **sessions** - Session management  
- **magic_links** - Passwordless authentication
- **oauth_accounts** - OAuth integrations
- **agent_runs** - Agent execution history
- **ad_metrics** - Unified cross-platform metrics
- **touchpoints** - User journey touchpoints
- **conversions** - Conversion events
- **campaign_policies** - Optimization rules
- **keywords_external** - External keyword data

### Key Relationships

```
users -> sessions (1:many)
users -> magic_links (1:many) 
users -> oauth_accounts (1:many)
agent_runs -> metrics via stats JSON
ad_metrics -> campaigns via platform+campaign_id
touchpoints -> users via user_id
conversions -> platforms via click_id
```

## 🔐 Authentication & Authorization

### User Roles

- **Admin**: Full system access, user management, agent execution
- **Analyst**: Agent execution, campaign optimization, reporting  
- **Viewer**: Read-only access to dashboards and reports

### Authentication Methods

1. **Email/Password**: Traditional authentication with secure hashing
2. **Magic Link**: Passwordless via email token (10-minute expiry)
3. **Session Cookies**: HTTP-only, secure, 24-hour expiry
4. **Bearer Tokens**: JWT for API access

### Example Auth Flow

```python
# Signup
POST /auth/signup {"email": "user@example.com", "password": "secure123"}

# Login
POST /auth/login {"email": "user@example.com", "password": "secure123"}
# Returns session cookie

# Magic Link
POST /auth/magic-link {"email": "user@example.com"}
GET /auth/magic?token=abc123
# Sets session cookie

# Get User Info
GET /auth/me
# Returns: {"id": 1, "email": "user@example.com", "role": "viewer"}
```

## 🚀 Deployment & Production

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_adwords

# Security  
SECRET_KEY=your-secret-key-32-chars-minimum
JWT_SECRET_KEY=your-jwt-secret

# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Features
MOCK_REDDIT=false
MOCK_TWITTER=false
ENABLE_REAL_MUTATES=false  # Safety: default to dry-run

# External APIs
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_DEVELOPER_TOKEN=...
REDDIT_CLIENT_ID=...
TWITTER_API_KEY=...
```

### Docker Setup

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only=main
COPY . .
EXPOSE 8000
CMD ["poetry", "run", "python", "start_app.py"]
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure production database with SSL
- [ ] Enable HTTPS with proper TLS certificates  
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up database backups
- [ ] Test disaster recovery procedures
- [ ] Review and set proper CORS origins
- [ ] Enable rate limiting on sensitive endpoints
- [ ] Set up health checks for load balancer

## 📈 Monitoring & Observability

### Health Checks

```bash
# Application health
GET /health
# Returns: {"status": "healthy", "agents_registered": 7}

# Agent system health  
GET /agents/health
# Returns: {"status": "healthy", "agents_registered": 7}
```

### Logs & Metrics

- **Structured Logging** with timestamps and context
- **Agent Execution Metrics** stored in database
- **API Access Logging** with user attribution
- **Error Tracking** with full stack traces
- **Performance Metrics** including response times

### Agent Monitoring

```bash
# Recent agent runs
GET /agents/status

# Specific run details
GET /agents/runs/{run_id}

# Cleanup old runs
POST /agents/cleanup {"days_to_keep": 30}
```

## 🔧 Development

### Project Structure

```
src/
├── agents/           # Agent system
│   ├── base.py      # Base agent classes
│   ├── ingestors.py # Data ingestion agents
│   ├── transforms.py# Data transformation agents  
│   ├── activations.py# Activation agents
│   ├── decisions.py # Decision/optimization agents
│   ├── database.py  # Agent database operations
│   └── runner.py    # Agent orchestration
├── api/             # FastAPI application
│   ├── app.py       # Main application
│   ├── auth_routes.py# Authentication endpoints
│   ├── agent_routes.py# Agent management endpoints
│   └── middleware.py# Auth & RBAC middleware
├── auth/            # Authentication system
│   ├── service.py   # Auth business logic
│   └── security.py  # Password/token utilities
├── models/          # Database models
│   ├── database.py  # Database connection
│   ├── auth.py      # Auth models
│   └── agents.py    # Agent & data models
└── cli_agents.py    # Agent CLI interface
```

### Adding New Agents

1. **Create Agent Class**:
   ```python
   class MyAgent(DecisionAgent):
       async def run(self, job_input: AgentJobInput) -> AgentResult:
           # Agent logic here
           return self.create_result(job_input, ok=True)
   ```

2. **Register Agent**:
   ```python
   agent_registry.register("my-agent", MyAgent)
   ```

3. **Add Tests**:
   ```python
   def test_my_agent():
       agent = MyAgent()
       result = await agent.run(mock_input)
       assert result.ok
   ```

### Testing

```bash
# Unit tests
poetry run pytest tests/

# Integration tests with database
poetry run pytest tests/ -m integration

# Agent system test
poetry run python test_app.py

# CLI test
poetry run python -m src.cli_agents demo
```

## 🎯 Roadmap & Future Enhancements

### Phase 1 - Completed ✅
- [x] Agent orchestration system with 7 agents
- [x] Authentication system with RBAC
- [x] Database schema and operations
- [x] REST API with comprehensive endpoints  
- [x] CLI interface for agent management
- [x] Production-ready deployment setup

### Phase 2 - Next Steps 🚧
- [ ] Google OAuth integration
- [ ] Agent scheduling with cron jobs
- [ ] Email system for magic links and alerts
- [ ] Advanced dashboard with React frontend  
- [ ] Webhook system for external integrations
- [ ] Multi-tenant support for agencies

### Phase 3 - Advanced Features 🔮
- [ ] Machine learning optimization models
- [ ] Advanced attribution modeling
- [ ] Real-time alerting and notifications
- [ ] Campaign performance forecasting
- [ ] A/B testing framework for ads
- [ ] Integration with additional ad platforms

## 📞 Support & Contributing

### Getting Help

1. **Documentation**: Check this README and AGENT_SYSTEM_GUIDE.md
2. **API Docs**: Visit /docs when running the application  
3. **Logs**: Check application logs for detailed error information
4. **Health Checks**: Use /health and /agents/health endpoints

### Contributing

1. **Fork** the repository
2. **Create** feature branch from main
3. **Follow** existing code patterns and conventions
4. **Add** tests for new functionality
5. **Update** documentation as needed
6. **Submit** pull request with clear description

### Code Standards

- **Python**: Follow PEP 8 with Black formatting
- **Type Hints**: Use throughout for better code clarity
- **Logging**: Include structured logging with context
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Security**: Follow OWASP guidelines for web security
- **Testing**: Aim for >80% test coverage

## 📄 License

MIT License - see LICENSE file for details.

---

**Built following the comprehensive AGENTS.md specification for autonomous cross-channel ad management** 🚀
