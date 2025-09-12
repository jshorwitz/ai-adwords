"""Google Analytics 4 API client for conversion validation."""

import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class GA4Client:
    """Google Analytics 4 API client for conversion data."""

    def __init__(self, property_id: str, credentials_path: str = None):
        """Initialize GA4 client.

        Args:
            property_id: GA4 property ID (numeric, e.g., "123456789")
            credentials_path: Path to service account JSON file
        """
        self.property_id = property_id
        self.credentials_path = credentials_path
        self._client = None

    @property
    def client(self) -> BetaAnalyticsDataClient:
        """Lazy-loaded GA4 client."""
        if self._client is None:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = Credentials.from_service_account_file(
                    self.credentials_path
                )
                self._client = BetaAnalyticsDataClient(credentials=credentials)
            else:
                # Try default credentials
                try:
                    self._client = BetaAnalyticsDataClient()
                except DefaultCredentialsError:
                    logger.error("No valid GA4 credentials found")
                    raise
        return self._client

    def get_conversion_data(
        self,
        start_date: str = None,
        end_date: str = None,
        conversion_events: list[str] = None,
    ) -> pd.DataFrame:
        """Get conversion data from GA4.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            conversion_events: List of conversion event names

        Returns:
            DataFrame with conversion data
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        if not conversion_events:
            conversion_events = [
                "purchase",
                "generate_lead",
                "sign_up",
                "form_submit",
                "demo_request",
            ]

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="eventName"),
                Dimension(name="source"),
                Dimension(name="medium"),
                Dimension(name="campaign"),
            ],
            metrics=[
                Metric(name="eventCount"),
                Metric(name="eventValue"),
                Metric(name="totalUsers"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            # Filter for conversion events
            dimension_filter={
                "filter": {
                    "field_name": "eventName",
                    "in_list_filter": {"values": conversion_events},
                }
            },
        )

        try:
            response = self.client.run_report(request)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error fetching GA4 data: {e}")
            return pd.DataFrame()

    def get_google_ads_conversions(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get conversions attributed to Google Ads in GA4.

        This specifically looks for traffic/conversions from Google Ads
        based on utm_source=google and utm_medium=cpc/ppc.
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="eventName"),
                Dimension(name="campaign"),
                Dimension(name="adGroup"),
                Dimension(name="keyword"),
            ],
            metrics=[
                Metric(name="eventCount"),
                Metric(name="eventValue"),
                Metric(name="conversions"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            # Filter for Google Ads traffic
            dimension_filter={
                "and_group": {
                    "expressions": [
                        {
                            "filter": {
                                "field_name": "source",
                                "string_filter": {"value": "google"},
                            }
                        },
                        {
                            "filter": {
                                "field_name": "medium",
                                "in_list_filter": {"values": ["cpc", "ppc"]},
                            }
                        },
                    ]
                }
            },
        )

        try:
            response = self.client.run_report(request)
            df = self._parse_response(response)
            if not df.empty:
                df["source"] = "google_ads"
            return df
        except Exception as e:
            logger.error(f"Error fetching GA4 Google Ads data: {e}")
            return pd.DataFrame()

    def _parse_response(self, response) -> pd.DataFrame:
        """Parse GA4 API response into DataFrame."""
        data = []

        for row in response.rows:
            row_data = {}

            # Add dimensions
            for i, dimension_header in enumerate(response.dimension_headers):
                row_data[dimension_header.name] = row.dimension_values[i].value

            # Add metrics
            for i, metric_header in enumerate(response.metric_headers):
                value = row.metric_values[i].value
                # Convert to numeric if possible
                try:
                    row_data[metric_header.name] = float(value)
                except ValueError:
                    row_data[metric_header.name] = value

            data.append(row_data)

        return pd.DataFrame(data)


def create_ga4_client_from_env() -> GA4Client | None:
    """Create GA4 client from environment variables."""
    from dotenv import load_dotenv

    load_dotenv()

    property_id = os.getenv("GA4_PROPERTY_ID")
    credentials_path = os.getenv("GA4_CREDENTIALS_PATH")

    if not property_id:
        logger.warning("GA4_PROPERTY_ID not found in environment")
        return None

    try:
        return GA4Client(property_id, credentials_path)
    except Exception as e:
        logger.error(f"Failed to create GA4 client: {e}")
        return None
