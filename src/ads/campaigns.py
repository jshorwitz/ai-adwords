"""Campaign management - budgets, campaigns, ad groups, criteria, RSAs, negatives."""

from __future__ import annotations

import os
from typing import Any

from src.ads.ads_client import create_client_from_env
from src.ads.data_generator import generate_historical_campaign_data


def list_campaigns(customer_id: str) -> list[dict[str, Any]]:
    """List campaigns for a customer.

    - If ADS_USE_MOCK=1 or ADS_USE_DEMO=1, returns mock/demo campaigns.
    - Otherwise, queries Google Ads API for campaign id, name, and status.
    """
    if os.getenv("ADS_USE_MOCK") == "1" or os.getenv("ADS_USE_DEMO") == "1":
        # Derive unique campaigns from generated demo data
        df = generate_historical_campaign_data(customer_id, days_back=7)
        uniq = df.drop_duplicates(subset=["campaign_id"])  # type: ignore[arg-type]
        return [
            {
                "id": str(r.campaign_id),
                "name": str(r.campaign_name),
                "status": str(r.campaign_status),
            }
            for r in uniq.itertuples(index=False)
        ]

    # Real API path
    service = create_client_from_env()
    client = service.client
    ga_service = client.get_service("GoogleAdsService")

    query = (
        "SELECT campaign.id, campaign.name, campaign.status FROM campaign "
        "WHERE campaign.status != 'REMOVED'"
    )

    rows: list[dict[str, Any]] = []
    try:
        # Prefer streaming, fall back to paged search
        try:
            request = client.get_type("SearchGoogleAdsStreamRequest")
            request.customer_id = customer_id
            request.query = query
            for batch in ga_service.search_stream(request=request):
                for r in batch.results:
                    rows.append(
                        {
                            "id": str(r.campaign.id),
                            "name": str(r.campaign.name),
                            "status": r.campaign.status.name
                            if hasattr(r.campaign.status, "name")
                            else str(r.campaign.status),
                        }
                    )
        except Exception:
            for r in ga_service.search(customer_id=customer_id, query=query):
                rows.append(
                    {
                        "id": str(r.campaign.id),
                        "name": str(r.campaign.name),
                        "status": r.campaign.status.name
                        if hasattr(r.campaign.status, "name")
                        else str(r.campaign.status),
                    }
                )
    except Exception:
        # Return an empty list on failure
        return []

    return rows


class CampaignManager:
    """Manages Google Ads campaigns, ad groups, and related entities."""

    def create_campaign(self) -> None:
        """Create a new campaign."""
        pass

    def create_ad_group(self) -> None:
        """Create a new ad group."""
        pass

    def create_responsive_search_ad(self) -> None:
        """Create a responsive search ad (RSA)."""
        pass

    def add_keywords(self) -> None:
        """Add keywords to an ad group."""
        pass

    def add_negative_keywords(self) -> None:
        """Add negative keywords."""
        pass
