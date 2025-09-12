"""PostHog API client for conversion validation."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests
from posthog import Posthog

logger = logging.getLogger(__name__)


class PostHogClient:
    """PostHog API client for conversion data."""

    def __init__(self, api_key: str, host: str = "https://app.posthog.com"):
        """Initialize PostHog client.

        Args:
            api_key: PostHog API key
            host: PostHog instance host (default: app.posthog.com)
        """
        self.api_key = api_key
        self.host = host.rstrip("/")
        self.posthog = Posthog(api_key, host=host)

    def get_conversion_events(
        self,
        start_date: str = None,
        end_date: str = None,
        event_names: list[str] = None,
    ) -> pd.DataFrame:
        """Get conversion events from PostHog.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            event_names: List of event names to filter for

        Returns:
            DataFrame with conversion events
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        if not event_names:
            event_names = [
                "sign_up",
                "purchase",
                "demo_request",
                "form_submit",
                "$pageview",
            ]

        # Use PostHog's query API
        query = {
            "kind": "EventsQuery",
            "select": [
                "event",
                "timestamp",
                "person_id",
                "properties.$current_url",
                "properties.utm_source",
                "properties.utm_medium",
                "properties.utm_campaign",
                "properties.gclid",
                "properties.$revenue",
            ],
            "where": [
                f"timestamp >= '{start_date}T00:00:00Z'",
                f"timestamp <= '{end_date}T23:59:59Z'",
                f"event IN {tuple(event_names) if len(event_names) > 1 else '(' + repr(event_names[0]) + ')'}",
            ],
        }

        try:
            response = self._query_events(query)
            return self._parse_events_response(response)
        except Exception as e:
            logger.error(f"Error fetching PostHog events: {e}")
            return pd.DataFrame()

    def get_google_ads_conversions(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get conversions attributed to Google Ads in PostHog.

        This looks for events with utm_source=google and utm_medium=cpc
        or events with gclid parameter.
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = {
            "kind": "EventsQuery",
            "select": [
                "event",
                "timestamp",
                "person_id",
                "properties.utm_source",
                "properties.utm_medium",
                "properties.utm_campaign",
                "properties.gclid",
                "properties.$revenue",
            ],
            "where": [
                f"timestamp >= '{start_date}T00:00:00Z'",
                f"timestamp <= '{end_date}T23:59:59Z'",
                # Look for Google Ads traffic
                "((properties.utm_source = 'google' AND properties.utm_medium IN ('cpc', 'ppc')) OR properties.gclid IS NOT NULL)",
            ],
        }

        try:
            response = self._query_events(query)
            df = self._parse_events_response(response)
            if not df.empty:
                df["source"] = "google_ads"
                # Mark events with gclid as definitely from Google Ads
                if "gclid" in df.columns:
                    df.loc[df["gclid"].notna(), "source"] = "google_ads_gclid"
            return df
        except Exception as e:
            logger.error(f"Error fetching PostHog Google Ads data: {e}")
            return pd.DataFrame()

    def get_conversion_funnel(
        self, steps: list[str], start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get conversion funnel data from PostHog.

        Args:
            steps: List of event names representing funnel steps
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = {
            "kind": "FunnelsQuery",
            "series": [{"event": step} for step in steps],
            "dateRange": {"date_from": start_date, "date_to": end_date},
            "funnelWindowInterval": 30,
            "funnelWindowIntervalUnit": "day",
        }

        try:
            response = self._query_insights(query)
            return self._parse_funnel_response(response)
        except Exception as e:
            logger.error(f"Error fetching PostHog funnel: {e}")
            return pd.DataFrame()

    def _query_events(self, query: dict[str, Any]) -> dict[str, Any]:
        """Execute events query against PostHog API."""
        url = f"{self.host}/api/projects/@current/query"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json={"query": query}, headers=headers)
        response.raise_for_status()
        return response.json()

    def _query_insights(self, query: dict[str, Any]) -> dict[str, Any]:
        """Execute insights query against PostHog API."""
        url = f"{self.host}/api/projects/@current/insights"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=query, headers=headers)
        response.raise_for_status()
        return response.json()

    def _parse_events_response(self, response: dict[str, Any]) -> pd.DataFrame:
        """Parse PostHog events response into DataFrame."""
        if "results" not in response:
            return pd.DataFrame()

        events = response["results"]
        if not events:
            return pd.DataFrame()

        # Flatten the events data
        data = []
        for event in events:
            row = {
                "event": event.get("event"),
                "timestamp": event.get("timestamp"),
                "person_id": event.get("person_id"),
            }

            # Add properties
            if "properties" in event:
                props = event["properties"]
                row.update(
                    {
                        "utm_source": props.get("utm_source"),
                        "utm_medium": props.get("utm_medium"),
                        "utm_campaign": props.get("utm_campaign"),
                        "gclid": props.get("gclid"),
                        "revenue": props.get("$revenue"),
                        "current_url": props.get("$current_url"),
                    }
                )

            data.append(row)

        df = pd.DataFrame(data)
        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["date"] = df["timestamp"].dt.date

        return df

    def _parse_funnel_response(self, response: dict[str, Any]) -> pd.DataFrame:
        """Parse PostHog funnel response into DataFrame."""
        if "result" not in response:
            return pd.DataFrame()

        funnel_data = response["result"]
        return pd.DataFrame(funnel_data)


def create_posthog_client_from_env() -> PostHogClient | None:
    """Create PostHog client from environment variables."""
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("POSTHOG_API_KEY")
    host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")

    if not api_key:
        logger.warning("POSTHOG_API_KEY not found in environment")
        return None

    try:
        return PostHogClient(api_key, host)
    except Exception as e:
        logger.error(f"Failed to create PostHog client: {e}")
        return None
