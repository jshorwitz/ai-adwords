"""Data source integrations for real advertising intelligence."""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """Configuration for external data sources."""
    name: str
    api_key: Optional[str]
    base_url: str
    available: bool
    capabilities: List[str]
    cost_per_request: float = 0.0


class DataSourceManager:
    """Manages all external data sources for advertising intelligence."""
    
    def __init__(self):
        self.sources = self.initialize_data_sources()
        self.log_available_sources()
    
    def initialize_data_sources(self) -> Dict[str, DataSourceConfig]:
        """Initialize all available data sources."""
        
        sources = {
            # Ad Intelligence Platforms
            'semrush': DataSourceConfig(
                name="SEMrush",
                api_key=os.getenv('SEMRUSH_API_KEY'),
                base_url="https://api.semrush.com/",
                available=bool(os.getenv('SEMRUSH_API_KEY')),
                capabilities=["keyword_research", "competitor_ads", "traffic_analysis", "backlink_analysis"],
                cost_per_request=0.10
            ),
            
            'ahrefs': DataSourceConfig(
                name="Ahrefs",
                api_key=os.getenv('AHREFS_API_KEY'),
                base_url="https://apiv2.ahrefs.com/",
                available=bool(os.getenv('AHREFS_API_KEY')),
                capabilities=["keyword_research", "competitor_analysis", "content_analysis"],
                cost_per_request=0.15
            ),
            
            'spyfu': DataSourceConfig(
                name="SpyFu",
                api_key=os.getenv('SPYFU_API_KEY'),
                base_url="https://www.spyfu.com/apis/",
                available=bool(os.getenv('SPYFU_API_KEY')),
                capabilities=["competitor_ads", "keyword_history", "ad_copy_analysis"],
                cost_per_request=0.08
            ),
            
            # Platform APIs
            'google_ads': DataSourceConfig(
                name="Google Ads API",
                api_key=os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN'),
                base_url="https://googleads.googleapis.com/",
                available=bool(os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')),
                capabilities=["campaign_data", "keyword_performance", "ad_performance", "audience_insights"]
            ),
            
            'facebook_ads': DataSourceConfig(
                name="Facebook Ads API",
                api_key=os.getenv('FACEBOOK_ACCESS_TOKEN'),
                base_url="https://graph.facebook.com/",
                available=bool(os.getenv('FACEBOOK_ACCESS_TOKEN')),
                capabilities=["campaign_data", "ad_creative", "audience_insights"]
            ),
            
            'reddit_ads': DataSourceConfig(
                name="Reddit Ads API",
                api_key=os.getenv('REDDIT_CLIENT_ID'),
                base_url="https://ads-api.reddit.com/",
                available=bool(os.getenv('REDDIT_CLIENT_ID')),
                capabilities=["campaign_data", "targeting_options", "performance_metrics"]
            ),
            
            'x_ads': DataSourceConfig(
                name="X Ads API",
                api_key=os.getenv('TWITTER_API_KEY'),
                base_url="https://ads-api-sandbox.twitter.com/",
                available=bool(os.getenv('TWITTER_API_KEY')),
                capabilities=["campaign_data", "promoted_tweets", "audience_insights"]
            ),
            
            # Analytics Platforms
            'google_analytics': DataSourceConfig(
                name="Google Analytics 4",
                api_key=os.getenv('GA4_PROPERTY_ID'),
                base_url="https://analyticsdata.googleapis.com/",
                available=bool(os.getenv('GA4_PROPERTY_ID')),
                capabilities=["traffic_analysis", "conversion_tracking", "attribution_analysis"]
            ),
            
            'google_search_console': DataSourceConfig(
                name="Google Search Console",
                api_key=os.getenv('GSC_PROPERTY_URL'),
                base_url="https://searchconsole.googleapis.com/",
                available=bool(os.getenv('GSC_PROPERTY_URL')),
                capabilities=["organic_keywords", "search_performance", "technical_seo"]
            ),
            
            # Public APIs
            'facebook_ads_library': DataSourceConfig(
                name="Facebook Ads Library",
                api_key="public",
                base_url="https://graph.facebook.com/",
                available=True,
                capabilities=["public_ads", "political_ads", "competitor_creatives"]
            ),
            
            'google_trends': DataSourceConfig(
                name="Google Trends",
                api_key="public",
                base_url="https://trends.google.com/",
                available=True,
                capabilities=["keyword_trends", "seasonal_patterns", "geographic_insights"]
            ),
            
            # Third-party Intelligence
            'similar_web': DataSourceConfig(
                name="SimilarWeb",
                api_key=os.getenv('SIMILARWEB_API_KEY'),
                base_url="https://api.similarweb.com/",
                available=bool(os.getenv('SIMILARWEB_API_KEY')),
                capabilities=["traffic_analysis", "competitor_intelligence", "market_research"]
            ),
            
            'builtwith': DataSourceConfig(
                name="BuiltWith",
                api_key=os.getenv('BUILTWITH_API_KEY'),
                base_url="https://api.builtwith.com/",
                available=bool(os.getenv('BUILTWITH_API_KEY')),
                capabilities=["technology_detection", "competitor_tech_stack", "market_trends"]
            )
        }
        
        return sources
    
    def log_available_sources(self):
        """Log available data sources."""
        
        available = [source.name for source in self.sources.values() if source.available]
        unavailable = [source.name for source in self.sources.values() if not source.available]
        
        logger.info(f"✅ Available data sources ({len(available)}): {', '.join(available)}")
        if unavailable:
            logger.info(f"⚠️ Unavailable data sources ({len(unavailable)}): {', '.join(unavailable)}")
    
    def get_available_capabilities(self) -> List[str]:
        """Get all available capabilities across data sources."""
        
        capabilities = set()
        for source in self.sources.values():
            if source.available:
                capabilities.update(source.capabilities)
        
        return sorted(list(capabilities))
    
    def get_source_for_capability(self, capability: str) -> Optional[DataSourceConfig]:
        """Get the best data source for a specific capability."""
        
        available_sources = [
            source for source in self.sources.values() 
            if source.available and capability in source.capabilities
        ]
        
        if not available_sources:
            return None
        
        # Return cheapest available source
        return min(available_sources, key=lambda x: x.cost_per_request)
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all data sources."""
        
        return {
            'total_sources': len(self.sources),
            'available_sources': len([s for s in self.sources.values() if s.available]),
            'capabilities': self.get_available_capabilities(),
            'sources': {
                name: {
                    'available': source.available,
                    'capabilities': source.capabilities,
                    'cost_per_request': source.cost_per_request
                }
                for name, source in self.sources.items()
            },
            'recommendations': self.get_setup_recommendations()
        }
    
    def get_setup_recommendations(self) -> List[str]:
        """Get recommendations for improving data source coverage."""
        
        recommendations = []
        
        if not self.sources['google_ads'].available:
            recommendations.append("Connect Google Ads API for real campaign data and optimization")
        
        if not self.sources['semrush'].available:
            recommendations.append("Add SEMrush API key for competitor keyword research")
        
        if not self.sources['facebook_ads'].available:
            recommendations.append("Connect Facebook Ads API for social media advertising data")
        
        if not self.sources['google_analytics'].available:
            recommendations.append("Connect Google Analytics 4 for conversion tracking and attribution")
        
        if len([s for s in self.sources.values() if s.available]) < 3:
            recommendations.append("Add more data sources for comprehensive advertising intelligence")
        
        return recommendations


# Global data source manager
data_sources = DataSourceManager()


# Configuration validation
def validate_environment_setup() -> Dict[str, Any]:
    """Validate that required environment variables are set."""
    
    required_for_production = {
        'GOOGLE_ADS_CLIENT_ID': 'Google Ads integration',
        'GOOGLE_ADS_CLIENT_SECRET': 'Google Ads integration',
        'GOOGLE_ADS_DEVELOPER_TOKEN': 'Google Ads API access',
        'OPENAI_API_KEY': 'AI strategy and copywriting',
        'ANTHROPIC_API_KEY': 'AI analysis and optimization'
    }
    
    optional_but_recommended = {
        'SEMRUSH_API_KEY': 'Competitor keyword research',
        'GOOGLE_AI_API_KEY': 'AI market research',
        'GA4_PROPERTY_ID': 'Conversion tracking',
        'FACEBOOK_ACCESS_TOKEN': 'Social media advertising data',
        'AHREFS_API_KEY': 'Advanced SEO and competitor analysis'
    }
    
    setup_status = {
        'required': {},
        'optional': {},
        'overall_score': 0,
        'recommendations': []
    }
    
    # Check required
    for key, description in required_for_production.items():
        is_set = bool(os.getenv(key))
        setup_status['required'][key] = {
            'configured': is_set,
            'description': description
        }
        if is_set:
            setup_status['overall_score'] += 15
    
    # Check optional
    for key, description in optional_but_recommended.items():
        is_set = bool(os.getenv(key))
        setup_status['optional'][key] = {
            'configured': is_set,
            'description': description
        }
        if is_set:
            setup_status['overall_score'] += 5
    
    # Generate recommendations
    missing_required = [k for k, v in setup_status['required'].items() if not v['configured']]
    if missing_required:
        setup_status['recommendations'].append(f"Add required API keys: {', '.join(missing_required)}")
    
    missing_optional = [k for k, v in setup_status['optional'].items() if not v['configured']]
    if len(missing_optional) > 3:
        setup_status['recommendations'].append("Consider adding optional API keys for enhanced functionality")
    
    if setup_status['overall_score'] >= 80:
        setup_status['status'] = 'Production Ready'
    elif setup_status['overall_score'] >= 50:
        setup_status['status'] = 'Partially Configured'
    else:
        setup_status['status'] = 'Demo Mode'
    
    return setup_status


if __name__ == "__main__":
    # Test data source configuration
    status = validate_environment_setup()
    print(f"Setup Status: {status['status']}")
    print(f"Overall Score: {status['overall_score']}/100")
    
    if status['recommendations']:
        print("Recommendations:")
        for rec in status['recommendations']:
            print(f"  - {rec}")
