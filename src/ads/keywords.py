"""Keyword listing and basic metrics retrieval.

Provides a simple list of keywords with impressions/clicks/cost metrics
for either mock/demo mode or real Google Ads API.
"""

from __future__ import annotations

import os
from typing import Any, List

from src.ads.ads_client import create_client_from_env
from src.ads.data_generator import generate_historical_keyword_data


def list_keywords(customer_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """List top keywords by impressions.

    - If ADS_USE_MOCK=1 or ADS_USE_DEMO=1, uses generated demo data.
    - Otherwise queries keyword_view via GAQL.
    """
    if os.getenv("ADS_USE_MOCK") == "1" or os.getenv("ADS_USE_DEMO") == "1":
        df = generate_historical_keyword_data(customer_id, days_back=7)
        if df.empty:
            return []
        # aggregate last 7 days by keyword and sort by impressions
        agg = (
            df.groupby(["keyword_text", "match_type", "campaign_id", "ad_group_id"], as_index=False)
            .agg({
                "impressions": "sum",
                "clicks": "sum",
                "cost": "sum",
                "conversions": "sum",
                "average_cpc_dollars": "mean",
            })
            .sort_values("impressions", ascending=False)
            .head(limit)
        )
        results: list[dict[str, Any]] = []
        for r in agg.itertuples(index=False):
            results.append({
                "keyword": str(r.keyword_text),
                "match_type": str(r.match_type),
                "campaign_id": str(r.campaign_id),
                "ad_group_id": str(r.ad_group_id),
                "impressions": int(r.impressions),
                "clicks": int(r.clicks),
                "cost": float(r.cost),
                "conversions": float(r.conversions),
                "avg_cpc": round(float(r.average_cpc_dollars), 2),
            })
        return results

    # Real API path
    service = create_client_from_env()
    client = service.client
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT 
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            campaign.id,
            ad_group.id,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.average_cpc
        FROM keyword_view
        WHERE ad_group_criterion.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.impressions DESC
        LIMIT {int(limit)}
    """

    rows: list[dict[str, Any]] = []
    try:
        try:
            request = client.get_type("SearchGoogleAdsStreamRequest")
            request.customer_id = customer_id
            request.query = query
            for batch in ga_service.search_stream(request=request):
                for r in batch.results:
                    rows.append(_row_to_keyword_dict(r))
        except Exception:
            for r in ga_service.search(customer_id=customer_id, query=query):
                rows.append(_row_to_keyword_dict(r))
    except Exception:
        return []

    return rows


def _row_to_keyword_dict(r: Any) -> dict[str, Any]:
    micros = int(getattr(r.metrics, "average_cpc", 0) or 0)
    avg_cpc_dollars = round(micros / 1_000_000.0, 2)
    return {
        "keyword": str(r.ad_group_criterion.keyword.text),
        "match_type": r.ad_group_criterion.keyword.match_type.name if hasattr(r.ad_group_criterion.keyword.match_type, "name") else str(r.ad_group_criterion.keyword.match_type),
        "campaign_id": str(r.campaign.id),
        "ad_group_id": str(r.ad_group.id),
        "impressions": int(r.metrics.impressions),
        "clicks": int(r.metrics.clicks),
        "cost_micros": int(r.metrics.cost_micros),
        "avg_cpc": avg_cpc_dollars,
    }
