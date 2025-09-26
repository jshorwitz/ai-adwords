"""
Streamlit dashboard for Google Ads performance analytics.
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from ads.accounts import get_customer_info, list_accessible_clients
    from ads.bigquery_client import create_bigquery_client_from_env
    from ads.conversion_validator import create_validator_from_env
except ImportError:
    # For Streamlit Cloud deployment
    sys.path.append("/app/src")
    from ads.accounts import get_customer_info, list_accessible_clients
    from ads.bigquery_client import create_bigquery_client_from_env
    from ads.conversion_validator import create_validator_from_env


class GoogleAdsDashboard:
    """Main dashboard class for Google Ads analytics."""

    def __init__(self):
        try:
            self.bq_client = create_bigquery_client_from_env()
        except Exception:
            self.bq_client = None  # Will use demo data instead
        self._accounts_cache = None

    def get_accessible_accounts(self, refresh: bool = False) -> dict[str, str]:
        """Get accessible Google Ads accounts with their names."""
        if self._accounts_cache is None or refresh:
            try:
                # Use demo accounts if in demo mode
                if os.getenv("ADS_USE_DEMO") == "1" or os.getenv("ADS_USE_MOCK") == "1":
                    self._accounts_cache = {
                        "9639990200": "Sourcegraph",
                        "1234567890": "Demo Account 1",
                    }
                    return self._accounts_cache

                account_ids = list_accessible_clients()
                accounts = {}
                for account_id in account_ids:
                    info = get_customer_info(account_id)
                    if info and info.get("name"):
                        name = info["name"]
                    else:
                        # Fallback names for known accounts
                        if account_id == "9639990200":
                            name = "Sourcegraph"
                        else:
                            name = f"Account {account_id}"
                    accounts[account_id] = name
                self._accounts_cache = accounts
            except Exception as e:
                st.warning(f"Using demo mode due to API connection issue: {e}")
                # Fallback to demo accounts
                self._accounts_cache = {
                    "9639990200": "Sourcegraph (Demo)",
                    "1234567890": "Demo Account 1",
                }
        return self._accounts_cache

    def load_campaign_data(
        self, days_back: int = 30, customer_id: str = None
    ) -> pd.DataFrame:
        """Load campaign performance data from realistic sample or BigQuery."""
        # Check for real Sourcegraph data first
        if customer_id == "9639990200":
            real_data_file = "sourcegraph_realistic_sample.csv"
            if os.path.exists(real_data_file):
                df = pd.read_csv(real_data_file)
                st.info(
                    "📊 Using realistic Sourcegraph data based on actual account patterns"
                )
                return df

        # Always use direct API for demo mode or if BigQuery is unavailable
        if customer_id or self.bq_client is None:
            return self._load_direct_campaign_data(customer_id, days_back)

        try:
            where_clause = (
                f"WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)"
            )
            if customer_id:
                where_clause += f" AND customer_id = '{customer_id}'"

            query = f"""
            SELECT
                date,
                customer_id,
                campaign_id,
                campaign_name,
                campaign_status as status,
                impressions,
                clicks,
                cost,
                conversions,
                ctr,
                average_cpc_dollars as cpc,
                conversion_rate
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.campaigns_performance`
            {where_clause}
            ORDER BY date DESC, campaign_name
            """

            return self.bq_client.query(query)
        except Exception:
            # Fallback to direct API for any account if BigQuery fails
            if customer_id:
                return self._load_direct_campaign_data(customer_id, days_back)
            return pd.DataFrame()

    def _load_direct_campaign_data(
        self, customer_id: str, days_back: int
    ) -> pd.DataFrame:
        """Load campaign data directly from Google Ads API."""
        try:
            import os
            from datetime import datetime, timedelta

            from ads.reporting import ReportingManager

            # Try cached data first for known accounts if API fails
            if customer_id == "9639990200":
                cache_file = "/tmp/sourcegraph_dashboard_cache.csv"
            elif customer_id == "4174586061":
                cache_file = "/tmp/singlestore_dashboard_cache.csv"
            else:
                cache_file = None

            if cache_file:
                if os.path.exists(cache_file):
                    try:
                        df = pd.read_csv(cache_file)
                        df["date"] = pd.to_datetime(df["date"])

                        # Filter by days_back
                        cutoff_date = datetime.now() - timedelta(days=days_back)
                        df = df[df["date"] >= cutoff_date]

                        account_name = (
                            "Sourcegraph"
                            if customer_id == "9639990200"
                            else "SingleStore"
                        )
                        st.info(
                            f"📊 Using cached {account_name} data (API connectivity issues)"
                        )
                        return df
                    except Exception:
                        pass

            reporting = ReportingManager(customer_id)
            df = reporting.get_campaign_performance()

            if df.empty:
                return df

            # Convert to match BigQuery schema
            df["date"] = pd.to_datetime(df["date"])
            df["cost"] = df["cost_micros"] / 1_000_000  # Convert from micros to dollars
            df["cpc"] = df["average_cpc"] / 1_000_000  # Convert from micros to dollars
            df["status"] = df["campaign_status"]
            df["conversion_rate"] = (df["conversions"] / df["clicks"] * 100).fillna(0)

            # Filter by days_back
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df = df[df["date"] >= cutoff_date]

            # Select and rename columns to match expected schema
            return df[
                [
                    "date",
                    "customer_id",
                    "campaign_id",
                    "campaign_name",
                    "status",
                    "impressions",
                    "clicks",
                    "cost",
                    "conversions",
                    "ctr",
                    "cpc",
                    "conversion_rate",
                ]
            ]

        except Exception as e:
            st.error(f"Error loading direct API data: {e}")
            return pd.DataFrame()

    def load_keyword_data(
        self, days_back: int = 30, customer_id: str = None
    ) -> pd.DataFrame:
        """Load keyword performance data from BigQuery or direct API."""
        # Always use direct API for demo mode or if BigQuery is unavailable
        if customer_id or self.bq_client is None:
            return self._load_direct_keyword_data(customer_id, days_back)

        try:
            where_clause = (
                f"WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)"
            )
            if customer_id:
                where_clause += f" AND customer_id = '{customer_id}'"

            query = f"""
            SELECT
                date,
                customer_id,
                campaign_id,
                '' as campaign_name,
                ad_group_id,
                '' as ad_group_name,
                criterion_id as keyword_id,
                keyword_text,
                match_type,
                impressions,
                clicks,
                cost,
                conversions,
                ctr,
                average_cpc_dollars as cpc,
                (conversions / clicks * 100) as conversion_rate,
                quality_score
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.keywords_performance`
            {where_clause}
            ORDER BY date DESC, campaign_name, keyword_text
            """

            return self.bq_client.query(query)
        except Exception:
            # Fallback to direct API for any account if BigQuery fails
            if customer_id:
                return self._load_direct_keyword_data(customer_id, days_back)
            return pd.DataFrame()

    def _load_direct_keyword_data(
        self, customer_id: str, days_back: int
    ) -> pd.DataFrame:
        """Load keyword data directly from Google Ads API."""
        try:
            import os
            from datetime import datetime

            from ads.keywords import list_keywords

            # Try cached keyword analysis first
            if customer_id == "9639990200":
                cache_file = "/tmp/sourcegraph_keyword_detailed.csv"
            elif customer_id == "4174586061":
                cache_file = "/tmp/singlestore_keyword_detailed.csv"
            else:
                cache_file = None
            if os.path.exists(cache_file):
                try:
                    df = pd.read_csv(cache_file)
                    if "keyword_text" not in df.columns and "keyword" in df.columns:
                        df["keyword_text"] = df["keyword"]

                    # Add required columns if missing
                    for col in [
                        "date",
                        "customer_id",
                        "campaign_id",
                        "campaign_name",
                        "ad_group_id",
                        "ad_group_name",
                        "quality_score",
                    ]:
                        if col not in df.columns:
                            if col == "date":
                                df[col] = datetime.now().date()
                            elif col == "customer_id":
                                df[col] = customer_id
                            elif col in ["campaign_id", "ad_group_id", "quality_score"]:
                                df[col] = 0
                            else:
                                df[col] = ""

                    account_name = (
                        "Sourcegraph"
                        if customer_id == "9639990200"
                        else "SingleStore"
                        if customer_id == "4174586061"
                        else "Account"
                    )
                    st.info(f"📊 Using cached {account_name} keyword analysis data")
                    return df
                except Exception:
                    pass

            # Fallback to live API call
            keywords = list_keywords(customer_id, limit=100)

            if not keywords:
                return pd.DataFrame()

            # Convert to DataFrame format expected by dashboard
            df = pd.DataFrame(keywords)
            df["date"] = datetime.now().date()
            df["customer_id"] = customer_id
            df["keyword_text"] = df.get("keyword", "")
            df["campaign_name"] = ""
            df["ad_group_name"] = ""
            df["quality_score"] = 0
            df["cost"] = (
                df.get("cost_micros", df.get("cost", 0)) / 1_000_000
                if "cost_micros" in df.columns
                else df.get("cost", 0)
            )
            df["cpc"] = df.get("avg_cpc", 0)
            df["ctr"] = (df["clicks"] / df["impressions"] * 100).fillna(0)
            df["conversion_rate"] = (
                df.get("conversions", 0) / df["clicks"] * 100
            ).fillna(0)

            return df

        except Exception as e:
            st.error(f"Error loading keyword data: {e}")
            return pd.DataFrame()


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Google Ads Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🚀 Google Ads Analytics Dashboard")
    st.markdown("Real-time insights from your Google Ads campaigns")

    # Initialize dashboard
    try:
        dashboard = GoogleAdsDashboard()
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {e}")
        st.stop()

    # Sidebar filters
    st.sidebar.header("Filters")

    # Account filter with refresh button
    col1, col2 = st.sidebar.columns([3, 1])
    with col2:
        if st.button("🔄", help="Refresh accounts", key="refresh_accounts"):
            dashboard.get_accessible_accounts(refresh=True)
            st.rerun()

    with col1:
        accounts = dashboard.get_accessible_accounts()
        if accounts:
            account_options = ["All Accounts"] + [
                f"{name} ({acc_id})" for acc_id, name in accounts.items()
            ]
            selected_account_option = st.selectbox(
                "Google Ads Account", account_options
            )

            if selected_account_option == "All Accounts":
                selected_customer_id = None
            else:
                # Extract customer ID from the display format "Name (ID)"
                selected_customer_id = selected_account_option.split("(")[-1].rstrip(
                    ")"
                )
        else:
            selected_customer_id = None
            st.warning("No accessible accounts found")

    days_back = st.sidebar.selectbox(
        "Time Period", [7, 14, 30, 60, 90], index=2, help="Number of days to look back"
    )

    # Load data
    with st.spinner("Loading campaign data..."):
        try:
            campaign_df = dashboard.load_campaign_data(days_back, selected_customer_id)
            keyword_df = dashboard.load_keyword_data(days_back, selected_customer_id)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

    if campaign_df.empty:
        account_info = (
            f" for account {selected_account_option}" if selected_customer_id else ""
        )
        st.warning(
            f"No campaign data found for the selected time period{account_info}."
        )
        st.stop()

    # Campaign filter
    campaigns = ["All"] + sorted(campaign_df["campaign_name"].unique().tolist())
    selected_campaign = st.sidebar.selectbox("Campaign", campaigns)

    # Filter data based on selection
    if selected_campaign != "All":
        campaign_df = campaign_df[campaign_df["campaign_name"] == selected_campaign]
        keyword_df = keyword_df[keyword_df["campaign_name"] == selected_campaign]

    # Key Metrics Row
    st.header("📈 Key Performance Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_impressions = campaign_df["impressions"].sum()
        st.metric("Total Impressions", f"{total_impressions:,}")

    with col2:
        total_clicks = campaign_df["clicks"].sum()
        avg_ctr = (
            (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        )
        st.metric("Total Clicks", f"{total_clicks:,}", f"{avg_ctr:.2f}% CTR")

    with col3:
        total_cost = campaign_df["cost"].sum()
        avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        st.metric("Total Spend", f"${total_cost:,.2f}", f"${avg_cpc:.2f} CPC")

    with col4:
        total_conversions = campaign_df["conversions"].sum()
        conv_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        st.metric("Conversions", f"{total_conversions:,}", f"{conv_rate:.2f}% Rate")

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Daily Performance Trend")
        daily_data = (
            campaign_df.groupby("date")
            .agg(
                {
                    "impressions": "sum",
                    "clicks": "sum",
                    "cost": "sum",
                    "conversions": "sum",
                }
            )
            .reset_index()
        )

        fig = px.line(
            daily_data,
            x="date",
            y=["clicks", "conversions"],
            title="Clicks & Conversions Over Time",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Cost & CTR Analysis")
        daily_data["ctr"] = (
            daily_data["clicks"] / daily_data["impressions"] * 100
        ).fillna(0)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=daily_data["date"], y=daily_data["cost"], name="Daily Cost", yaxis="y"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=daily_data["date"], y=daily_data["ctr"], name="CTR %", yaxis="y2"
            )
        )

        fig.update_layout(
            title="Daily Cost vs CTR",
            yaxis={"title": "Cost ($)", "side": "left"},
            yaxis2={"title": "CTR (%)", "side": "right", "overlaying": "y"},
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Campaign Performance Table
    st.header("🎯 Campaign Performance Summary")

    campaign_summary = (
        campaign_df.groupby("campaign_name")
        .agg(
            {
                "impressions": "sum",
                "clicks": "sum",
                "cost": "sum",
                "conversions": "sum",
                "ctr": "mean",
                "cpc": "mean",
                "conversion_rate": "mean",
            }
        )
        .reset_index()
    )

    # Format the dataframe for display
    campaign_summary["cost"] = campaign_summary["cost"].apply(lambda x: f"${x:,.2f}")
    campaign_summary["ctr"] = campaign_summary["ctr"].apply(lambda x: f"{x:.2f}%")
    campaign_summary["cpc"] = campaign_summary["cpc"].apply(lambda x: f"${x:.2f}")
    campaign_summary["conversion_rate"] = campaign_summary["conversion_rate"].apply(
        lambda x: f"{x:.2f}%"
    )

    st.dataframe(campaign_summary, use_container_width=True)

    # Account-specific keyword analysis section
    if selected_customer_id in ["9639990200", "4174586061"]:
        account_name = (
            "Sourcegraph" if selected_customer_id == "9639990200" else "SingleStore"
        )
        st.header(f"🎯 {account_name} Keyword Performance Analysis")

        # Load keyword analysis results
        if selected_customer_id == "9639990200":
            analysis_file = "/tmp/sourcegraph_keyword_analysis.json"
            analysis_script = "sourcegraph_keyword_analysis.py"
        else:
            analysis_file = "/tmp/singlestore_keyword_analysis.json"
            analysis_script = "singlestore_keyword_analysis.py"
        keyword_analysis = None

        import json
        import os

        if os.path.exists(analysis_file):
            try:
                with open(analysis_file) as f:
                    keyword_analysis = json.load(f)
                st.success("📊 Showing latest keyword analysis results")
            except Exception:
                pass

        if keyword_analysis:
            # Analysis summary metrics
            st.subheader("📈 Analysis Summary")

            col1, col2, col3, col4 = st.columns(4)

            summary = keyword_analysis["summary"]
            with col1:
                st.metric("Keywords Analyzed", f"{summary['total_keywords']}")

            with col2:
                st.metric("Total Impressions", f"{summary['total_impressions']:,}")

            with col3:
                st.metric("Average CTR", f"{summary['average_ctr']:.2f}%")

            with col4:
                st.metric("Average CPC", f"${summary['average_cpc']:.2f}")

            # Performance issues
            issues = keyword_analysis["issues"]
            if any(issues.values()):
                st.subheader("🚨 Performance Issues Identified")

                if issues["low_ctr_keywords"] > 0:
                    st.error(
                        f"⚠️ {issues['low_ctr_keywords']} keywords with low CTR (<2%)"
                    )

                if issues["high_cpc_keywords"] > 0:
                    st.error(
                        f"⚠️ {issues['high_cpc_keywords']} keywords with high CPC (>$8)"
                    )

                if issues["zero_click_keywords"] > 0:
                    st.error(
                        f"⚠️ {issues['zero_click_keywords']} keywords with zero clicks despite impressions"
                    )

            else:
                st.success("✅ No major performance issues detected")

            # Top performers visualization
            st.subheader("🚀 Top Performing Keywords")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Top Keywords by Impressions**")
                top_imp = keyword_analysis["top_performers"]["by_impressions"]
                if top_imp:
                    imp_df = pd.DataFrame(top_imp)
                    fig = px.bar(
                        imp_df.head(5),
                        x="keyword",
                        y="impressions",
                        title="Top 5 Keywords by Impressions",
                    )
                    fig.update_xaxes(tickangle=45)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.write("**Top Keywords by Clicks**")
                top_clicks = keyword_analysis["top_performers"]["by_clicks"]
                if top_clicks:
                    clicks_df = pd.DataFrame(top_clicks)
                    fig = px.bar(
                        clicks_df.head(5),
                        x="keyword",
                        y="clicks",
                        title="Top 5 Keywords by Clicks",
                    )
                    fig.update_xaxes(tickangle=45)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("⚡ Run keyword analysis to see detailed insights")

            if st.button(
                f"🔄 Generate Fresh {account_name} Keyword Analysis", key="run_analysis"
            ):
                with st.spinner(f"Analyzing {account_name} keywords..."):
                    try:
                        import subprocess

                        result = subprocess.run(
                            ["poetry", "run", "python", analysis_script],
                            cwd="/Users/joelhorwitz/dev/ai-adwords",
                            env={
                                **os.environ,
                                "ADS_USE_DEMO": "1",
                                "CUSTOMER_ID": selected_customer_id,
                            },
                            capture_output=True,
                            text=True,
                        )

                        if result.returncode == 0:
                            st.success(
                                "✅ Analysis complete! Refresh the page to see results."
                            )
                        else:
                            st.error(f"Analysis failed: {result.stderr}")

                    except Exception as e:
                        st.error(f"Failed to run analysis: {e}")

    # Top Keywords Section (for other accounts)
    elif not keyword_df.empty:
        st.header("🔍 Top Performing Keywords")

        # Top keywords by clicks
        top_keywords = (
            keyword_df.groupby("keyword_text")
            .agg(
                {
                    "clicks": "sum",
                    "impressions": "sum",
                    "cost": "sum",
                    "conversions": "sum",
                    "quality_score": "mean",
                }
            )
            .reset_index()
        )

        top_keywords = top_keywords.sort_values("clicks", ascending=False).head(20)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                top_keywords.head(10),
                x="keyword_text",
                y="clicks",
                title="Top 10 Keywords by Clicks",
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                top_keywords,
                x="cost",
                y="conversions",
                size="clicks",
                hover_data=["keyword_text", "quality_score"],
                title="Cost vs Conversions (bubble size = clicks)",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    # Conversion Validation Section
    if selected_customer_id:
        st.header("🔍 Conversion Validation")
        st.markdown(
            "Compare Google Ads conversions with GA4 and PostHog data to validate attribution accuracy."
        )

        with st.expander("🔧 Conversion Validation Settings", expanded=False):
            st.markdown(
                """
            **Required Environment Variables:**
            - `GA4_PROPERTY_ID`: Your GA4 property ID
            - `GA4_CREDENTIALS_PATH`: Path to GA4 service account JSON (optional)
            - `POSTHOG_API_KEY`: Your PostHog API key
            - `POSTHOG_HOST`: PostHog instance host (optional, defaults to app.posthog.com)
            """
            )

            if st.button("🧪 Run Conversion Validation", key="validate_conversions"):
                with st.spinner("Validating conversions across platforms..."):
                    try:
                        validator = create_validator_from_env(selected_customer_id)
                        validation_result = validator.validate_conversions(
                            days_back=days_back
                        )

                        # Display insights
                        st.subheader("💡 Validation Insights")
                        for insight in validation_result["insights"]:
                            st.info(insight)

                        # Display comparison chart
                        if not validation_result["comparison"].empty:
                            st.subheader("📊 Multi-Platform Comparison")
                            comparison_chart = validator.create_comparison_chart(
                                validation_result["comparison"]
                            )
                            st.plotly_chart(comparison_chart, use_container_width=True)

                            # Show detailed comparison data
                            with st.expander("📋 Detailed Comparison Data"):
                                st.dataframe(
                                    validation_result["comparison"],
                                    use_container_width=True,
                                )
                        else:
                            st.warning(
                                "No comparison data available. Check your GA4 and PostHog configurations."
                            )

                    except Exception as e:
                        st.error(f"Conversion validation failed: {e}")
                        st.info(
                            "Make sure GA4 and PostHog credentials are properly configured."
                        )
    else:
        st.info("Select a specific account to access conversion validation features.")


if __name__ == "__main__":
    main()
