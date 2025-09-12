"""Agent execution and data models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Integer, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class AgentRun(Base):
    """Agent execution history and status."""
    
    __tablename__ = "agent_runs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    stats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    watermark: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('agent', 'run_id', name='uniq_agent_run'),
    )


class AdMetrics(Base):
    """Unified ad metrics across all platforms."""
    
    __tablename__ = "ad_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # 'google', 'reddit', 'x'
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    account_id: Mapped[str] = mapped_column(String(50), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(50), nullable=False)
    adgroup_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ad_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    campaign_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spend_usd: Mapped[float] = mapped_column(nullable=False)
    conversions: Mapped[float] = mapped_column(default=0.0, nullable=False)
    ctr: Mapped[Optional[float]] = mapped_column(nullable=True)
    cpc_usd: Mapped[Optional[float]] = mapped_column(nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('platform', 'date', 'account_id', 'campaign_id', 'adgroup_id', 'ad_id', 
                        name='uniq_ad_metrics_row'),
    )


class Touchpoint(Base):
    """User touchpoints derived from events."""
    
    __tablename__ = "touchpoints"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # 'google', 'reddit', 'x', 'other'
    click_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    campaign: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    landing_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_properties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        # De-dupe by (user_id, timestamp, platform, campaign)
        UniqueConstraint('user_id', 'timestamp', 'platform', 'campaign', 
                        name='uniq_touchpoint'),
    )


class Conversion(Base):
    """Conversion events for upload to platforms."""
    
    __tablename__ = "conversions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    conversion_name: Mapped[str] = mapped_column(String(100), nullable=False)
    conversion_value: Mapped[float] = mapped_column(default=0.0, nullable=False)
    conversion_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    click_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_source: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    uploaded_to_platforms: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Track upload status
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CampaignPolicy(Base):
    """Campaign optimization policies and targets."""
    
    __tablename__ = "campaign_policies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(50), nullable=False)
    target_cac: Mapped[Optional[float]] = mapped_column(nullable=True)
    target_roas: Mapped[Optional[float]] = mapped_column(nullable=True)
    min_daily_budget: Mapped[Optional[float]] = mapped_column(nullable=True)
    max_daily_budget: Mapped[Optional[float]] = mapped_column(nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('platform', 'campaign_id', name='uniq_campaign_policy'),
    )


class KeywordsExternal(Base):
    """External keyword research data."""
    
    __tablename__ = "keywords_external"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # 'ke_api', 'semrush', etc.
    monthly_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    est_cpc: Mapped[Optional[float]] = mapped_column(nullable=True)
    competition: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'low', 'medium', 'high'
    pulled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('keyword', 'source', name='uniq_keyword_source'),
    )
