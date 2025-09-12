"""GAQL SearchStream exporters for reporting."""

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from google.ads.googleads.errors import GoogleAdsException  # type: ignore

from ads.ads_client import create_client_from_env

logger = logging.getLogger(__name__)


class ReportingManager:
    """Manages Google Ads reporting using GAQL SearchStream."""

    def __init__(self, customer_id: str):
        """Initialize with customer ID."""
        self.customer_id = customer_id
        self.service = create_client_from_env()
        self.client = self.service.client

    def get_campaign_performance(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get campaign performance data."""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = f"""
            SELECT
                segments.date,
                customer.id,
                customer.descriptive_name,
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND campaign.status = 'ENABLED'
        """

        return self._execute_query(query, "campaign_performance")

    def get_keyword_performance(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get keyword performance data."""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        query = f"""
            SELECT
                segments.date,
                customer.id,
                campaign.id,
                ad_group.id,
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.quality_info.quality_score,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM keyword_view
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND ad_group_criterion.status = 'ENABLED'
            AND ad_group.status = 'ENABLED'
            AND campaign.status = 'ENABLED'
        """

        return self._execute_query(query, "keyword_performance")

    def _execute_query(self, query: str, report_name: str) -> pd.DataFrame:
        """Execute GAQL query against Google Ads and return DataFrame.

        Falls back to demo data only if explicitly requested via env (ADS_USE_DEMO=1).
        """
        import os

        use_demo = os.getenv("ADS_USE_DEMO") == "1"
        if use_demo:
            logger.warning("ADS_USE_DEMO=1 set; returning generated demo data")
            from ads.data_generator import (
                generate_historical_campaign_data,
                generate_historical_keyword_data,
            )

            if report_name == "campaign_performance":
                return generate_historical_campaign_data(self.customer_id, days_back=90)
            if report_name == "keyword_performance":
                return generate_historical_keyword_data(self.customer_id, days_back=90)
            return pd.DataFrame()

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            def _row_to_dict(r):
                if report_name == "campaign_performance":
                    return {
                        "date": str(r.segments.date),
                        "customer_id": str(r.customer.id),
                        "customer_name": str(r.customer.descriptive_name),
                        "campaign_id": str(r.campaign.id),
                        "campaign_name": str(r.campaign.name),
                        "campaign_status": r.campaign.status.name
                        if hasattr(r.campaign.status, "name")
                        else str(r.campaign.status),
                        "impressions": int(r.metrics.impressions),
                        "clicks": int(r.metrics.clicks),
                        "cost_micros": int(r.metrics.cost_micros),
                        "conversions": float(r.metrics.conversions),
                        "ctr": float(r.metrics.ctr),
                        "average_cpc": int(r.metrics.average_cpc),
                        "cost_per_conversion": float(r.metrics.cost_per_conversion)
                        if hasattr(r.metrics, "cost_per_conversion")
                        else None,
                        "conversions_value": float(r.metrics.conversions_value)
                        if hasattr(r.metrics, "conversions_value")
                        else None,
                    }
                elif report_name == "keyword_performance":
                    return {
                        "date": str(r.segments.date),
                        "customer_id": str(r.customer.id),
                        "campaign_id": str(r.campaign.id),
                        "ad_group_id": str(r.ad_group.id),
                        "criterion_id": str(r.ad_group_criterion.criterion_id),
                        "keyword_text": str(r.ad_group_criterion.keyword.text),
                        "match_type": r.ad_group_criterion.keyword.match_type.name
                        if hasattr(r.ad_group_criterion.keyword.match_type, "name")
                        else str(r.ad_group_criterion.keyword.match_type),
                        "quality_score": int(
                            getattr(
                                r.ad_group_criterion.quality_info, "quality_score", 0
                            )
                            or 0
                        ),
                        "impressions": int(r.metrics.impressions),
                        "clicks": int(r.metrics.clicks),
                        "cost_micros": int(r.metrics.cost_micros),
                        "conversions": float(r.metrics.conversions),
                        "ctr": float(r.metrics.ctr),
                        "average_cpc": int(r.metrics.average_cpc),
                    }
                else:
                    return {"raw": r}

            rows: list[dict[str, Any]] = []

            # Try streaming first (gRPC). If unavailable, fall back to paged REST search.
            try:
                request = self.client.get_type("SearchGoogleAdsStreamRequest")
                request.customer_id = self.customer_id
                request.query = query
                for batch in ga_service.search_stream(request=request):
                    for r in batch.results:
                        rows.append(_row_to_dict(r))
            except Exception as stream_err:
                logger.warning(
                    f"search_stream unavailable ({stream_err}); falling back to search"
                )
                for r in ga_service.search(customer_id=self.customer_id, query=query):
                    rows.append(_row_to_dict(r))

            return pd.DataFrame(rows)

        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            for err in ex.failure.errors:
                logger.error(f"  - {err.error_code}: {err.message}")
            return pd.DataFrame()
        except Exception as ex:
            logger.error(f"Failed to execute query for {report_name}: {ex}")
            return pd.DataFrame()

    def export_campaign_performance(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Export campaign performance report."""
        return self.get_campaign_performance(start_date, end_date)

    def export_keyword_performance(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Export keyword performance report."""
        return self.get_keyword_performance(start_date, end_date)

    def export_search_terms(self) -> pd.DataFrame:
        """Export search terms report."""
        # TODO: Implement search terms query
        return pd.DataFrame()

    def stream_report(self, query: str) -> pd.DataFrame:
        """Stream a custom GAQL report."""
        return self._execute_query(query, "custom_report")
