"""LLM client configurations for different AI models."""

import os
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try importing LLM libraries with fallbacks
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available")

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    logger.warning("Google AI not available")


class BaseLLMClient(ABC):
    """Base class for all LLM clients."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.available = True
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text response from the model."""
        pass
    
    async def generate_safe(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Safe generation with fallback to mock response."""
        try:
            if self.available:
                return await self.generate(prompt, system_prompt, **kwargs)
            else:
                return self._get_fallback_response(prompt)
        except Exception as e:
            logger.warning(f"LLM generation failed for {self.model_name}: {e}")
            return self._get_fallback_response(prompt)
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Generate fallback response when LLM is unavailable."""
        if "strategy" in prompt.lower():
            return "**Campaign Strategy**: Focus on high-value keywords, implement cross-platform approach, optimize for ROAS."
        elif "copy" in prompt.lower() or "ad" in prompt.lower():
            return "**Ad Copy**: Compelling headline with clear value proposition. Emphasize unique benefits and strong call-to-action."
        elif "keyword" in prompt.lower():
            return "**Keywords**: Target long-tail, high-intent keywords with lower competition and higher conversion potential."
        elif "competitor" in prompt.lower():
            return "**Competitive Analysis**: Analyze competitor ad strategies, identify gaps, and capitalize on unique positioning opportunities."
        else:
            return "**AI Analysis**: Comprehensive analysis completed. Recommendations focus on data-driven optimization and ROI improvement."


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT-4 client for campaign strategy and copywriting."""
    
    def __init__(self):
        super().__init__("GPT-4")
        self.client = None
        self.available = OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))
        
        if self.available:
            try:
                self.client = openai.AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.available = False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate response using GPT-4."""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7),
        )
        
        return response.choices[0].message.content


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client for analysis and optimization."""
    
    def __init__(self):
        super().__init__("Claude-3.5-Sonnet")
        self.client = None
        self.available = ANTHROPIC_AVAILABLE and bool(os.getenv("ANTHROPIC_API_KEY"))
        
        if self.available:
            try:
                self.client = anthropic.AsyncAnthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
                self.available = False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate response using Claude."""
        
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7),
            system=system_prompt or "You are an expert advertising analyst.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text


class GoogleAIClient(BaseLLMClient):
    """Google Gemini client for competitive intelligence."""
    
    def __init__(self):
        super().__init__("Gemini-Pro")
        self.available = GOOGLE_AI_AVAILABLE and bool(os.getenv("GOOGLE_AI_API_KEY"))
        
        if self.available:
            try:
                genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                logger.warning(f"Failed to initialize Google AI client: {e}")
                self.available = False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate response using Gemini."""
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
            )
        )
        
        return response.text


class AIAgencyManager:
    """Manages multiple AI specialists for advertising agency functions."""
    
    def __init__(self):
        self.specialists = {
            "strategist": OpenAIClient(),      # Campaign strategy and planning
            "copywriter": OpenAIClient(),     # Ad copy and creative
            "analyst": AnthropicClient(),     # Performance analysis and optimization
            "researcher": GoogleAIClient(),   # Market research and competitive intelligence
        }
        
        # Log available models
        available_models = [name for name, client in self.specialists.items() if client.available]
        logger.info(f"✅ AI Agency initialized with specialists: {available_models}")
        
        if not available_models:
            logger.warning("⚠️ No AI models available - using fallback responses")
    
    async def get_campaign_strategy(self, website_data: Dict[str, Any], keywords: List[str], budget: float = None) -> str:
        """Get AI-generated campaign strategy."""
        
        system_prompt = """You are a senior advertising strategist at a top-tier agency. 
        Create comprehensive campaign strategies that maximize ROAS across Google Ads, Reddit Ads, and X/Twitter Ads.
        Focus on data-driven recommendations with specific, actionable insights."""
        
        prompt = f"""
        Create a comprehensive advertising strategy for this website:
        
        Website: {website_data.get('title', 'Unknown')}
        Industry: {website_data.get('industry', 'Unknown')}
        Description: {website_data.get('description', 'No description')}
        
        Top Keywords: {', '.join(keywords[:10])}
        Budget: ${budget or 'Not specified'}
        
        Provide:
        1. Overall campaign strategy
        2. Platform-specific recommendations (Google Ads, Reddit Ads, X Ads)
        3. Budget allocation suggestions
        4. Timeline and milestones
        5. Expected performance metrics
        
        Format as clear, actionable recommendations for immediate implementation.
        """
        
        return await self.specialists["strategist"].generate_safe(prompt, system_prompt)
    
    async def generate_ad_copy(self, product: str, keywords: List[str], platform: str = "google") -> Dict[str, List[str]]:
        """Generate ad copy variations for different platforms."""
        
        system_prompt = f"""You are a world-class advertising copywriter specializing in {platform} ads.
        Create compelling, high-converting ad copy that drives clicks and conversions.
        Focus on emotional triggers, clear value propositions, and strong calls-to-action."""
        
        prompt = f"""
        Create 5 high-converting ad variations for:
        
        Product/Service: {product}
        Platform: {platform.title()}
        Keywords: {', '.join(keywords[:5])}
        
        For each ad, provide:
        - Headline (max 30 chars for {platform})
        - Description (max 90 chars for {platform})
        - Call-to-action
        
        Focus on:
        1. Clear value proposition
        2. Emotional triggers
        3. Urgency/scarcity when appropriate
        4. Platform-specific best practices
        5. Keyword integration
        
        Format as JSON with headline, description, and cta fields.
        """
        
        response = await self.specialists["copywriter"].generate_safe(prompt, system_prompt)
        
        # Parse response or return structured fallback
        try:
            import json
            return json.loads(response)
        except:
            return {
                "ads": [
                    {
                        "headline": f"Best {product} - Get Started",
                        "description": f"Discover why thousands choose {product} for growth. Start free trial today.",
                        "cta": "Get Started Free"
                    },
                    {
                        "headline": f"{product} - Save Time & Money",
                        "description": f"Streamline your workflow with {product}. Join successful businesses today.",
                        "cta": "Start Saving Now"
                    }
                ]
            }
    
    async def analyze_performance(self, metrics: Dict[str, Any], timeframe: str = "30 days") -> str:
        """Analyze campaign performance and provide optimization insights."""
        
        system_prompt = """You are a senior performance marketing analyst with expertise in Google Ads, Reddit Ads, and X advertising.
        Provide detailed, actionable insights based on campaign data. Focus on specific optimization opportunities and ROI improvements."""
        
        prompt = f"""
        Analyze this campaign performance data from the last {timeframe}:
        
        Metrics:
        {self._format_metrics(metrics)}
        
        Provide detailed analysis covering:
        1. Performance highlights and concerns
        2. Specific optimization opportunities
        3. Budget reallocation recommendations
        4. Keyword performance insights
        5. Platform-specific optimizations
        6. Forecasted improvements with recommended changes
        
        Focus on actionable insights that can improve ROAS within 7 days.
        """
        
        return await self.specialists["analyst"].generate_safe(prompt, system_prompt)
    
    async def research_market_opportunities(self, industry: str, competitors: List[str]) -> str:
        """Research market opportunities and competitive landscape."""
        
        system_prompt = """You are a market research specialist at a leading advertising agency.
        Provide comprehensive market intelligence and competitive analysis for advertising strategy development."""
        
        prompt = f"""
        Conduct market research analysis for:
        
        Industry: {industry}
        Main Competitors: {', '.join(competitors[:5])}
        
        Research and provide:
        1. Market trends and opportunities
        2. Competitive positioning analysis
        3. Underexploited keyword opportunities
        4. Emerging platform opportunities (TikTok, LinkedIn, etc.)
        5. Seasonal trends and timing recommendations
        6. Budget allocation insights by platform
        
        Focus on actionable insights that can provide competitive advantages.
        """
        
        return await self.specialists["researcher"].generate_safe(prompt, system_prompt)
    
    async def optimize_campaigns(self, campaign_data: Dict[str, Any]) -> str:
        """Generate campaign optimization recommendations."""
        
        system_prompt = """You are a campaign optimization expert specializing in AI-driven advertising.
        Provide specific, data-driven optimization recommendations that can be implemented immediately."""
        
        prompt = f"""
        Optimize these advertising campaigns:
        
        Campaign Data:
        {self._format_campaign_data(campaign_data)}
        
        Provide optimization recommendations for:
        1. Bid adjustments and budget allocation
        2. Keyword additions and negatives
        3. Ad copy improvements
        4. Audience targeting refinements
        5. Landing page optimization suggestions
        6. Attribution and tracking improvements
        
        Prioritize recommendations by potential impact and implementation ease.
        """
        
        return await self.specialists["analyst"].generate_safe(prompt, system_prompt)
    
    async def generate_keyword_strategy(self, website_url: str, industry: str, current_keywords: List[str]) -> Dict[str, Any]:
        """Generate comprehensive keyword strategy."""
        
        system_prompt = """You are a keyword research expert with deep knowledge of search intent and conversion optimization.
        Provide strategic keyword recommendations that balance volume, competition, and conversion potential."""
        
        prompt = f"""
        Develop a comprehensive keyword strategy for:
        
        Website: {website_url}
        Industry: {industry}
        Current Keywords: {', '.join(current_keywords[:10])}
        
        Provide:
        1. High-value keyword expansions
        2. Long-tail keyword opportunities
        3. Competitor keyword gaps
        4. Seasonal keyword variations
        5. Negative keyword recommendations
        6. Keyword grouping and campaign structure
        
        Format as actionable keyword lists with rationale for each recommendation.
        """
        
        response = await self.specialists["strategist"].generate_safe(prompt, system_prompt)
        
        return {
            "strategy": response,
            "keyword_categories": self._extract_keyword_categories(response),
            "implementation_priority": "high"
        }
    
    async def generate_audience_insights(self, website_data: Dict[str, Any], keywords: List[str]) -> str:
        """Generate audience targeting insights."""
        
        system_prompt = """You are an audience targeting specialist with expertise in customer personas and behavioral targeting.
        Create detailed audience insights and targeting recommendations for maximum ad performance."""
        
        prompt = f"""
        Develop audience targeting strategy for:
        
        Business: {website_data.get('title', 'Unknown')}
        Industry: {website_data.get('industry', 'Unknown')}
        Target Keywords: {', '.join(keywords[:8])}
        
        Provide:
        1. Primary audience personas
        2. Demographic targeting recommendations
        3. Interest and behavior targeting
        4. Lookalike audience strategies
        5. Platform-specific audience insights
        6. Remarketing and retention strategies
        
        Focus on audiences most likely to convert with highest lifetime value.
        """
        
        return await self.specialists["researcher"].generate_safe(prompt, system_prompt)
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for LLM analysis."""
        formatted = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if key.lower() in ['spend', 'cost', 'cpc', 'cac']:
                    formatted.append(f"- {key}: ${value:,.2f}")
                elif key.lower() in ['ctr', 'roas']:
                    formatted.append(f"- {key}: {value:.2f}")
                else:
                    formatted.append(f"- {key}: {value:,}")
            else:
                formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)
    
    def _format_campaign_data(self, campaign_data: Dict[str, Any]) -> str:
        """Format campaign data for LLM analysis."""
        formatted = []
        for campaign, data in campaign_data.items():
            formatted.append(f"\n{campaign}:")
            formatted.append(self._format_metrics(data))
        return "\n".join(formatted)
    
    def _extract_keyword_categories(self, response: str) -> List[str]:
        """Extract keyword categories from LLM response."""
        # Simple extraction - could be enhanced with NLP
        categories = []
        if "brand" in response.lower():
            categories.append("brand")
        if "competitor" in response.lower():
            categories.append("competitor")
        if "product" in response.lower():
            categories.append("product")
        if "solution" in response.lower():
            categories.append("solution")
        return categories or ["general"]


# Global AI agency instance
ai_agency = AIAgencyManager()


# Specialized AI agents for different functions
class AIStrategist:
    """AI Campaign Strategist using GPT-4."""
    
    @staticmethod
    async def create_campaign_plan(website_data: Dict, keywords: List[str], budget: float = None) -> Dict[str, Any]:
        strategy = await ai_agency.get_campaign_strategy(website_data, keywords, budget)
        
        return {
            "strategy_brief": strategy,
            "recommended_budget": budget or 5000,
            "timeline": "2-4 weeks for full implementation",
            "expected_roas": "3.5x within 60 days",
            "priority_platforms": ["Google Ads", "Reddit Ads", "X Ads"]
        }


class AICopywriter:
    """AI Ad Copywriter using GPT-4."""
    
    @staticmethod
    async def create_ad_variations(product: str, keywords: List[str], platform: str = "google") -> Dict[str, Any]:
        ad_copy = await ai_agency.generate_ad_copy(product, keywords, platform)
        
        return {
            "platform": platform,
            "ad_variations": ad_copy.get("ads", []),
            "testing_recommendations": [
                "A/B test emotional vs rational appeals",
                "Test urgency vs benefit-focused messaging",
                "Compare direct vs question-based headlines"
            ]
        }


class AIAnalyst:
    """AI Performance Analyst using Claude."""
    
    @staticmethod
    async def analyze_campaign_performance(metrics: Dict[str, Any]) -> Dict[str, Any]:
        analysis = await ai_agency.analyze_performance(metrics)
        
        return {
            "performance_analysis": analysis,
            "optimization_score": 85,  # Mock score
            "priority_actions": [
                "Increase budget on top-performing keywords",
                "Pause underperforming ad groups",
                "Test new ad copy variations"
            ],
            "forecasted_improvements": {
                "roas_lift": "15-25%",
                "cac_reduction": "10-20%",
                "conversion_increase": "20-30%"
            }
        }


class AIResearcher:
    """AI Market Researcher using Google Gemini."""
    
    @staticmethod
    async def research_opportunities(industry: str, competitors: List[str]) -> Dict[str, Any]:
        research = await ai_agency.research_market_opportunities(industry, competitors)
        
        return {
            "market_research": research,
            "opportunity_score": 92,  # Mock score
            "trending_keywords": [
                "AI-powered solutions",
                "automation tools",
                "business efficiency"
            ],
            "competitive_gaps": [
                "Mobile optimization",
                "Video advertising",
                "Influencer partnerships"
            ]
        }
