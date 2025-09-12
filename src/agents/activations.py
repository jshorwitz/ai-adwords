"""Activation agents for conversion uploads and external API interactions."""

import logging
from datetime import datetime
from typing import Any, Dict, List

from .base import ActivationAgent, AgentJobInput, AgentResult
from .runner import agent_registry

logger = logging.getLogger(__name__)


class ConversionUploaderAgent(ActivationAgent):
    """Sends server-side conversions back to ad platforms."""
    
    def __init__(self, agent_name: str = "conversion-uploader"):
        super().__init__(agent_name)
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Upload conversions to Google Ads, Reddit CAPI, and X CAPI."""
        
        try:
            self.logger.info("Starting conversion upload process")
            
            # Get new conversions since last watermark
            conversions = await self._fetch_new_conversions()
            
            if not conversions:
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={"conversions_processed": 0},
                    notes=["No new conversions to upload"],
                )
            
            if job_input.dry_run:
                return await self._dry_run_upload(job_input, conversions)
            
            # Upload to each platform
            results = await self._upload_to_platforms(conversions)
            
            # Update watermark
            await self._update_watermark()
            
            total_uploaded = sum(r["uploaded"] for r in results.values())
            
            return self.create_result(
                job_input,
                ok=True,
                metrics={
                    "conversions_fetched": len(conversions),
                    "google_uploaded": results.get("google", {}).get("uploaded", 0),
                    "reddit_uploaded": results.get("reddit", {}).get("uploaded", 0),
                    "x_uploaded": results.get("x", {}).get("uploaded", 0),
                    "total_uploaded": total_uploaded,
                },
                records_written=total_uploaded,
                notes=[
                    f"Uploaded {total_uploaded} conversions across platforms",
                    f"Google: {results.get('google', {}).get('uploaded', 0)}",
                    f"Reddit: {results.get('reddit', {}).get('uploaded', 0)}",
                    f"X: {results.get('x', {}).get('uploaded', 0)}",
                ],
            )
            
        except Exception as e:
            self.logger.exception("Failed to upload conversions")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _fetch_new_conversions(self) -> List[Dict[str, Any]]:
        """Fetch new conversions since last watermark."""
        
        # TODO: Implement actual database query
        # This would query the conversions table for new records
        
        # Mock conversions with different platform click IDs
        mock_conversions = [
            {
                "id": "conv_123",
                "user_id": "user_123",
                "conversion_name": "purchase",
                "conversion_value": 99.99,
                "conversion_time": "2025-01-10T10:30:00Z",
                "gclid": "abc123gclid",
                "platform_source": "google",
            },
            {
                "id": "conv_456", 
                "user_id": "user_456",
                "conversion_name": "signup",
                "conversion_value": 0,
                "conversion_time": "2025-01-10T11:15:00Z",
                "rdt_cid": "reddit_click_456",
                "platform_source": "reddit",
            },
            {
                "id": "conv_789",
                "user_id": "user_789",
                "conversion_name": "purchase",
                "conversion_value": 149.99,
                "conversion_time": "2025-01-10T12:00:00Z",
                "twclid": "twitter_click_789", 
                "platform_source": "x",
            },
        ]
        
        self.logger.info(f"Fetched {len(mock_conversions)} new conversions")
        return mock_conversions
    
    async def _dry_run_upload(
        self, job_input: AgentJobInput, conversions: List[Dict[str, Any]]
    ) -> AgentResult:
        """Simulate conversion upload in dry run mode."""
        
        # Group by platform
        platform_counts = {}
        for conv in conversions:
            platform = conv.get("platform_source", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        upload_payloads = []
        for conv in conversions:
            payload = self._create_upload_payload(conv)
            upload_payloads.append(payload)
        
        self.logger.info(f"DRY RUN: Would upload {len(conversions)} conversions")
        for platform, count in platform_counts.items():
            self.logger.info(f"DRY RUN: {platform}: {count} conversions")
        
        return self.create_result(
            job_input,
            ok=True,
            metrics={
                "dry_run": 1,
                "conversions_would_upload": len(conversions),
                **{f"{platform}_would_upload": count for platform, count in platform_counts.items()},
            },
            notes=[
                "Dry run completed successfully",
                f"Would upload {len(conversions)} conversions",
                *[f"{platform}: {count} conversions" for platform, count in platform_counts.items()],
            ],
        )
    
    async def _upload_to_platforms(self, conversions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Upload conversions to all platforms."""
        
        results = {}
        
        # Group conversions by platform
        google_conversions = [c for c in conversions if c.get("gclid") or c.get("gbraid") or c.get("wbraid")]
        reddit_conversions = [c for c in conversions if c.get("rdt_cid")]
        x_conversions = [c for c in conversions if c.get("twclid")]
        
        # Upload to Google Ads
        if google_conversions:
            results["google"] = await self._upload_to_google(google_conversions)
        
        # Upload to Reddit CAPI
        if reddit_conversions:
            results["reddit"] = await self._upload_to_reddit(reddit_conversions)
        
        # Upload to X CAPI
        if x_conversions:
            results["x"] = await self._upload_to_x(x_conversions)
        
        return results
    
    async def _upload_to_google(self, conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload conversions to Google Ads Enhanced Conversions."""
        
        # TODO: Implement Google Ads Enhanced Conversions API
        
        self.logger.info(f"Uploading {len(conversions)} conversions to Google Ads")
        
        # Mock upload response
        return {
            "uploaded": len(conversions),
            "failed": 0,
            "errors": [],
        }
    
    async def _upload_to_reddit(self, conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload conversions to Reddit Conversions API."""
        
        # TODO: Implement Reddit CAPI
        
        self.logger.info(f"Uploading {len(conversions)} conversions to Reddit CAPI")
        
        # Mock upload response
        return {
            "uploaded": len(conversions),
            "failed": 0,
            "errors": [],
        }
    
    async def _upload_to_x(self, conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload conversions to X Conversions API."""
        
        # TODO: Implement X CAPI
        
        self.logger.info(f"Uploading {len(conversions)} conversions to X CAPI")
        
        # Mock upload response  
        return {
            "uploaded": len(conversions),
            "failed": 0,
            "errors": [],
        }
    
    def _create_upload_payload(self, conversion: Dict[str, Any]) -> Dict[str, Any]:
        """Create platform-specific upload payload."""
        
        return {
            "conversion_name": conversion.get("conversion_name"),
            "conversion_value": conversion.get("conversion_value"),
            "conversion_time": conversion.get("conversion_time"),
            "click_id": (
                conversion.get("gclid") or
                conversion.get("gbraid") or
                conversion.get("wbraid") or
                conversion.get("rdt_cid") or
                conversion.get("twclid")
            ),
            "user_id": conversion.get("user_id"),
        }
    
    async def _update_watermark(self):
        """Update the conversion upload watermark."""
        
        # TODO: Implement watermark update in agent_runs table
        self.logger.info("Updated conversion upload watermark")


# Register activation agents
agent_registry.register("conversion-uploader", ConversionUploaderAgent)
