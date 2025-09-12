"""Generate realistic Google Ads historical data for demo purposes."""

import random
from datetime import datetime, timedelta

import pandas as pd


def generate_historical_campaign_data(
    customer_id: str, days_back: int = 365
) -> pd.DataFrame:
    """Generate realistic historical campaign performance data."""

    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    # Define multiple campaigns with different characteristics
    campaigns = [
        {
            "id": "123456789",
            "name": "Brand Campaign",
            "base_impressions": 5000,
            "base_ctr": 0.08,
            "seasonality": 0.1,
        },
        {
            "id": "234567890",
            "name": "Search Campaign",
            "base_impressions": 8000,
            "base_ctr": 0.05,
            "seasonality": 0.15,
        },
        {
            "id": "345678901",
            "name": "Display Campaign",
            "base_impressions": 12000,
            "base_ctr": 0.02,
            "seasonality": 0.2,
        },
        {
            "id": "456789012",
            "name": "Shopping Campaign",
            "base_impressions": 3000,
            "base_ctr": 0.12,
            "seasonality": 0.25,
        },
        {
            "id": "567890123",
            "name": "Video Campaign",
            "base_impressions": 15000,
            "base_ctr": 0.03,
            "seasonality": 0.1,
        },
    ]

    all_data = []

    for date in date_range:
        # Add day-of-week and seasonal effects
        day_of_week_multiplier = 1.0
        if date.weekday() in [5, 6]:  # Weekend
            day_of_week_multiplier = 0.8
        elif date.weekday() in [1, 2, 3]:  # Tue-Thu
            day_of_week_multiplier = 1.1

        # Holiday/seasonal effects
        month = date.month
        seasonal_multiplier = 1.0
        if month in [11, 12]:  # Holiday season
            seasonal_multiplier = 1.4
        elif month in [1, 2]:  # Post-holiday
            seasonal_multiplier = 0.7
        elif month in [6, 7, 8]:  # Summer
            seasonal_multiplier = 1.2

        for campaign in campaigns:
            # Add random variation
            random_variation = random.uniform(0.8, 1.2)

            # Calculate impressions with trends and seasonality
            base_impressions = campaign["base_impressions"]
            impressions = int(
                base_impressions
                * day_of_week_multiplier
                * seasonal_multiplier
                * random_variation
            )

            # Calculate CTR with some variation
            base_ctr = campaign["base_ctr"]
            ctr_variation = random.uniform(0.9, 1.1)
            ctr = base_ctr * ctr_variation

            # Calculate clicks
            clicks = int(impressions * ctr)

            # Calculate cost (varies by campaign type and competition)
            base_cpc = random.uniform(1.5, 8.0)  # $1.50 to $8.00 CPC
            cost = clicks * base_cpc
            cost_micros = int(cost * 1_000_000)

            # Calculate conversions (varies by campaign effectiveness)
            conversion_rate = random.uniform(0.02, 0.15)  # 2% to 15%
            conversions = clicks * conversion_rate

            # Calculate additional metrics
            cost_per_conversion = cost / conversions if conversions > 0 else 0
            average_cpc = cost / clicks if clicks > 0 else 0

            row = {
                "date": date.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "customer_name": "Demo Account",
                "campaign_id": campaign["id"],
                "campaign_name": campaign["name"],
                "campaign_status": "ENABLED",
                "impressions": impressions,
                "clicks": clicks,
                "cost_micros": cost_micros,
                "cost": cost,
                "conversions": round(conversions, 2),
                "ctr": round(ctr, 4),
                "average_cpc": int(average_cpc * 1_000_000),  # in micros
                "average_cpc_dollars": round(average_cpc, 2),
                "cost_per_conversion": round(cost_per_conversion, 2),
                "conversion_rate": round(conversion_rate, 4),
                "updated_at": datetime.now(),
            }

            all_data.append(row)

    return pd.DataFrame(all_data)


def generate_historical_keyword_data(
    customer_id: str, days_back: int = 365
) -> pd.DataFrame:
    """Generate realistic historical keyword performance data."""

    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    # Define keywords for different campaigns
    keywords = [
        # Brand keywords
        {
            "text": "your brand name",
            "campaign_id": "123456789",
            "ad_group_id": "111111111",
            "match_type": "EXACT",
            "quality_score": 9,
            "base_impressions": 500,
        },
        {
            "text": "your company",
            "campaign_id": "123456789",
            "ad_group_id": "111111111",
            "match_type": "PHRASE",
            "quality_score": 8,
            "base_impressions": 300,
        },
        # Search keywords
        {
            "text": "best software solution",
            "campaign_id": "234567890",
            "ad_group_id": "222222222",
            "match_type": "BROAD",
            "quality_score": 6,
            "base_impressions": 800,
        },
        {
            "text": "enterprise software",
            "campaign_id": "234567890",
            "ad_group_id": "222222222",
            "match_type": "PHRASE",
            "quality_score": 7,
            "base_impressions": 600,
        },
        {
            "text": "business automation",
            "campaign_id": "234567890",
            "ad_group_id": "333333333",
            "match_type": "BROAD",
            "quality_score": 5,
            "base_impressions": 400,
        },
        # Shopping keywords
        {
            "text": "buy software online",
            "campaign_id": "456789012",
            "ad_group_id": "444444444",
            "match_type": "PHRASE",
            "quality_score": 8,
            "base_impressions": 200,
        },
        {
            "text": "software deals",
            "campaign_id": "456789012",
            "ad_group_id": "444444444",
            "match_type": "BROAD",
            "quality_score": 6,
            "base_impressions": 350,
        },
    ]

    all_data = []

    for date in date_range:
        # Add day-of-week effects
        day_of_week_multiplier = 1.0
        if date.weekday() in [5, 6]:  # Weekend
            day_of_week_multiplier = 0.7
        elif date.weekday() in [1, 2, 3]:  # Tue-Thu
            day_of_week_multiplier = 1.1

        for i, keyword in enumerate(keywords):
            # Add random variation
            random_variation = random.uniform(0.7, 1.3)

            # Calculate impressions
            impressions = int(
                keyword["base_impressions"] * day_of_week_multiplier * random_variation
            )

            # Calculate CTR based on match type and quality score
            base_ctr = 0.02 + (keyword["quality_score"] / 100)  # Higher QS = higher CTR
            if keyword["match_type"] == "EXACT":
                base_ctr *= 1.5
            elif keyword["match_type"] == "PHRASE":
                base_ctr *= 1.2

            ctr = base_ctr * random.uniform(0.8, 1.2)
            clicks = int(impressions * ctr)

            # Calculate cost
            base_cpc = random.uniform(2.0, 12.0)
            # Brand keywords typically cheaper
            if keyword["campaign_id"] == "123456789":
                base_cpc *= 0.6

            cost = clicks * base_cpc
            cost_micros = int(cost * 1_000_000)

            # Calculate conversions
            conversion_rate = random.uniform(0.01, 0.2)
            conversions = clicks * conversion_rate

            row = {
                "date": date.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "campaign_id": keyword["campaign_id"],
                "ad_group_id": keyword["ad_group_id"],
                "criterion_id": f"{1000000 + i}",
                "keyword_text": keyword["text"],
                "match_type": keyword["match_type"],
                "quality_score": keyword["quality_score"],
                "impressions": impressions,
                "clicks": clicks,
                "cost_micros": cost_micros,
                "cost": cost,
                "conversions": round(conversions, 2),
                "ctr": round(ctr, 4),
                "average_cpc": int(base_cpc * 1_000_000),
                "average_cpc_dollars": round(base_cpc, 2),
                "updated_at": datetime.now(),
            }

            all_data.append(row)

    return pd.DataFrame(all_data)
