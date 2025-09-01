# Google Ads API – Design, Compliance, and Use-Case Summary

Owner: Joel Horwitz (joel@neoteric3d.com)
Support: manager@neoteric3d.com
Product: AI AdWords – Google Ads performance monitoring, optimization recommendations, and reporting

## 1. Executive Summary
AI AdWords is a first‑party tool used to manage and analyze our own Google Ads accounts (and, where applicable, authorized client accounts under our MCC). It retrieves campaign and keyword performance data via the Google Ads API, generates insights, and produces dashboards and reports. All usage complies with Google Ads API Terms of Service and Display Requirements.

Planned Access Level: Basic/Standard developer token to enable production access for non‑test accounts.

## 2. Primary Use Cases
- Performance reporting (campaigns, ad groups, keywords, search terms)
- Diagnostics and alerting (anomaly detection, pacing, threshold-based alerts)
- Optimization insights (bid strategy tuning recommendations, negative keyword mining, ad copy tests)
- Limited automated changes (optional; defaults to validate_only unless explicitly enabled)

We will limit mutating operations to the following, and only after validation:
- Adding negative keywords
- Adjusting budgets and bid strategy settings (tCPA/tROAS) on selected campaigns
- Pausing clearly underperforming keywords (opt‑in only)

## 3. Users and Access Scope
- Internal marketing team and authorized account managers.
- Only accounts we own or are explicitly granted access to under our MCC (login_customer_id set and enforced).
- No resale of data or services to third parties.
- No sharing of Google Ads data with unauthorized parties.

## 4. Authentication & Authorization
- OAuth 2.0 for Google Ads API access using a refresh token stored securely (encrypted at rest).
- Always set `login_customer_id` (digits only) to the MCC CID to properly scope requests.
- For read-only dashboards, we use a service account only for BigQuery access (not for Google Ads API, which uses OAuth).
- Access tokens are short‑lived; refresh tokens and developer token are treated as secrets.

## 5. Data Flow & Architecture
- Google Ads API (read) → ETL Process → BigQuery (data warehouse) → Streamlit dashboard for visualization.
- Optional optimizations are executed via Google Ads API mutates with `validate_only=True` by default.

Components:
- Reporting (GAQL SearchStream/Search) for performance data export.
- ETL consolidates multiple customers and loads into partitioned BigQuery tables.
- Dashboard visualizes trends and aggregates (no PII).
- Optimization engine suggests actions, requires explicit approval to mutate.

## 6. Data Storage & Retention
- Storage: BigQuery dataset (project-owned, GCP managed).
- Encryption: GCP-managed encryption at rest; TLS in transit.
- Retention: 24 months default, configurable via dataset policies.
- PII: Not stored. We do not ingest or persist end‑user personal data. Data is aggregate performance metrics (impressions, clicks, cost, conversions, CTR, CPC, QS, etc.).
- Audit: All mutating actions are logged (who, what, when, before/after state) for traceability.

## 7. Security & Secrets Management
- Secrets stored in environment (.env for local dev; secret stores in deployment) and never committed to VCS.
- Tokens and keys restricted to least-privilege service accounts.
- Access controls enforced at application and cloud levels (IAM roles for BigQuery read/write).
- Regular key rotation policy for OAuth client secrets and service accounts.

## 8. Rate Limiting, Quotas, and Error Handling
- Exponential backoff on transient errors (GoogleAdsException, GoogleAPICallError, RetryError).
- Respect daily quotas; batch and paginate large reports.
- Caching (where applicable) to limit redundant queries.
- Circuit breakers to stop/slow jobs if quota/threshold is approached.

## 9. Compliance With Google Policies
- Terms of Service: Accepted and enforced within code (read-only defaults, validate_only for mutates).
- Display Requirements: We do not alter Google Ads performance data or misrepresent metrics. All UI labels and metrics map directly to Google Ads definitions.
- No scraping; only approved API endpoints are used.
- No sharing or selling of Google Ads data. No data reselling marketplace.
- Respect user privacy; no PII stored.

## 10. API Surfaces & Objects Used
- Reports (GAQL search/searchStream) on:
  - campaign, ad_group, keyword_view
  - metrics.* (impressions, clicks, cost_micros, conversions, ctr, average_cpc, cost_per_conversion, conversions_value)
  - segments.date
- Mutating endpoints (optional, gated and opt‑in):
  - CampaignBudgetService (budget adjustments)
  - RecommendationService (reading recommendations)
  - AdGroupCriterionService (negative keywords; pause underperformers)
- All writes use field masks; `partial_failure=True` for bulk operations; `validate_only=True` by default.

## 11. Volume Estimates
- Customers: 1–25 initially
- Data refresh cadence: hourly to daily
- Queries per day: ~1–5 per entity type per customer (~100–300/day)
- Mutates per day: 0–50 (opt‑in only)
- Peak QPS: << 1; heavy jobs staggered; pagination for large responses.

## 12. Monitoring & Alerting
- Application logs for all API requests (request_id, customer_id, operation).
- Error alerts for AUTHENTICATION_ERROR, QUOTA_ERROR, RATE_LIMIT_ERROR.
- Budget utilization/pacing alerts.
- Health checks for ETL pipelines and dashboard.

## 13. Testing Strategy
- Test accounts: All development and validation executed first against Google Ads test accounts.
- Validate-only: Mutations run with `validate_only=True` before production enablement.
- Integration tests: GAQL queries validated with known test data; fallbacks for API connectivity.

## 14. Privacy & Data Protection
- No end-user PII collected or stored.
- Only aggregate campaign/ad group/keyword metrics are stored for analysis.
- Data access limited to authorized employees with least-privilege IAM.
- Data retention policy documented and enforced via BigQuery dataset policies.

## 15. Support & Contact
- Primary contact: joel@neoteric3d.com
- Website: http://www.neoteric3d.com
- Support distribution: manager@neoteric3d.com
- Incident response: document in runbook; 24–48h SLA for critical issues.

## 16. Screens/UX Summary (Dashboard)
- Key metrics (Impressions, Clicks, Spend, Conversions, CTR, CPC, CVR)
- Daily trends (clicks, conversions, CTR vs cost)
- Campaign summary table with sortable KPIs
- Keyword analysis (top keywords, cost vs conversions, low CTR/QS flags)
- Optional: insight panel for recommendations; explicit approval required for changes

## 17. Commitments & Attestations
- We will only access accounts we own or manage with explicit authorization under our MCC.
- We will comply with Google Ads API Terms of Service, Display Requirements, and all policies.
- We will not share, resell, or expose Google Ads data to third parties.
- We will implement and maintain appropriate technical and organizational measures to protect the data.
- We will use test accounts for development and validation before enabling production access.

## 18. Appendices
- Architecture diagram (high level):
  - Google Ads API → ETL → BigQuery → Dashboard
  - Optional → Optimization (validate_only by default)
- Example GAQL Queries used
- Example dashboard screenshots (available upon request)
