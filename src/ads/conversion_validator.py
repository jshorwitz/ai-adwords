"""Conversion validation service comparing Google Ads, GA4, and PostHog data."""

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .ga4_client import create_ga4_client_from_env
from .posthog_client import create_posthog_client_from_env
from .reporting import ReportingManager

logger = logging.getLogger(__name__)


class ConversionValidator:
    """Validates conversion data across Google Ads, GA4, and PostHog."""

    def __init__(self, customer_id: str):
        """Initialize conversion validator.

        Args:
            customer_id: Google Ads customer ID
        """
        self.customer_id = customer_id
        self.google_ads = ReportingManager(customer_id)
        self.ga4_client = create_ga4_client_from_env()
        self.posthog_client = create_posthog_client_from_env()

    def validate_conversions(
        self, start_date: str = None, end_date: str = None
    ) -> dict[str, Any]:
        """Compare conversions across all platforms.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with comparison data and insights
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Validating conversions for {start_date} to {end_date}")

        # Get data from all sources
        google_ads_data = self._get_google_ads_conversions(start_date, end_date)
        ga4_data = self._get_ga4_conversions(start_date, end_date)
        posthog_data = self._get_posthog_conversions(start_date, end_date)

        # Compare the data
        comparison = self._compare_conversion_data(
            google_ads_data, ga4_data, posthog_data
        )

        return {
            "comparison": comparison,
            "google_ads_data": google_ads_data,
            "ga4_data": ga4_data,
            "posthog_data": posthog_data,
            "insights": self._generate_insights(comparison),
            "date_range": {"start": start_date, "end": end_date},
        }

    def _get_google_ads_conversions(
        self, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Get Google Ads conversion data."""
        try:
            df = self.google_ads.get_campaign_performance(start_date, end_date)
            if df.empty:
                return pd.DataFrame()

            # Aggregate by date
            daily_conversions = (
                df.groupby("date")
                .agg(
                    {
                        "conversions": "sum",
                        "conversions_value": "sum",
                        "cost_micros": "sum",
                    }
                )
                .reset_index()
            )

            daily_conversions["cost"] = daily_conversions["cost_micros"] / 1_000_000
            daily_conversions["source"] = "google_ads"

            return daily_conversions[
                ["date", "conversions", "conversions_value", "cost", "source"]
            ]

        except Exception as e:
            logger.error(f"Error fetching Google Ads conversions: {e}")
            return pd.DataFrame()

    def _get_ga4_conversions(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get GA4 conversion data attributed to Google Ads."""
        if not self.ga4_client:
            logger.warning("GA4 client not available")
            return pd.DataFrame()

        try:
            df = self.ga4_client.get_google_ads_conversions(start_date, end_date)
            if df.empty:
                return pd.DataFrame()

            # Aggregate by date
            daily_conversions = (
                df.groupby("date")
                .agg(
                    {
                        "eventCount": "sum",
                        "eventValue": "sum",
                    }
                )
                .reset_index()
            )

            daily_conversions = daily_conversions.rename(
                columns={"eventCount": "conversions", "eventValue": "conversions_value"}
            )
            daily_conversions["source"] = "ga4"
            daily_conversions["cost"] = 0  # GA4 doesn't track cost

            return daily_conversions[
                ["date", "conversions", "conversions_value", "cost", "source"]
            ]

        except Exception as e:
            logger.error(f"Error fetching GA4 conversions: {e}")
            return pd.DataFrame()

    def _get_posthog_conversions(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get PostHog conversion data attributed to Google Ads."""
        if not self.posthog_client:
            logger.warning("PostHog client not available")
            return pd.DataFrame()

        try:
            df = self.posthog_client.get_google_ads_conversions(start_date, end_date)
            if df.empty:
                return pd.DataFrame()

            # Aggregate by date
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            daily_conversions = (
                df.groupby("date")
                .agg(
                    {
                        "event": "count",  # Count of events as conversions
                        "revenue": "sum",
                    }
                )
                .reset_index()
            )

            daily_conversions = daily_conversions.rename(
                columns={"event": "conversions", "revenue": "conversions_value"}
            )
            daily_conversions["conversions_value"] = daily_conversions[
                "conversions_value"
            ].fillna(0)
            daily_conversions["source"] = "posthog"
            daily_conversions["cost"] = 0  # PostHog doesn't track cost

            return daily_conversions[
                ["date", "conversions", "conversions_value", "cost", "source"]
            ]

        except Exception as e:
            logger.error(f"Error fetching PostHog conversions: {e}")
            return pd.DataFrame()

    def _compare_conversion_data(
        self, google_ads: pd.DataFrame, ga4: pd.DataFrame, posthog: pd.DataFrame
    ) -> pd.DataFrame:
        """Compare conversion data across platforms."""
        # Combine all data
        all_data = []

        for df in [google_ads, ga4, posthog]:
            if not df.empty:
                all_data.append(df)

        if not all_data:
            return pd.DataFrame()

        combined = pd.concat(all_data, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"])

        # Create pivot table for comparison
        comparison = combined.pivot_table(
            index="date",
            columns="source",
            values=["conversions", "conversions_value"],
            aggfunc="sum",
            fill_value=0,
        ).round(2)

        # Flatten column names
        comparison.columns = [f"{col[1]}_{col[0]}" for col in comparison.columns]
        comparison = comparison.reset_index()

        # Add totals and variance analysis
        google_ads_conv = comparison.get("google_ads_conversions", pd.Series([0]))
        ga4_conv = comparison.get("ga4_conversions", pd.Series([0]))
        posthog_conv = comparison.get("posthog_conversions", pd.Series([0]))

        if len(google_ads_conv) > 0:
            comparison["ga4_variance"] = (
                (ga4_conv - google_ads_conv) / google_ads_conv * 100
            ).round(2)
            comparison["posthog_variance"] = (
                (posthog_conv - google_ads_conv) / google_ads_conv * 100
            ).round(2)

        return comparison

    def _generate_insights(self, comparison: pd.DataFrame) -> list[str]:
        """Generate insights from conversion comparison."""
        insights = []

        if comparison.empty:
            insights.append("⚠️ No conversion data available for comparison")
            return insights

        # Check data availability
        sources = []
        if "google_ads_conversions" in comparison.columns:
            sources.append("Google Ads")
        if "ga4_conversions" in comparison.columns:
            sources.append("GA4")
        if "posthog_conversions" in comparison.columns:
            sources.append("PostHog")

        insights.append(f"📊 Data available from: {', '.join(sources)}")

        # Calculate totals
        if "google_ads_conversions" in comparison.columns:
            google_ads_total = comparison["google_ads_conversions"].sum()
            insights.append(
                f"🎯 Google Ads reported {google_ads_total:.0f} total conversions"
            )

        if "ga4_conversions" in comparison.columns:
            ga4_total = comparison["ga4_conversions"].sum()
            insights.append(
                f"📈 GA4 attributed {ga4_total:.0f} conversions to Google Ads"
            )

        if "posthog_conversions" in comparison.columns:
            posthog_total = comparison["posthog_conversions"].sum()
            insights.append(
                f"📱 PostHog attributed {posthog_total:.0f} conversions to Google Ads"
            )

        # Variance analysis
        if "ga4_variance" in comparison.columns:
            avg_ga4_variance = comparison["ga4_variance"].mean()
            if abs(avg_ga4_variance) < 10:
                insights.append(
                    f"✅ GA4 data closely matches Google Ads ({avg_ga4_variance:+.1f}% avg variance)"
                )
            elif avg_ga4_variance > 10:
                insights.append(
                    f"⚠️ GA4 showing {avg_ga4_variance:.1f}% higher conversions than Google Ads"
                )
            else:
                insights.append(
                    f"⚠️ GA4 showing {abs(avg_ga4_variance):.1f}% lower conversions than Google Ads"
                )

        if "posthog_variance" in comparison.columns:
            avg_posthog_variance = comparison["posthog_variance"].mean()
            if abs(avg_posthog_variance) < 10:
                insights.append(
                    f"✅ PostHog data closely matches Google Ads ({avg_posthog_variance:+.1f}% avg variance)"
                )
            elif avg_posthog_variance > 10:
                insights.append(
                    f"⚠️ PostHog showing {avg_posthog_variance:.1f}% higher conversions than Google Ads"
                )
            else:
                insights.append(
                    f"⚠️ PostHog showing {abs(avg_posthog_variance):.1f}% lower conversions than Google Ads"
                )

        return insights

    def create_comparison_chart(self, comparison: pd.DataFrame) -> go.Figure:
        """Create interactive comparison chart."""
        if comparison.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=(
                "Conversion Count Comparison",
                "Conversion Value Comparison",
            ),
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        )

        # Conversion count chart
        for col in comparison.columns:
            if col.endswith("_conversions") and col != "date":
                source = col.replace("_conversions", "").replace("_", " ").title()
                fig.add_trace(
                    go.Scatter(
                        x=comparison["date"],
                        y=comparison[col],
                        mode="lines+markers",
                        name=f"{source} Conversions",
                        line={"width": 2},
                    ),
                    row=1,
                    col=1,
                )

        # Conversion value chart
        for col in comparison.columns:
            if col.endswith("_conversions_value") and col != "date":
                source = col.replace("_conversions_value", "").replace("_", " ").title()
                fig.add_trace(
                    go.Scatter(
                        x=comparison["date"],
                        y=comparison[col],
                        mode="lines+markers",
                        name=f"{source} Value",
                        line={"width": 2, "dash": "dash"},
                    ),
                    row=2,
                    col=1,
                )

        fig.update_layout(
            height=600,
            title="Conversion Validation: Multi-Platform Comparison",
            showlegend=True,
            hovermode="x unified",
        )

        return fig


def create_validator_from_env(customer_id: str) -> ConversionValidator:
    """Create conversion validator from environment configuration."""
    return ConversionValidator(customer_id)
