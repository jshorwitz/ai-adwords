# AI AdWords - Agent Guidance

## Project Overview
This is a Google Ads AI application that monitors ad performance, makes automated optimizations, and delivers regular reports.

# AGENTS.md — Google Ads Management App

## What we're building
A backend app that manages Google Ads (AdWords) via the Google Ads API from our MCC, for a B2B SaaS account. See @docs/GOOGLE_ADS_APP_SPEC.md for scope, data model, and API objects.

## Language & toolchain
- Python 3.11+ with Poetry
- Postgres for config/state; SingleStore for reporting warehouse
- pytest, mypy, ruff/black
- Docker for local/dev parity

## Build & test
- Install: `make setup`
- Lint/Typecheck: `make check`
- Unit tests: `make test`
- All tests (fast): `make ci`
- Run a local “dry-run” E2E with Google Ads `validate_only=True`: `make e2e-validate`

## Folder layout the agent should create
- `src/ads/ads_client.py` – client factory (OAuth refresh token, developer token, login_customer_id)
- `src/ads/accounts.py` – list/link/create customers
- `src/ads/campaigns.py` – budgets, campaigns, ad groups, criteria, RSAs, negatives
- `src/ads/pmax.py` – PMax + asset groups
- `src/ads/audiences.py` – remarketing lists & Customer Match
- `src/ads/measurement.py` – conversion actions, offline/ECL uploads, adjustments
- `src/ads/reporting.py` – GAQL SearchStream exporters
- `src/ads/optimize.py` – SQR mining, pacing, recommendations, experiments
- `src/cli.py` – Typer/Click CLI wrappers for the above
- `tests/**` – unit tests + “validate_only” integration tests

## Non‑negotiable guardrails
- **Never** push commits or tags; open a PR instead.
- **Never** print or commit secrets. Use `.env` (untracked) and `.env.template` (tracked).
- Default all mutates to `validate_only=True` unless `ENABLE_REAL_MUTATES=1` is set.
- Use **field masks** on updates; prefer **partial_failure=True** on bulk mutates.
- For Google Ads calls, always set `login_customer_id` (MCC CID, digits only).

## How to review your work
- After edits, run: `make check && make test`
- For any mutate, run `make e2e-validate` first and paste output into the PR.
- Include GAQL output samples for new reports.

## References for the agent
- Primary spec: @docs/GOOGLE_ADS_APP_SPEC.md
- Acceptance: @docs/ACCEPTANCE.md
- Example GAQL: include in @docs/GOOGLE_ADS_APP_SPEC.md under “Optimization & reporting”

## Editor tips for Amp
- Think hard before large refactors.
- Keep threads focused: one epic per thread (scaffold → search campaigns → audiences → measurement → reporting → optimization).


## Technology Stack
- **Runtime**: Node.js with TypeScript
- **Database**: PostgreSQL 
- **APIs**: Google Ads API v14
- **Authentication**: OAuth 2.0
- **Testing**: Jest
- **Build**: npm/yarn

## Key Commands

### Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Testing
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run integration tests
npm run test:integration
```

### Build & Deploy
```bash
# Build for production
npm run build

# Start production server
npm start

# Database migrations
npm run db:migrate

# Seed database
npm run db:seed
```

## Code Style & Conventions

### File Structure
- `/src` - Main application source code
- `/src/api` - API route handlers
- `/src/services` - Business logic services
- `/src/models` - Database models and types
- `/src/utils` - Utility functions
- `/src/config` - Configuration files
- `/tests` - Test files
- `/docs` - Documentation

### Naming Conventions
- **Files**: kebab-case (e.g., `google-ads-service.ts`)
- **Variables/Functions**: camelCase (e.g., `getCampaignData`)
- **Classes**: PascalCase (e.g., `GoogleAdsClient`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_VERSION`)
- **Interfaces**: PascalCase with 'I' prefix (e.g., `ICampaignData`)

### TypeScript Guidelines
- Use strict type checking
- Define interfaces for all external API responses
- Use enums for fixed value sets
- Prefer `interface` over `type` for object shapes
- Use `readonly` for immutable properties

### Error Handling
- Use custom error classes that extend Error
- Always log errors with context
- Return proper HTTP status codes
- Validate all inputs at API boundaries

## Environment Setup

### Required Environment Variables
```bash
# Google Ads API
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_ADS_CUSTOMER_ID=your_customer_id

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_adwords

# Authentication
JWT_SECRET=your_jwt_secret
SESSION_SECRET=your_session_secret

# Email/Notifications
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email
SMTP_PASS=your_password
SLACK_WEBHOOK_URL=your_slack_webhook

# Application
NODE_ENV=development
PORT=3000
LOG_LEVEL=debug
```

### Database Setup
1. Install PostgreSQL
2. Create database: `createdb ai_adwords`
3. Run migrations: `npm run db:migrate`
4. Seed data: `npm run db:seed`

## Google Ads API Integration

### Authentication Flow
1. User authorizes application via OAuth 2.0
2. Store refresh token securely
3. Use refresh token to get access tokens
4. Include customer ID in all API requests

### Rate Limiting
- Google Ads API has strict rate limits
- Implement exponential backoff for retries
- Use batch requests when possible
- Cache frequently accessed data

### Key API Endpoints
- **Campaigns**: `/googleads/v14/customers/{customer_id}/campaigns`
- **Reports**: `/googleads/v14/customers/{customer_id}/googleAds:searchStream`
- **Keywords**: `/googleads/v14/customers/{customer_id}/adGroupCriteria`

## Testing Guidelines

### Unit Tests
- Test all service methods
- Mock external API calls
- Test error conditions
- Aim for >80% coverage

### Integration Tests
- Test API endpoints end-to-end
- Use test database
- Test authentication flows
- Test Google Ads API integration

### E2E Tests
- Test complete user workflows
- Test critical business logic
- Use test Google Ads account

## Deployment

### Docker
- Use multi-stage builds
- Include health checks
- Set proper resource limits
- Use non-root user

### Environment-specific configs
- **Development**: Debug logging, hot reload
- **Staging**: Production-like settings, test data
- **Production**: Optimized builds, monitoring

## Monitoring & Alerts

### Key Metrics
- API response times
- Error rates
- Google Ads API quota usage
- Database connection pool status

### Alerting Thresholds
- Error rate > 5%
- API response time > 2s
- API quota usage > 80%
- Database connections > 90%

## Security

### API Security
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Log security events

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Rotate API keys regularly
- Follow GDPR compliance

## Common Issues & Solutions

### Google Ads API Errors
- **AUTHENTICATION_ERROR**: Check OAuth tokens and customer ID
- **QUOTA_ERROR**: Implement proper rate limiting
- **INVALID_CUSTOMER_ID**: Verify customer ID format

### Performance Issues
- Use connection pooling for database
- Implement caching for frequently accessed data
- Optimize database queries
- Use pagination for large datasets

## Resources
- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
