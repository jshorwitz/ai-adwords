# AI AdWords

An intelligent application for monitoring Google AdWords performance, making data-driven optimization changes, and delivering automated reports.

## Features
- Connect to Google AdWords APIs
- Monitor ad performance metrics
- Automated campaign optimization
- Regular performance reporting

## Setup
TBD

## Usage

### Mock mode (no Google Ads access required)
Use mock mode to develop and demo flows without API keys or approval:

- List campaigns (mocked data):

```bash
ADS_USE_MOCK=1 poetry run python -m src.cli campaigns --customer-id 1234567890 --action list
```

- Reporting demo data (historical metrics): set `ADS_USE_DEMO=1` to have reporting return generated sample datasets.

- List keywords (mocked data):

```bash
ADS_USE_MOCK=1 poetry run python -m src.cli keywords --customer-id 1234567890 --limit 10
```

- List accessible accounts (mocked):

```bash
ADS_USE_MOCK=1 poetry run python -m src.cli accounts
```

When ready to hit the real API, unset `ADS_USE_MOCK` and provide credentials via `.env` (see `.env.template`).

# Force redeploy Thu Sep 25 16:47:14 PDT 2025
