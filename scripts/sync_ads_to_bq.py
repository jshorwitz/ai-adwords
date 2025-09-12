#!/usr/bin/env python3
"""Sync Google Ads performance data into BigQuery.

Usage:
  poetry run python scripts/sync_ads_to_bq.py --customers 1234567890,0987654321 --days 30

Requires env vars for Google Ads API and GCP BigQuery (see .env.template).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

# Ensure src on path
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

# Load .env early so we can read GOOGLE_ADS_CUSTOMER_ID
from dotenv import load_dotenv  # noqa: E402
load_dotenv()  # noqa: E402

from ads.etl_pipeline import GoogleAdsETLPipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync Google Ads data to BigQuery")
    p.add_argument(
        "--customers",
        required=False,
        default=None,
        help="Comma-separated list of customer IDs to sync (digits only). If omitted, uses $GOOGLE_ADS_CUSTOMER_ID or $GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    )
    p.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days back to fetch (default: 7)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    customer_str = args.customers or os.getenv("GOOGLE_ADS_CUSTOMER_ID") or os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    customers: List[str] = []
    if customer_str:
        customers = [c.strip().replace("-", "") for c in customer_str.split(",") if c.strip()]

    if not customers:
        print("No customers provided and no GOOGLE_ADS_CUSTOMER_ID/GOOGLE_ADS_LOGIN_CUSTOMER_ID set", file=sys.stderr)
        sys.exit(1)

    pipeline = GoogleAdsETLPipeline()
    pipeline.full_sync(customers, days_back=args.days)


if __name__ == "__main__":
    main()
