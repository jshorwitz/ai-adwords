# Agent Orchestration System - User Guide

## Overview

The AI AdWords agent system provides autonomous and assisted agents for cross-channel ads platform management. The system handles Google Ads, Reddit Ads, and X/Twitter Ads with real-time optimization and attribution analysis.

## Agent Taxonomy

| Agent | Type | Trigger | Responsibilities |
|-------|------|---------|------------------|
| **ingestor-google** | ETL | Cron (2h) / Manual | Pull Google Ads metrics via GAQL, normalize to `ad_metrics` |
| **ingestor-reddit** | ETL | Cron (2h) / Manual | Pull Reddit Ads metrics (mockable), normalize |
| **ingestor-x** | ETL | Cron (2h) / Manual | Pull X/Twitter Ads metrics (mockable), normalize |
| **touchpoint-extractor** | Transform | Cron (10m) | Derive click/landing touchpoints from events → `touchpoints` |
| **conversion-uploader** | Activation | Nightly | Send server-side conversions back to platforms |
| **budget-optimizer** | Decision | Nightly | Compute CAC/ROAS by campaign; scale budgets ±10–20% |
| **keywords-hydrator** | Decision | Weekly | Pull keyword metrics from external sources |

## Quick Start

### 1. List Available Agents

```bash
poetry run python -m src.cli_agents list
```

### 2. Run Agent Demo Workflow

```bash
poetry run python -m src.cli_agents demo
```

### 3. Run Individual Agent (Dry Run)

```bash
poetry run python -m src.cli_agents run budget-optimizer --dry-run
```

### 4. Run Agent with Date Range

```bash
poetry run python -m src.cli_agents run ingestor-google --start 2025-01-01 --end 2025-01-10 --dry-run
```

### 5. Check Agent Status

```bash
poetry run python -m src.cli_agents status
```

## Agent Details

### Ingestor Agents

#### ingestor-google
- **Purpose**: Pull Google Ads campaign metrics using GAQL
- **Output**: Normalizes to `ad_metrics` table with platform='google'
- **Features**:
  - Converts costMicros to USD
  - Handles rate limiting and retries
  - Supports custom date ranges
  - Uses existing reporting infrastructure

```bash
# Run Google Ads ingestion for last 7 days
poetry run python -m src.cli_agents run ingestor-google --start 2025-01-03 --end 2025-01-10
```

#### ingestor-reddit
- **Purpose**: Pull Reddit Ads metrics (mockable for development)
- **Mock Mode**: Set `MOCK_REDDIT=true` environment variable
- **Output**: Normalizes to `ad_metrics` table with platform='reddit'

```bash
# Run Reddit ingestion with mock data
MOCK_REDDIT=true poetry run python -m src.cli_agents run ingestor-reddit --dry-run
```

#### ingestor-x
- **Purpose**: Pull X/Twitter Ads metrics (mockable for development)
- **Mock Mode**: Default enabled, set `MOCK_TWITTER=false` to use real API
- **Output**: Normalizes to `ad_metrics` table with platform='x'

### Transform Agents

#### touchpoint-extractor
- **Purpose**: Extract touchpoints from PostHog events or events table
- **Logic**: Identifies platform from click IDs (gclid → google, rdt_cid → reddit, twclid → x)
- **Output**: Creates touchpoints table with attribution data
- **Frequency**: Every 10 minutes to capture real-time events

### Activation Agents

#### conversion-uploader
- **Purpose**: Send conversions back to ad platforms using Enhanced Conversions
- **Supports**: Google Ads Enhanced Conversions, Reddit CAPI, X CAPI
- **Mapping**: Uses click IDs to match conversions to platform clicks
- **Safety**: Always logs payloads, supports dry-run validation

```bash
# Preview conversion uploads
poetry run python -m src.cli_agents run conversion-uploader --dry-run
```

### Decision Agents

#### budget-optimizer
- **Purpose**: Analyze 14-day CAC/ROAS performance and adjust budgets
- **Rules**:
  - CAC < target & ROAS ≥ target → +15% budget (up to max)
  - CAC > target × 1.2 → -20% budget (down to min)
  - CAC > target × 2 & ROAS < target × 0.5 → pause campaign
- **Guardrails**: Minimum conversion volume (5), budget caps per campaign
- **Frequency**: Nightly at 3:00 AM

```bash
# Preview budget optimizations
poetry run python -m src.cli_agents run budget-optimizer --dry-run
```

#### keywords-hydrator  
- **Purpose**: Enrich keywords with external data (volume, CPC, competition)
- **Sources**: Keyword research APIs (configurable)
- **Batching**: ≤100 keywords per API request
- **Frequency**: Weekly on Mondays at 4:00 AM

## Configuration

### Environment Variables

```bash
# Core Settings
LOG_LEVEL=info
DRY_RUN=false

# Database
DB_URL=mysql://ads_user:ads_pass@singlestore:3306/ads_unified

# Mock Flags (for development)
MOCK_REDDIT=true
MOCK_TWITTER=true

# Provider Credentials
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_DEVELOPER_TOKEN=...
REDDIT_CLIENT_ID=...
TWITTER_API_KEY=...
```

### Agent Job Input Format

```json
{
  "job_id": "budget-optimizer-20250110_143000",
  "run_id": "uuid-string",
  "params": {
    "target_cac": 200.0,
    "custom_param": "value"
  },
  "window": {
    "start": "2025-01-01", 
    "end": "2025-01-10"
  },
  "dry_run": true
}
```

### Agent Result Format

```json
{
  "job_id": "budget-optimizer-20250110_143000",
  "run_id": "uuid-string",
  "ok": true,
  "metrics": {
    "campaigns_analyzed": 5,
    "budget_increases": 2,
    "budget_decreases": 1,
    "duration_seconds": 12.5
  },
  "records_written": 3,
  "notes": [
    "Analyzed 5 campaigns",
    "Applied 3 budget changes"
  ],
  "error": null
}
```

## Error Handling

### Retry Policy
- **Transient errors** (5xx, rate limit): Exponential backoff (1m, 4m, 10m) up to 5 attempts
- **Auth errors** (4xx): Mark FAILED-AUTH, notify admin
- **Schema errors**: Mark FAILED-SCHEMA, create ticket

### Dry Run Mode
All agents support `--dry-run` flag:
- Computes all logic without external API calls
- Logs what would be changed/uploaded
- Returns metrics showing impact
- Safe for testing and validation

## Monitoring

### Agent Status Dashboard

```bash
poetry run python -m src.cli_agents status
```

Shows:
- Recent agent runs with timestamps
- Success/failure status
- Duration and records processed
- Error details for failed runs

### Health Checks

Each agent writes to `agent_runs` table:
- `started_at` / `finished_at` timestamps  
- `ok` status and `stats` JSON
- `watermark` for incremental processing
- Error details and retry attempts

## Integration Examples

### Manual Agent Execution

```bash
# Run full ingestion workflow for specific date range
poetry run python -m src.cli_agents run ingestor-google --start 2025-01-01 --end 2025-01-07 --dry-run
poetry run python -m src.cli_agents run ingestor-reddit --start 2025-01-01 --end 2025-01-07 --dry-run  
poetry run python -m src.cli_agents run touchpoint-extractor --dry-run
poetry run python -m src.cli_agents run budget-optimizer --dry-run
```

### Custom Parameters

```bash
# Run budget optimizer with custom target CAC
poetry run python -m src.cli_agents run budget-optimizer --params '{"target_cac": 150.0}' --dry-run
```

### API Integration

The agent system can be triggered via API (future implementation):

```http
POST /api/agents/run
{
  "agent": "budget-optimizer",
  "window": {"start": "2025-01-01", "end": "2025-01-10"},
  "dry_run": true
}
```

## Development

### Adding New Agents

1. Extend appropriate base class (`IngestorAgent`, `DecisionAgent`, etc.)
2. Implement `run(job_input)` method
3. Register agent in `runner.py`
4. Add tests in `tests/test_agents.py`

```python
class MyCustomAgent(DecisionAgent):
    def __init__(self, agent_name: str = "my-custom-agent"):
        super().__init__(agent_name)
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        # Agent logic here
        return self.create_result(job_input, ok=True, metrics={"processed": 10})

# Register
agent_registry.register("my-custom-agent", MyCustomAgent)
```

### Testing Agents

```bash
# Test specific agent
poetry run python -m src.cli_agents test budget-optimizer

# Run all tests
make test

# Test with coverage
poetry run pytest tests/ --cov=src/agents/
```

## Best Practices

### Safety First
- Always test with `--dry-run` before production
- Validate date ranges and parameters
- Monitor agent status dashboard regularly
- Set appropriate budget caps and guardrails

### Performance
- Use appropriate batch sizes for API calls
- Implement caching for frequently accessed data
- Monitor API quotas and rate limits
- Use incremental processing with watermarks

### Debugging
- Check agent logs for detailed execution info
- Use dry-run mode to validate logic
- Examine agent metrics for performance insights
- Review error patterns in status dashboard

This agent system provides a robust foundation for autonomous ad management across multiple platforms with proper safety controls, monitoring, and extensibility.
