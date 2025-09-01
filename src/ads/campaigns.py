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


def create_campaign(
    customer_id: str,
    name: str,
    daily_budget_micros: int,
    channel: str = "SEARCH",
    bidding_strategy: str = "MAXIMIZE_CONVERSIONS",
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = True,
) -> dict[str, str | int | bool]:
    """Create a campaign or perform a dry-run validation.

    - In mock mode (ADS_USE_MOCK=1) always returns a simulated success.
    - In real mode, creates a CampaignBudget then a Campaign. When dry_run=True,
      calls the API with validate_only=True so nothing is changed.

    Returns a dict with keys: status, budget_resource_name, campaign_resource_name.
    """
    import os
    from datetime import datetime

    if os.getenv("ADS_USE_MOCK") == "1":
        return {
            "status": "VALIDATION_PASSED",
            "budget_resource_name": f"customers/{customer_id}/campaignBudgets/9999999999",
            "campaign_resource_name": f"customers/{customer_id}/campaigns/8888888888",
            "dry_run": True,
        }

    # Real API path
    service = create_client_from_env()
    client = service.client

    # 1) Create budget
    budget_svc = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create
    budget.name = f"{name} Budget {datetime.now().strftime('%Y%m%d-%H%M%S')}"
    budget.amount_micros = int(daily_budget_micros)
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    budget.explicitly_shared = False

    budget_resp = budget_svc.mutate_campaign_budgets(
        customer_id=customer_id,
        operations=[budget_op],
        partial_failure=True,
        validate_only=dry_run,
    )

    budget_rn = (
        budget_resp.results[0].resource_name if not dry_run else f"customers/{customer_id}/campaignBudgets/placeholder"
    )

    # 2) Create campaign
    campaign_svc = client.get_service("CampaignService")
    camp_op = client.get_type("CampaignOperation")
    camp = camp_op.create
    camp.name = name
    camp.status = client.enums.CampaignStatusEnum.PAUSED
    camp.advertising_channel_type = getattr(
        client.enums.AdvertisingChannelTypeEnum, channel, client.enums.AdvertisingChannelTypeEnum.SEARCH
    )
    camp.campaign_budget = budget_rn

    # Bidding strategy
    if bidding_strategy.upper() == "MAXIMIZE_CONVERSIONS":
        camp.maximize_conversions.CopyFrom(client.get_type("MaximizeConversions"))
    elif bidding_strategy.upper() == "MAXIMIZE_CONVERSION_VALUE":
        camp.maximize_conversion_value.CopyFrom(client.get_type("MaximizeConversionValue"))
    elif bidding_strategy.upper() == "MANUAL_CPC":
        camp.manual_cpc.CopyFrom(client.get_type("ManualCpc"))

    # Dates (YYYY-MM-DD)
    if start_date:
        camp.start_date = start_date
    if end_date:
        camp.end_date = end_date

    # Simple network settings for SEARCH
    if channel.upper() == "SEARCH":
        camp.network_settings.target_google_search = True
        camp.network_settings.target_search_network = True
        camp.network_settings.target_partner_search_network = False

    camp_resp = campaign_svc.mutate_campaigns(
        customer_id=customer_id,
        operations=[camp_op],
        partial_failure=True,
        validate_only=dry_run,
    )

    camp_rn = (
        camp_resp.results[0].resource_name if not dry_run else f"customers/{customer_id}/campaigns/placeholder"
    )

    return {
        "status": "VALIDATION_PASSED" if dry_run else "CREATED",
        "budget_resource_name": budget_rn,
        "campaign_resource_name": camp_rn,
        "dry_run": dry_run,
    }

