#!/usr/bin/env python3
"""Analyze Google Ads performance from BigQuery and print recommendations.

Usage:
  poetry run python scripts/analyze_account.py --days 30 [--campaign <name>]

Requires GOOGLE_CLOUD_PROJECT/BIGQUERY_DATASET_ID env and BigQuery tables populated.
"""
from __future__ import annotations

import argparse
import os
import sys
import math
from typing import Optional
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ads.bigquery_client import create_bigquery_client_from_env  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze account performance")
    p.add_argument("--days", type=int, default=30, help="Days back to analyze")
    p.add_argument("--campaign", type=str, default=None, help="Focus on a single campaign name")
    return p.parse_args()


def pct(n: float) -> float:
    return n * 100.0


def fmt_money(x: float) -> str:
    return f"${x:,.2f}"


def load_data(days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    bq = create_bigquery_client_from_env()
    q_campaigns = f"""
    SELECT date, campaign_name, campaign_status, impressions, clicks, cost, conversions, ctr, average_cpc_dollars AS cpc, conversion_rate
    FROM `{bq.project_id}.{bq.dataset_id}.campaigns_performance`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    """
    q_keywords = f"""
    SELECT date, campaign_id, keyword_text, match_type, impressions, clicks, cost, conversions, ctr, average_cpc_dollars AS cpc, quality_score
    FROM `{bq.project_id}.{bq.dataset_id}.keywords_performance`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    """
    return bq.query(q_campaigns), bq.query(q_keywords)


def analyze(cdf: pd.DataFrame, kdf: pd.DataFrame, focus_campaign: Optional[str] = None) -> str:
    out: list[str] = []
    if cdf.empty:
        return "No campaign data found for the period. Run the ETL sync first."

    if focus_campaign:
        cdf = cdf[cdf["campaign_name"] == focus_campaign]
        kdf = kdf[kdf["campaign_id"].isin(cdf["campaign_name"].unique())]

    # Aggregate
    totals = cdf.aggregate({
        "impressions": "sum", "clicks": "sum", "cost": "sum", "conversions": "sum"
    })
    tot_impr, tot_clicks, tot_cost, tot_conv = [totals.get(k, 0) for k in ["impressions","clicks","cost","conversions"]]
    ctr = (tot_clicks / tot_impr) if tot_impr else 0
    cpc = (tot_cost / tot_clicks) if tot_clicks else 0
    cvr = (tot_conv / tot_clicks) if tot_clicks else 0
    cpa = (tot_cost / tot_conv) if tot_conv else math.inf

    out.append("Account summary (last period):")
    out.append(f"  Spend: {fmt_money(tot_cost)} | Clicks: {int(tot_clicks):,} | Conv: {tot_conv:.1f} | CTR: {pct(ctr):.2f}% | CPC: {fmt_money(cpc)} | CVR: {pct(cvr):.2f}% | CPA: {fmt_money(cpa) if math.isfinite(cpa) else '∞'}")

    # Campaign hotspots
    camp = cdf.groupby("campaign_name", as_index=False).agg({
        "impressions":"sum","clicks":"sum","cost":"sum","conversions":"sum","ctr":"mean","cpc":"mean","conversion_rate":"mean"
    })
    if not camp.empty:
        # Underperformers by high spend but low CVR
        high_spend = camp.sort_values("cost", ascending=False).head(10)
        under = high_spend[high_spend["conversion_rate"] < (camp["conversion_rate"].median() or 0)]
        for _, r in under.iterrows():
            out.append(f"  Review '{r.campaign_name}': high spend {fmt_money(r.cost)} with low CVR {r.conversion_rate:.2f}% and CTR {r.ctr:.2f}% → tighten targeting, improve RSA ad copy, and mine negatives.")

        # Winners: consider scaling budgets
        winners = camp[(camp["conversion_rate"] > camp["conversion_rate"].quantile(0.75)) & (camp["cost"] > camp["cost"].median())]
        for _, r in winners.iterrows():
            out.append(f"  Scale '{r.campaign_name}': strong CVR {r.conversion_rate:.2f}% at CPC {r.cpc:.2f} → consider budget increases or tROAS/tCPA tuning.")

    # Keyword insights
    if not kdf.empty:
        keys = kdf.groupby(["keyword_text","match_type"], as_index=False).agg({
            "impressions":"sum","clicks":"sum","cost":"sum","conversions":"sum","ctr":"mean","cpc":"mean","quality_score":"mean"
        })
        # Low CTR with impressions: ad copy or relevance issue
        low_ctr = keys[(keys["impressions"] > 500) & (keys["ctr"] < 0.02)].sort_values("impressions", ascending=False).head(10)
        for _, r in low_ctr.iterrows():
            out.append(f"  Low CTR keyword '{r.keyword_text}' ({r.match_type}): CTR {r.ctr:.2f}% on {int(r.impressions):,} impr → refine ads/LP or narrow match.")
        # High spend, zero conversions: candidates for negatives/pauses
        zero_conv = keys[(keys["cost"] > 50) & (keys["conversions"] < 1)].sort_values("cost", ascending=False).head(10)
        for _, r in zero_conv.iterrows():
            out.append(f"  Waste spend '{r.keyword_text}': {fmt_money(r.cost)} with 0 conv → add test negatives and tighten match/geos/devices.")
        # Quality Score improvements
        low_qs = keys[(keys["quality_score"] > 0) & (keys["quality_score"] <= 5)].sort_values("impressions", ascending=False).head(10)
        for _, r in low_qs.iterrows():
            out.append(f"  Low QS '{r.keyword_text}' (QS {r.quality_score:.0f}) → improve ad relevance and LP experience; consider splitting ad groups.")

    return "\n".join(out)


def main() -> None:
    args = parse_args()
    cdf, kdf = load_data(args.days)
    print(analyze(cdf, kdf))


if __name__ == "__main__":
    main()
