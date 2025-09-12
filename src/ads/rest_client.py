"""Direct REST API client for Google Ads when GRPC fails."""

import logging
import os
from typing import Any

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class GoogleAdsRestClient:
    """Direct REST API client for Google Ads API."""

    BASE_URL = "https://googleads.googleapis.com/v17"

    def __init__(
        self,
        developer_token: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        login_customer_id: str | None = None,
    ):
        """Initialize REST client."""
        self.developer_token = developer_token
        self.login_customer_id = login_customer_id

        # Create OAuth credentials
        self.credentials = Credentials(
            token=None,  # Will be refreshed
            refresh_token=refresh_token,
            id_token=None,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/adwords"],
        )

        # Refresh access token
        self.credentials.refresh(Request())

    def _make_request(
        self,
        method: str,
        endpoint: str,
        customer_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated REST API request."""
        url = f"{self.BASE_URL}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json",
        }

        if customer_id:
            headers["login-customer-id"] = str(customer_id)
        elif self.login_customer_id:
            headers["login-customer-id"] = str(self.login_customer_id)

        logger.info(f"REST API call: {method} {url}")

        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)

        response.raise_for_status()
        return response.json()

    def list_accessible_customers(self) -> list[str]:
        """Get list of accessible customer accounts."""
        try:
            result = self._make_request("GET", "customers:listAccessibleCustomers")
            return [
                resource.replace("customers/", "")
                for resource in result.get("resourceNames", [])
            ]
        except Exception as e:
            logger.error(f"Failed to list customers: {e}")
            return []

    def get_customer_info(self, customer_id: str) -> dict[str, Any]:
        """Get basic customer information."""
        try:
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.status
                FROM customer
                LIMIT 1
            """

            data = {"query": query, "page_size": 1}

            result = self._make_request(
                "POST",
                f"customers/{customer_id}/googleAds:search",
                customer_id=customer_id,
                data=data,
            )

            if result.get("results"):
                return result["results"][0]
            return {}

        except Exception as e:
            logger.error(f"Failed to get customer info for {customer_id}: {e}")
            return {}

    def get_campaigns(self, customer_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get campaign data for customer."""
        try:
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type,
                    campaign_budget.amount_micros,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc
                FROM campaign
                WHERE segments.date DURING LAST_30_DAYS
                ORDER BY metrics.impressions DESC
                LIMIT {limit}
            """

            data = {"query": query, "page_size": limit}

            result = self._make_request(
                "POST",
                f"customers/{customer_id}/googleAds:search",
                customer_id=customer_id,
                data=data,
            )

            return result.get("results", [])

        except Exception as e:
            logger.error(f"Failed to get campaigns for {customer_id}: {e}")
            return []


def create_rest_client_from_env() -> GoogleAdsRestClient | None:
    """Create REST client from environment variables."""
    try:
        return GoogleAdsRestClient(
            developer_token=os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
            refresh_token=os.getenv("GOOGLE_ADS_REFRESH_TOKEN", ""),
            client_id=os.getenv("GOOGLE_ADS_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_ADS_CLIENT_SECRET", ""),
            login_customer_id=os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        )
    except Exception as e:
        logger.error(f"Failed to create REST client: {e}")
        return None
