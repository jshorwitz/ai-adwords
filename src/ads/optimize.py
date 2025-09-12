"""Optimization engine - SQR mining, pacing, recommendations, experiments."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from .ads_client import create_client_from_env
from .campaigns import create_campaign
from .reporting import ReportingManager

logger = logging.getLogger(__name__)


@dataclass
class CampaignConsolidationPlan:
    """Plan for consolidating campaigns."""

    campaigns_to_archive: list[dict[str, Any]]
    campaigns_to_merge: list[dict[str, list[dict[str, Any]]]]
    new_campaigns_to_create: list[dict[str, Any]]
    budget_reallocations: list[dict[str, Any]]


@dataclass
class OptimizationRule:
    """Represents an optimization rule with conditions and actions."""

    id: str
    name: str
    rule_type: str  # 'bid_adjustment', 'keyword_management', 'budget_allocation'
    conditions: dict[str, Any]
    actions: dict[str, Any]
    enabled: bool = True


class CampaignConsolidator:
    """Manages campaign consolidation for Sourcegraph optimization."""

    # Define the new dual-product campaign structure for Sourcegraph
    SOURCEGRAPH_CAMPAIGN_STRUCTURE = [
        # === CODE SEARCH PRODUCT LINE ===
        {
            "name": "25Q1 - Code Search Brand - Global",
            "type": "CODE_SEARCH_BRAND",
            "product": "CODE_SEARCH",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSION_VALUE",
            "daily_budget_micros": 120_000_000,  # $120/day
            "keywords": ["sourcegraph", "sourcegraph code search", "source graph"],
            "match_types": ["EXACT", "PHRASE"],
            "landing_page_focus": "code_search",
        },
        {
            "name": "25Q1 - Enterprise Code Search - NA",
            "type": "CODE_SEARCH_ENTERPRISE",
            "product": "CODE_SEARCH",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSION_VALUE",
            "daily_budget_micros": 250_000_000,  # $250/day
            "keywords": [
                "enterprise code search",
                "code search platform",
                "large codebase search",
            ],
            "match_types": ["PHRASE", "BROAD"],
            "landing_page_focus": "enterprise_code_search",
        },
        {
            "name": "25Q1 - Code Search Competitors - Global",
            "type": "CODE_SEARCH_COMPETITOR",
            "product": "CODE_SEARCH",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "daily_budget_micros": 150_000_000,  # $150/day
            "keywords": [
                "github search",
                "gitlab search",
                "bitbucket search",
                "azure devops search",
            ],
            "match_types": ["PHRASE", "BROAD"],
            "landing_page_focus": "code_search_vs_competitors",
        },
        {
            "name": "25Q1 - Code Discovery Tools - Global",
            "type": "CODE_SEARCH_CATEGORY",
            "product": "CODE_SEARCH",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "daily_budget_micros": 125_000_000,  # $125/day
            "keywords": [
                "code search",
                "search codebase",
                "find code",
                "code navigation",
            ],
            "match_types": ["PHRASE", "BROAD"],
            "landing_page_focus": "code_discovery",
        },
        # === AMP AI PRODUCT LINE ===
        {
            "name": "25Q1 - Amp AI Brand - Global",
            "type": "AMP_BRAND",
            "product": "AMP",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSION_VALUE",
            "daily_budget_micros": 130_000_000,  # $130/day
            "keywords": ["amp coding", "amp ai", "ampcode", "sourcegraph amp"],
            "match_types": ["EXACT", "PHRASE"],
            "landing_page_focus": "amp_product",
        },
        {
            "name": "25Q1 - AI Coding Assistant - Global",
            "type": "AMP_CATEGORY",
            "product": "AMP",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "daily_budget_micros": 200_000_000,  # $200/day
            "keywords": [
                "ai coding assistant",
                "autonomous coding",
                "ai code generation",
                "agentic coding",
            ],
            "match_types": ["PHRASE", "BROAD"],
            "landing_page_focus": "ai_coding_assistant",
        },
        {
            "name": "25Q1 - Amp AI Competitors - Global",
            "type": "AMP_COMPETITOR",
            "product": "AMP",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "daily_budget_micros": 175_000_000,  # $175/day
            "keywords": [
                "cursor ai",
                "github copilot",
                "claude dev",
                "aider ai",
                "windsurf ai",
            ],
            "match_types": ["PHRASE", "BROAD"],
            "landing_page_focus": "amp_vs_competitors",
        },
        {
            "name": "25Q1 - AI Developer Productivity - Global",
            "type": "AMP_PRODUCTIVITY",
            "product": "AMP",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "daily_budget_micros": 150_000_000,  # $150/day
            "keywords": [
                "ai developer tools",
                "coding automation",
                "ai pair programming",
                "code refactoring ai",
            ],
            "match_types": ["PHRASE", "BROAD"],
            "landing_page_focus": "developer_productivity_ai",
        },
        # === SHARED/CROSS-PRODUCT ===
        {
            "name": "25Q1 - Performance Max - Dual Product",
            "type": "PMAX_SHARED",
            "product": "BOTH",
            "channel": "PERFORMANCE_MAX",
            "bidding_strategy": "MAXIMIZE_CONVERSION_VALUE",
            "daily_budget_micros": 200_000_000,  # $200/day
            "keywords": [],  # Performance Max uses asset groups
            "match_types": [],
            "landing_page_focus": "multi_product",
        },
        {
            "name": "25Q1 - Geographic Expansion - EMEA",
            "type": "GEO_EXPANSION",
            "product": "BOTH",
            "channel": "SEARCH",
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "daily_budget_micros": 100_000_000,  # $100/day
            "keywords": ["sourcegraph", "amp coding", "code search platform"],
            "match_types": ["EXACT", "PHRASE"],
            "landing_page_focus": "regional_landing",
        },
    ]

    def __init__(self, customer_id: str):
        """Initialize the consolidator for a specific customer."""
        self.customer_id = customer_id
        self.reporting = ReportingManager(customer_id)

    def analyze_current_campaigns(self, days_back: int = 30) -> pd.DataFrame:
        """Analyze current campaign performance to identify consolidation opportunities."""
        try:
            # Get campaign performance data
            df = self.reporting.get_campaign_performance()

            if df.empty:
                logger.warning("No campaign performance data found")
                return pd.DataFrame()

            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df = df[df["date"] >= cutoff_date]

            # Aggregate performance metrics by campaign
            performance = (
                df.groupby(["campaign_id", "campaign_name"])
                .agg(
                    {
                        "impressions": "sum",
                        "clicks": "sum",
                        "cost_micros": "sum",
                        "conversions": "sum",
                        "ctr": "mean",
                        "average_cpc": "mean",
                    }
                )
                .reset_index()
            )

            # Calculate derived metrics
            performance["cost"] = performance["cost_micros"] / 1_000_000
            performance["cpc"] = performance["average_cpc"] / 1_000_000
            performance["conversion_rate"] = (
                performance["conversions"] / performance["clicks"] * 100
            ).fillna(0)
            performance["cost_per_conversion"] = (
                performance["cost"] / performance["conversions"]
            ).fillna(0)

            # Add consolidation flags
            performance["should_archive"] = self._should_archive_campaign(performance)
            performance["consolidation_target"] = self._get_consolidation_target(
                performance
            )

            return performance

        except Exception as e:
            logger.error(f"Error analyzing campaigns: {e}")
            return pd.DataFrame()

    def _should_archive_campaign(self, df: pd.DataFrame) -> pd.Series:
        """Determine which campaigns should be archived."""
        conditions = (
            (df["conversions"] < 5)
            | (df["cost_per_conversion"] > 50)  # Less than 5 conversions
            | (df["clicks"] < 50)  # CPA > $50
            | (  # Less than 50 clicks
                df["campaign_name"].str.contains("23Q3|24Q4", case=False, na=False)
            )  # Legacy campaigns
        )
        return conditions

    def _get_consolidation_target(self, df: pd.DataFrame) -> pd.Series:
        """Determine which new campaign each existing campaign should merge into."""
        targets = []

        for _, row in df.iterrows():
            campaign_name = row["campaign_name"].lower()

            # === AMP AI PRODUCT LINE ===
            # Amp brand campaigns
            if any(amp in campaign_name for amp in ["amp", "cody", "sourcegraph amp"]):
                targets.append("25Q1 - Amp AI Brand - Global")
            # AI coding assistant campaigns
            elif any(
                ai in campaign_name
                for ai in [
                    "ai coding",
                    "autonomous coding",
                    "agentic",
                    "coding assistant",
                ]
            ):
                targets.append("25Q1 - AI Coding Assistant - Global")
            # Amp competitors
            elif any(
                comp in campaign_name
                for comp in ["cursor", "copilot", "claude dev", "aider", "windsurf"]
            ):
                targets.append("25Q1 - Amp AI Competitors - Global")
            # AI productivity tools
            elif any(
                prod in campaign_name
                for prod in ["ai developer", "coding automation", "ai pair"]
            ):
                targets.append("25Q1 - AI Developer Productivity - Global")

            # === CODE SEARCH PRODUCT LINE ===
            # Code search brand campaigns (exclude amp)
            elif (
                any(brand in campaign_name for brand in ["brand", "sourcegraph"])
                and "amp" not in campaign_name
            ):
                targets.append("25Q1 - Code Search Brand - Global")
            # Enterprise code search
            elif any(ent in campaign_name for ent in ["enterprise", "starter"]) and any(
                search in campaign_name for search in ["code search", "search"]
            ):
                targets.append("25Q1 - Enterprise Code Search - NA")
            # Code search competitors
            elif any(
                comp in campaign_name
                for comp in [
                    "github search",
                    "gitlab search",
                    "bitbucket search",
                    "azure devops",
                ]
            ):
                targets.append("25Q1 - Code Search Competitors - Global")
            # Code discovery tools
            elif any(
                search in campaign_name
                for search in [
                    "code search",
                    "search codebase",
                    "find code",
                    "code navigation",
                ]
            ):
                targets.append("25Q1 - Code Discovery Tools - Global")

            # === SHARED/CROSS-PRODUCT ===
            # Performance Max
            elif "pmax" in campaign_name or "performance" in campaign_name:
                targets.append("25Q1 - Performance Max - Dual Product")
            # Geographic expansion
            elif any(geo in campaign_name for geo in ["emea", "europe", "apac", "anz"]):
                targets.append("25Q1 - Geographic Expansion - EMEA")

            # Default fallback - determine by keywords
            else:
                # If contains AI/ML terms, default to Amp
                if any(
                    ai_term in campaign_name
                    for ai_term in ["ai", "ml", "assistant", "automation"]
                ):
                    targets.append("25Q1 - AI Coding Assistant - Global")
                # Otherwise default to code search
                else:
                    targets.append("25Q1 - Code Discovery Tools - Global")

        return pd.Series(targets, index=df.index)

    def create_consolidation_plan(self) -> CampaignConsolidationPlan:
        """Create a comprehensive plan for campaign consolidation."""
        performance_df = self.analyze_current_campaigns()

        # Always create the new campaign structure for Sourcegraph
        new_campaigns_to_create = self.SOURCEGRAPH_CAMPAIGN_STRUCTURE.copy()

        if performance_df.empty:
            logger.warning(
                "No performance data available - creating fresh campaign structure"
            )
            return CampaignConsolidationPlan([], [], new_campaigns_to_create, [])

        # Campaigns to archive
        campaigns_to_archive = performance_df[performance_df["should_archive"]].to_dict(
            "records"
        )

        # Campaigns to merge (group by consolidation target)
        campaigns_to_merge = []
        active_campaigns = performance_df[~performance_df["should_archive"]]

        for target in active_campaigns["consolidation_target"].unique():
            campaigns_in_group = active_campaigns[
                active_campaigns["consolidation_target"] == target
            ].to_dict("records")

            if len(campaigns_in_group) > 0:
                campaigns_to_merge.append(
                    {"target_campaign": target, "source_campaigns": campaigns_in_group}
                )

        # New campaigns to create (already defined above)

        # Budget reallocations based on performance
        budget_reallocations = self._calculate_budget_reallocations(active_campaigns)

        return CampaignConsolidationPlan(
            campaigns_to_archive=campaigns_to_archive,
            campaigns_to_merge=campaigns_to_merge,
            new_campaigns_to_create=new_campaigns_to_create,
            budget_reallocations=budget_reallocations,
        )

    def _calculate_budget_reallocations(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Calculate optimal budget allocation based on performance."""
        reallocations = []

        # Sort by cost per conversion (ascending = better performance)
        df_sorted = df.sort_values("cost_per_conversion")

        # Top performers get budget increases
        top_performers = df_sorted.head(3)
        for _, campaign in top_performers.iterrows():
            if campaign["cost_per_conversion"] < 15:  # Less than $15 CPA
                reallocations.append(
                    {
                        "campaign_name": campaign["campaign_name"],
                        "current_budget": campaign["cost"]
                        * 30,  # Estimate monthly budget
                        "recommended_budget_change": 0.30,  # +30%
                        "reason": f"High performance: ${campaign['cost_per_conversion']:.2f} CPA",
                    }
                )

        # Poor performers get budget decreases
        poor_performers = df_sorted.tail(5)
        for _, campaign in poor_performers.iterrows():
            if campaign["cost_per_conversion"] > 25:  # More than $25 CPA
                reallocations.append(
                    {
                        "campaign_name": campaign["campaign_name"],
                        "current_budget": campaign["cost"] * 30,
                        "recommended_budget_change": -0.25,  # -25%
                        "reason": f"Poor performance: ${campaign['cost_per_conversion']:.2f} CPA",
                    }
                )

        return reallocations

    def execute_consolidation_plan(
        self, plan: CampaignConsolidationPlan, dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute the campaign consolidation plan."""
        results = {
            "archived_campaigns": [],
            "created_campaigns": [],
            "errors": [],
            "dry_run": dry_run,
        }

        try:
            # Step 1: Create new campaign structure
            logger.info(
                f"Creating {len(plan.new_campaigns_to_create)} new campaigns..."
            )

            for campaign_config in plan.new_campaigns_to_create:
                try:
                    result = create_campaign(
                        customer_id=self.customer_id,
                        name=campaign_config["name"],
                        daily_budget_micros=campaign_config["daily_budget_micros"],
                        channel=campaign_config["channel"],
                        bidding_strategy=campaign_config["bidding_strategy"],
                        dry_run=dry_run,
                    )

                    results["created_campaigns"].append(
                        {
                            "name": campaign_config["name"],
                            "result": result,
                            "config": campaign_config,
                        }
                    )

                    logger.info(
                        f"Campaign creation {'validated' if dry_run else 'completed'}: {campaign_config['name']}"
                    )

                except Exception as e:
                    error_msg = (
                        f"Failed to create campaign {campaign_config['name']}: {e}"
                    )
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Step 2: Archive legacy campaigns (only in non-dry-run mode)
            if not dry_run and plan.campaigns_to_archive:
                logger.info(
                    f"Archiving {len(plan.campaigns_to_archive)} legacy campaigns..."
                )

                for campaign in plan.campaigns_to_archive:
                    try:
                        # Archive campaign by setting status to REMOVED
                        self._archive_campaign(campaign["campaign_id"])
                        results["archived_campaigns"].append(campaign)
                        logger.info(f"Archived campaign: {campaign['campaign_name']}")

                    except Exception as e:
                        error_msg = f"Failed to archive campaign {campaign['campaign_name']}: {e}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

            # Step 3: Log consolidation summary
            logger.info("Consolidation plan execution complete:")
            logger.info(f"- New campaigns: {len(results['created_campaigns'])}")
            logger.info(f"- Archived campaigns: {len(results['archived_campaigns'])}")
            logger.info(f"- Errors: {len(results['errors'])}")

        except Exception as e:
            error_msg = f"Error executing consolidation plan: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results

    def _archive_campaign(self, campaign_id: str) -> None:
        """Archive a campaign by setting its status to REMOVED."""
        if os.getenv("ADS_USE_MOCK") == "1":
            logger.info(f"Mock mode: Would archive campaign {campaign_id}")
            return

        service = create_client_from_env()
        client = service.client
        campaign_service = client.get_service("CampaignService")

        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.update
        campaign.resource_name = f"customers/{self.customer_id}/campaigns/{campaign_id}"
        campaign.status = client.enums.CampaignStatusEnum.REMOVED
        campaign_operation.update_mask.paths.append("status")

        campaign_service.mutate_campaigns(
            customer_id=self.customer_id, operations=[campaign_operation]
        )


class OptimizationManager:
    """Manages automated optimizations and recommendations."""

    def __init__(self, customer_id: str):
        """Initialize the optimization manager."""
        self.customer_id = customer_id
        self.consolidator = CampaignConsolidator(customer_id)
        self.reporting = ReportingManager(customer_id)
        self.optimization_rules: list[OptimizationRule] = []

    def consolidate_campaigns(self, dry_run: bool = True) -> dict[str, Any]:
        """Execute campaign consolidation for Sourcegraph optimization."""
        logger.info(
            f"Starting campaign consolidation for customer {self.customer_id} (dry_run={dry_run})"
        )

        # Create consolidation plan
        plan = self.consolidator.create_consolidation_plan()

        # Execute the plan
        results = self.consolidator.execute_consolidation_plan(plan, dry_run=dry_run)

        return {"consolidation_plan": plan, "execution_results": results}

    def analyze_consolidation_opportunities(self) -> pd.DataFrame:
        """Analyze current campaigns for consolidation opportunities."""
        return self.consolidator.analyze_current_campaigns()

    def mine_search_query_reports(self) -> None:
        """Mine search query reports for optimization opportunities."""
        # TODO: Implement SQR mining
        pass

    def adjust_bid_pacing(self) -> None:
        """Adjust bid pacing based on performance."""
        # TODO: Implement bid pacing adjustments
        pass

    def apply_recommendations(self) -> None:
        """Apply Google Ads recommendations."""
        # TODO: Implement Google Ads recommendations application
        pass

    def create_experiment(self) -> None:
        """Create campaign experiments for testing."""
        # TODO: Implement experiment creation
        pass

    def add_optimization_rule(self, rule: OptimizationRule) -> None:
        """Add an optimization rule."""
        self.optimization_rules.append(rule)

    def execute_optimization_rules(self, dry_run: bool = True) -> list[dict[str, Any]]:
        """Execute all enabled optimization rules."""
        results = []

        for rule in self.optimization_rules:
            if not rule.enabled:
                continue

            try:
                # TODO: Implement rule execution logic
                result = {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "status": "success",
                    "dry_run": dry_run,
                    "actions_taken": [],
                }
                results.append(result)

            except Exception as e:
                results.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "status": "error",
                        "error": str(e),
                        "dry_run": dry_run,
                    }
                )

        return results
