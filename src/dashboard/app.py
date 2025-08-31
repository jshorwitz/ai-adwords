"""
Streamlit dashboard for Google Ads performance analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from ads.bigquery_client import create_bigquery_client_from_env
except ImportError:
    # For Streamlit Cloud deployment
    sys.path.append('/app/src')
    from ads.bigquery_client import create_bigquery_client_from_env


class GoogleAdsDashboard:
    """Main dashboard class for Google Ads analytics."""
    
    def __init__(self):
        self.bq_client = create_bigquery_client_from_env()
    
    def load_campaign_data(self, days_back: int = 30) -> pd.DataFrame:
        """Load campaign performance data from BigQuery."""
        query = f"""
        SELECT 
            date,
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
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
        ORDER BY date DESC, campaign_name
        """
        
        return self.bq_client.query(query)
    
    def load_keyword_data(self, days_back: int = 30) -> pd.DataFrame:
        """Load keyword performance data from BigQuery."""
        query = f"""
        SELECT 
            date,
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
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
        ORDER BY date DESC, campaign_name, keyword_text
        """
        
        return self.bq_client.query(query)


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Google Ads Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
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
    days_back = st.sidebar.selectbox(
        "Time Period", 
        [7, 14, 30, 60, 90], 
        index=2,
        help="Number of days to look back"
    )
    
    # Load data
    with st.spinner("Loading campaign data..."):
        try:
            campaign_df = dashboard.load_campaign_data(days_back)
            keyword_df = dashboard.load_keyword_data(days_back)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()
    
    if campaign_df.empty:
        st.warning("No campaign data found for the selected time period.")
        st.stop()
    
    # Campaign filter
    campaigns = ['All'] + sorted(campaign_df['campaign_name'].unique().tolist())
    selected_campaign = st.sidebar.selectbox("Campaign", campaigns)
    
    # Filter data based on selection
    if selected_campaign != 'All':
        campaign_df = campaign_df[campaign_df['campaign_name'] == selected_campaign]
        keyword_df = keyword_df[keyword_df['campaign_name'] == selected_campaign]
    
    # Key Metrics Row
    st.header("📈 Key Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_impressions = campaign_df['impressions'].sum()
        st.metric("Total Impressions", f"{total_impressions:,}")
    
    with col2:
        total_clicks = campaign_df['clicks'].sum()
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        st.metric("Total Clicks", f"{total_clicks:,}", f"{avg_ctr:.2f}% CTR")
    
    with col3:
        total_cost = campaign_df['cost'].sum()
        avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        st.metric("Total Spend", f"${total_cost:,.2f}", f"${avg_cpc:.2f} CPC")
    
    with col4:
        total_conversions = campaign_df['conversions'].sum()
        conv_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        st.metric("Conversions", f"{total_conversions:,}", f"{conv_rate:.2f}% Rate")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Daily Performance Trend")
        daily_data = campaign_df.groupby('date').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum',
            'conversions': 'sum'
        }).reset_index()
        
        fig = px.line(
            daily_data, 
            x='date', 
            y=['clicks', 'conversions'],
            title="Clicks & Conversions Over Time"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Cost & CTR Analysis")
        daily_data['ctr'] = (daily_data['clicks'] / daily_data['impressions'] * 100).fillna(0)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['cost'],
            name='Daily Cost',
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['ctr'],
            name='CTR %',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Daily Cost vs CTR",
            yaxis=dict(title="Cost ($)", side="left"),
            yaxis2=dict(title="CTR (%)", side="right", overlaying="y"),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Campaign Performance Table
    st.header("🎯 Campaign Performance Summary")
    
    campaign_summary = campaign_df.groupby('campaign_name').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'cost': 'sum',
        'conversions': 'sum',
        'ctr': 'mean',
        'cpc': 'mean',
        'conversion_rate': 'mean'
    }).reset_index()
    
    # Format the dataframe for display
    campaign_summary['cost'] = campaign_summary['cost'].apply(lambda x: f"${x:,.2f}")
    campaign_summary['ctr'] = campaign_summary['ctr'].apply(lambda x: f"{x:.2f}%")
    campaign_summary['cpc'] = campaign_summary['cpc'].apply(lambda x: f"${x:.2f}")
    campaign_summary['conversion_rate'] = campaign_summary['conversion_rate'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(campaign_summary, use_container_width=True)
    
    # Top Keywords Section
    if not keyword_df.empty:
        st.header("🔍 Top Performing Keywords")
        
        # Top keywords by clicks
        top_keywords = keyword_df.groupby('keyword_text').agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'cost': 'sum',
            'conversions': 'sum',
            'quality_score': 'mean'
        }).reset_index()
        
        top_keywords = top_keywords.sort_values('clicks', ascending=False).head(20)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                top_keywords.head(10),
                x='keyword_text',
                y='clicks',
                title="Top 10 Keywords by Clicks"
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                top_keywords,
                x='cost',
                y='conversions',
                size='clicks',
                hover_data=['keyword_text', 'quality_score'],
                title="Cost vs Conversions (bubble size = clicks)"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
