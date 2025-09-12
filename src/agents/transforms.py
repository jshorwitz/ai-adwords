"""Transform agents for touchpoint extraction and data processing."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base import TransformAgent, AgentJobInput, AgentResult
from .runner import agent_registry

logger = logging.getLogger(__name__)


class TouchpointExtractorAgent(TransformAgent):
    """Derives click/landing touchpoints from events (PostHog) → touchpoints."""
    
    def __init__(self, agent_name: str = "touchpoint-extractor"):
        super().__init__(agent_name)
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Extract touchpoints from recent events."""
        
        try:
            self.logger.info("Extracting touchpoints from events")
            
            if job_input.dry_run:
                self.logger.info("DRY RUN: Would extract touchpoints from events")
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={"dry_run": 1, "touchpoints_would_extract": 50},
                    notes=["Dry run completed successfully"],
                )
            
            # Get recent events with click IDs or UTM parameters
            events = await self._fetch_recent_events()
            
            # Process events to extract touchpoints
            touchpoints = await self._extract_touchpoints(events)
            
            # Upsert to touchpoints table
            records_written = await self._upsert_touchpoints(touchpoints)
            
            return self.create_result(
                job_input,
                ok=True,
                metrics={
                    "events_processed": len(events),
                    "touchpoints_extracted": len(touchpoints),
                    "records_written": records_written,
                },
                records_written=records_written,
                notes=[f"Processed {len(events)} events, extracted {len(touchpoints)} touchpoints"],
            )
            
        except Exception as e:
            self.logger.exception("Failed to extract touchpoints")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _fetch_recent_events(self) -> List[Dict[str, Any]]:
        """Fetch recent events from PostHog or events table."""
        
        # TODO: Implement actual PostHog API or database query
        # For now, return mock events with click IDs
        
        mock_events = [
            {
                "user_id": "user_123",
                "event": "page_view",
                "timestamp": datetime.now().isoformat(),
                "properties": {
                    "gclid": "abc123gclid",
                    "utm_source": "google",
                    "utm_campaign": "brand_campaign",
                    "url": "https://example.com/landing",
                }
            },
            {
                "user_id": "user_456",
                "event": "page_view", 
                "timestamp": datetime.now().isoformat(),
                "properties": {
                    "rdt_cid": "reddit_click_456",
                    "utm_source": "reddit",
                    "utm_campaign": "awareness_campaign",
                    "url": "https://example.com/signup",
                }
            },
            {
                "user_id": "user_789",
                "event": "page_view",
                "timestamp": datetime.now().isoformat(),
                "properties": {
                    "twclid": "twitter_click_789",
                    "utm_source": "twitter",
                    "utm_campaign": "social_campaign", 
                    "url": "https://example.com/product",
                }
            },
        ]
        
        self.logger.info(f"Fetched {len(mock_events)} events")
        return mock_events
    
    async def _extract_touchpoints(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract touchpoints from events based on click IDs and UTM params."""
        
        touchpoints = []
        
        for event in events:
            props = event.get("properties", {})
            
            # Determine platform from click IDs (in priority order)
            platform = "other"
            click_id = None
            
            if props.get("gclid"):
                platform = "google"
                click_id = props["gclid"]
            elif props.get("gbraid"):
                platform = "google"
                click_id = props["gbraid"]
            elif props.get("wbraid"):
                platform = "google"
                click_id = props["wbraid"]
            elif props.get("rdt_cid"):
                platform = "reddit"
                click_id = props["rdt_cid"]
            elif props.get("twclid"):
                platform = "x"
                click_id = props["twclid"]
            elif props.get("utm_source"):
                # Fallback to UTM source
                utm_source = props["utm_source"].lower()
                if utm_source in ["google", "googleads"]:
                    platform = "google"
                elif utm_source == "reddit":
                    platform = "reddit"
                elif utm_source in ["twitter", "x"]:
                    platform = "x"
            
            touchpoint = {
                "user_id": event["user_id"],
                "timestamp": event["timestamp"],
                "platform": platform,
                "click_id": click_id,
                "campaign": props.get("utm_campaign"),
                "source": props.get("utm_source"),
                "medium": props.get("utm_medium"),
                "landing_url": props.get("url"),
                "event_type": event["event"],
                "raw_properties": props,
                "extracted_at": datetime.now().isoformat(),
            }
            
            touchpoints.append(touchpoint)
        
        return touchpoints
    
    async def _upsert_touchpoints(self, touchpoints: List[Dict[str, Any]]) -> int:
        """Upsert touchpoints to database with deduplication."""
        
        # TODO: Implement actual database upsert
        # De-dupe by (user_id, timestamp, platform, campaign)
        
        self.logger.info(f"Would upsert {len(touchpoints)} touchpoints")
        return len(touchpoints)


# Register transform agents
agent_registry.register("touchpoint-extractor", TouchpointExtractorAgent)
