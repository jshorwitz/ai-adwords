"""Decision-making agents for budget optimization and campaign management."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..ads.optimize import OptimizationManager
from .base import DecisionAgent, AgentJobInput, AgentResult
from .runner import agent_registry

logger = logging.getLogger(__name__)


class BudgetOptimizerAgent(DecisionAgent):
    """Computes CAC/ROAS by campaign and adjusts budgets with guardrails."""
    
    def __init__(self, agent_name: str = "budget-optimizer"):
        super().__init__(agent_name)
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Analyze campaign performance and optimize budgets."""
        
        try:
            self.logger.info("Starting budget optimization analysis")
            
            # Get campaign performance data
            campaigns = await self._fetch_campaign_performance()
            
            if not campaigns:
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={"campaigns_analyzed": 0},
                    notes=["No campaigns found for optimization"],
                )
            
            # Analyze performance and generate recommendations
            recommendations = await self._analyze_and_recommend(campaigns)
            
            if job_input.dry_run:
                return await self._dry_run_optimization(job_input, recommendations)
            
            # Apply budget adjustments
            results = await self._apply_budget_changes(recommendations)
            
            return self.create_result(
                job_input,
                ok=True,
                metrics={
                    "campaigns_analyzed": len(campaigns),
                    "recommendations_generated": len(recommendations),
                    "budget_increases": results["increases"],
                    "budget_decreases": results["decreases"],
                    "campaigns_paused": results["paused"],
                },
                records_written=results["total_changes"],
                notes=[
                    f"Analyzed {len(campaigns)} campaigns",
                    f"Generated {len(recommendations)} recommendations",
                    f"Applied {results['total_changes']} budget changes",
                ],
            )
            
        except Exception as e:
            self.logger.exception("Failed to optimize budgets")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _fetch_campaign_performance(self) -> List[Dict[str, Any]]:
        """Fetch 14-day campaign performance data."""
        
        # TODO: Implement actual query from fact_attribution_* tables
        # This would compute trailing 14-day CAC & ROAS by campaign
        
        # Mock campaign performance data
        mock_campaigns = [
            {
                "campaign_id": "campaign_123",
                "campaign_name": "Brand Campaign - Sourcegraph",
                "platform": "google",
                "spend_14d": 5000.0,
                "conversions_14d": 25,
                "cac_14d": 200.0,  # spend / conversions
                "roas_14d": 3.5,   # revenue / spend
                "current_daily_budget": 500.0,
                "min_budget": 200.0,
                "max_budget": 1000.0,
                "target_cac": 180.0,
                "target_roas": 3.0,
            },
            {
                "campaign_id": "campaign_456",
                "campaign_name": "Search Campaign - Code Search",
                "platform": "google", 
                "spend_14d": 3000.0,
                "conversions_14d": 5,
                "cac_14d": 600.0,
                "roas_14d": 1.2,
                "current_daily_budget": 300.0,
                "min_budget": 100.0,
                "max_budget": 500.0,
                "target_cac": 300.0,
                "target_roas": 2.5,
            },
            {
                "campaign_id": "campaign_789",
                "campaign_name": "Reddit Awareness Campaign",
                "platform": "reddit",
                "spend_14d": 2000.0,
                "conversions_14d": 15,
                "cac_14d": 133.33,
                "roas_14d": 4.2,
                "current_daily_budget": 200.0,
                "min_budget": 50.0,
                "max_budget": 400.0,
                "target_cac": 150.0,
                "target_roas": 3.5,
            },
        ]
        
        self.logger.info(f"Fetched performance for {len(mock_campaigns)} campaigns")
        return mock_campaigns
    
    async def _analyze_and_recommend(self, campaigns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze performance and generate budget recommendations."""
        
        recommendations = []
        
        for campaign in campaigns:
            cac = campaign["cac_14d"]
            roas = campaign["roas_14d"]
            conversions = campaign["conversions_14d"]
            current_budget = campaign["current_daily_budget"]
            target_cac = campaign["target_cac"]
            target_roas = campaign["target_roas"]
            min_budget = campaign["min_budget"]
            max_budget = campaign["max_budget"]
            
            # Minimum conversion threshold for optimization
            min_conversions = 5
            
            recommendation = {
                "campaign_id": campaign["campaign_id"],
                "campaign_name": campaign["campaign_name"],
                "platform": campaign["platform"],
                "current_budget": current_budget,
                "action": "no_change",
                "new_budget": current_budget,
                "reason": "No action needed",
                "metrics": {
                    "cac": cac,
                    "roas": roas,
                    "conversions": conversions,
                    "target_cac": target_cac,
                    "target_roas": target_roas,
                },
            }
            
            # Only optimize if we have sufficient conversion volume
            if conversions >= min_conversions:
                # Increase budget if performing well
                if cac < target_cac and roas >= target_roas:
                    new_budget = min(current_budget * 1.15, max_budget)  # +15%
                    if new_budget > current_budget:
                        recommendation.update({
                            "action": "increase_budget",
                            "new_budget": new_budget,
                            "reason": f"CAC (${cac:.2f}) below target (${target_cac:.2f}) and ROAS ({roas:.2f}) meets target",
                        })
                
                # Decrease budget if underperforming
                elif cac > target_cac * 1.2 and conversions >= min_conversions:  # 20% over target
                    new_budget = max(current_budget * 0.8, min_budget)  # -20%
                    if new_budget < current_budget:
                        recommendation.update({
                            "action": "decrease_budget", 
                            "new_budget": new_budget,
                            "reason": f"CAC (${cac:.2f}) significantly above target (${target_cac:.2f})",
                        })
                
                # Pause if performance is very poor
                elif cac > target_cac * 2 and roas < target_roas * 0.5:
                    recommendation.update({
                        "action": "pause_campaign",
                        "new_budget": 0,
                        "reason": f"Very poor performance: CAC (${cac:.2f}) >> target, ROAS ({roas:.2f}) << target",
                    })
            
            else:
                recommendation["reason"] = f"Insufficient conversion volume ({conversions} < {min_conversions})"
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _dry_run_optimization(
        self, job_input: AgentJobInput, recommendations: List[Dict[str, Any]]
    ) -> AgentResult:
        """Simulate budget optimization in dry run mode."""
        
        changes_summary = {
            "increases": 0,
            "decreases": 0, 
            "paused": 0,
            "no_change": 0,
        }
        
        for rec in recommendations:
            action = rec["action"]
            if action == "increase_budget":
                changes_summary["increases"] += 1
            elif action == "decrease_budget":
                changes_summary["decreases"] += 1
            elif action == "pause_campaign":
                changes_summary["paused"] += 1
            else:
                changes_summary["no_change"] += 1
        
        # Log detailed recommendations
        for rec in recommendations:
            if rec["action"] != "no_change":
                self.logger.info(
                    f"DRY RUN: {rec['campaign_name']} - {rec['action']} "
                    f"(${rec['current_budget']:.2f} → ${rec['new_budget']:.2f}): {rec['reason']}"
                )
        
        return self.create_result(
            job_input,
            ok=True,
            metrics={
                "dry_run": 1,
                "campaigns_analyzed": len(recommendations),
                **changes_summary,
            },
            notes=[
                "Dry run completed successfully",
                f"Would increase {changes_summary['increases']} campaign budgets",
                f"Would decrease {changes_summary['decreases']} campaign budgets", 
                f"Would pause {changes_summary['paused']} campaigns",
                f"{changes_summary['no_change']} campaigns require no changes",
            ],
        )
    
    async def _apply_budget_changes(self, recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Apply budget changes via provider APIs."""
        
        results = {
            "increases": 0,
            "decreases": 0,
            "paused": 0,
            "total_changes": 0,
        }
        
        for rec in recommendations:
            if rec["action"] == "no_change":
                continue
            
            # TODO: Implement actual API calls to update budgets
            # This would call Google Ads API, Reddit API, X API based on platform
            
            success = await self._update_campaign_budget(
                rec["platform"],
                rec["campaign_id"],
                rec["new_budget"],
                rec["action"] == "pause_campaign"
            )
            
            if success:
                if rec["action"] == "increase_budget":
                    results["increases"] += 1
                elif rec["action"] == "decrease_budget":
                    results["decreases"] += 1
                elif rec["action"] == "pause_campaign":
                    results["paused"] += 1
                
                results["total_changes"] += 1
                
                self.logger.info(
                    f"Updated {rec['campaign_name']}: {rec['action']} "
                    f"(${rec['current_budget']:.2f} → ${rec['new_budget']:.2f})"
                )
        
        return results
    
    async def _update_campaign_budget(
        self, platform: str, campaign_id: str, new_budget: float, pause: bool
    ) -> bool:
        """Update campaign budget via platform API."""
        
        # TODO: Implement actual API calls
        # For Google Ads: Update campaign budget and status
        # For Reddit/X: Update campaign daily budget
        
        self.logger.info(f"Updating {platform} campaign {campaign_id} budget to ${new_budget:.2f}")
        return True  # Mock success


class KeywordsHydratorAgent(DecisionAgent):
    """Hydrates keyword data from external sources."""
    
    def __init__(self, agent_name: str = "keywords-hydrator"):
        super().__init__(agent_name)
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Pull keyword metrics from external APIs and store in keywords_external."""
        
        try:
            self.logger.info("Starting keyword hydration")
            
            # Get seed keywords for expansion
            seed_keywords = await self._get_seed_keywords()
            
            if not seed_keywords:
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={"keywords_processed": 0},
                    notes=["No seed keywords found for hydration"],
                )
            
            if job_input.dry_run:
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={"dry_run": 1, "keywords_would_process": len(seed_keywords)},
                    notes=["Dry run completed successfully"],
                )
            
            # Batch API calls (≤100 keywords per request)
            keyword_data = await self._batch_keyword_api_calls(seed_keywords)
            
            # Upsert to keywords_external table
            records_written = await self._upsert_keyword_data(keyword_data)
            
            return self.create_result(
                job_input,
                ok=True,
                metrics={
                    "seed_keywords": len(seed_keywords),
                    "keywords_enriched": len(keyword_data),
                    "records_written": records_written,
                },
                records_written=records_written,
                notes=[f"Enriched {len(keyword_data)} keywords from {len(seed_keywords)} seeds"],
            )
            
        except Exception as e:
            self.logger.exception("Failed to hydrate keywords")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _get_seed_keywords(self) -> List[str]:
        """Get seed keywords for expansion."""
        
        # TODO: Get from actual keyword database or config
        return [
            "code search",
            "sourcegraph",
            "developer tools",
            "code intelligence",
            "AI code assistant",
        ]
    
    async def _batch_keyword_api_calls(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Make batched API calls to keyword research tool."""
        
        # TODO: Implement actual keyword research API (e.g., SEMrush, Ahrefs, etc.)
        # This would make ≤100 keywords per batch request
        
        # Mock keyword data
        keyword_data = []
        for keyword in keywords:
            keyword_data.append({
                "keyword": keyword,
                "monthly_volume": 1000 + hash(keyword) % 50000,
                "est_cpc": 2.50 + (hash(keyword) % 500) / 100,
                "competition": ["low", "medium", "high"][hash(keyword) % 3],
                "source": "mock_ke_api",
                "pulled_at": datetime.now().isoformat(),
            })
        
        return keyword_data
    
    async def _upsert_keyword_data(self, keyword_data: List[Dict[str, Any]]) -> int:
        """Upsert keyword data to keywords_external table."""
        
        # TODO: Implement database upsert
        self.logger.info(f"Would upsert {len(keyword_data)} keyword records")
        return len(keyword_data)


# Register decision agents
agent_registry.register("budget-optimizer", BudgetOptimizerAgent)
agent_registry.register("keywords-hydrator", KeywordsHydratorAgent)
