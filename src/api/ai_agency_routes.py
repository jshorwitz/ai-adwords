"""AI Agency API endpoints - Multiple LLM specialists for advertising expertise."""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..ai_agency.llm_clients import (
    AIStrategist, AICopywriter, AIAnalyst, AIResearcher, ai_agency
)
from ..models.auth import User
from .middleware import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-agency", tags=["ai-agency"])


# Request/Response models
class StrategyRequest(BaseModel):
    website_data: Dict[str, Any]
    keywords: List[str]
    budget: Optional[float] = None
    goals: List[str] = []


class CopywritingRequest(BaseModel):
    product: str
    keywords: List[str]
    platform: str = "google"
    tone: str = "professional"
    target_audience: str = ""


class AnalysisRequest(BaseModel):
    metrics: Dict[str, Any]
    timeframe: str = "30 days"
    campaigns: List[Dict[str, Any]] = []


class ResearchRequest(BaseModel):
    industry: str
    competitors: List[str]
    website_url: str
    focus_areas: List[str] = []


class AISpecialistResponse(BaseModel):
    specialist: str
    response: Dict[str, Any]
    confidence_score: int
    processing_time: float


@router.post("/strategy", response_model=AISpecialistResponse)
async def get_campaign_strategy(
    request: StrategyRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get AI-generated campaign strategy from GPT-4 strategist."""
    
    try:
        import time
        start_time = time.time()
        
        logger.info("🧠 AI Strategist generating campaign plan...")
        
        # Generate strategy using AI Strategist
        strategy_result = await AIStrategist.create_campaign_plan(
            website_data=request.website_data,
            keywords=request.keywords,
            budget=request.budget
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Campaign strategy generated in {processing_time:.2f}s")
        
        return AISpecialistResponse(
            specialist="AI Strategist (GPT-4)",
            response=strategy_result,
            confidence_score=95,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.exception("AI strategy generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy generation failed: {str(e)}"
        )


@router.post("/copywriting", response_model=AISpecialistResponse)
async def generate_ad_copy(
    request: CopywritingRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Generate ad copy variations from GPT-4 copywriter."""
    
    try:
        import time
        start_time = time.time()
        
        logger.info(f"✍️ AI Copywriter creating {request.platform} ads...")
        
        # Generate ad copy using AI Copywriter
        copy_result = await AICopywriter.create_ad_variations(
            product=request.product,
            keywords=request.keywords,
            platform=request.platform
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Ad copy generated in {processing_time:.2f}s")
        
        return AISpecialistResponse(
            specialist="AI Copywriter (GPT-4)",
            response=copy_result,
            confidence_score=92,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.exception("AI copywriting failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copywriting failed: {str(e)}"
        )


@router.post("/analysis", response_model=AISpecialistResponse)
async def analyze_performance(
    request: AnalysisRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get performance analysis from Claude analyst."""
    
    try:
        import time
        start_time = time.time()
        
        logger.info("📊 AI Analyst reviewing performance data...")
        
        # Analyze performance using AI Analyst
        analysis_result = await AIAnalyst.analyze_campaign_performance(
            metrics=request.metrics
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Performance analysis completed in {processing_time:.2f}s")
        
        return AISpecialistResponse(
            specialist="AI Analyst (Claude)",
            response=analysis_result,
            confidence_score=88,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.exception("AI analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/research", response_model=AISpecialistResponse)
async def research_opportunities(
    request: ResearchRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get market research from Google Gemini researcher."""
    
    try:
        import time
        start_time = time.time()
        
        logger.info("🔍 AI Researcher analyzing market opportunities...")
        
        # Research opportunities using AI Researcher
        research_result = await AIResearcher.research_opportunities(
            industry=request.industry,
            competitors=request.competitors
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Market research completed in {processing_time:.2f}s")
        
        return AISpecialistResponse(
            specialist="AI Researcher (Gemini)",
            response=research_result,
            confidence_score=90,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.exception("AI research failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research failed: {str(e)}"
        )


@router.get("/specialists")
async def get_ai_specialists():
    """Get list of available AI specialists and their capabilities."""
    
    try:
        specialists_info = []
        
        for name, client in ai_agency.specialists.items():
            specialist_info = {
                "name": name.title(),
                "model": client.model_name,
                "available": client.available,
                "specialization": get_specialization(name),
                "capabilities": get_capabilities(name)
            }
            specialists_info.append(specialist_info)
        
        return {
            "ai_agency_status": "active",
            "specialists": specialists_info,
            "total_specialists": len(specialists_info),
            "available_specialists": len([s for s in specialists_info if s["available"]])
        }
        
    except Exception as e:
        logger.exception("Failed to get AI specialists info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get specialists info: {str(e)}"
        )


@router.post("/full-analysis")
async def run_full_agency_analysis(
    website_url: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Run complete AI agency analysis with all specialists."""
    
    try:
        import time
        start_time = time.time()
        
        logger.info("🏢 Running full AI agency analysis...")
        
        # Mock website data for demo
        website_data = {
            "title": "Business Website",
            "industry": "Technology",
            "description": "Innovative technology solutions"
        }
        
        keywords = ["technology", "software", "solution", "platform", "tool"]
        competitors = ["TechRival", "SoftwareLeader", "PlatformPro"]
        
        # Run all AI specialists in parallel
        import asyncio
        
        strategy_task = AIStrategist.create_campaign_plan(website_data, keywords, 10000)
        copy_task = AICopywriter.create_ad_variations("Technology Platform", keywords, "google")
        analysis_task = AIAnalyst.analyze_campaign_performance({"spend": 5000, "conversions": 25, "roas": 3.2})
        research_task = AIResearcher.research_opportunities("Technology", competitors)
        
        strategy_result, copy_result, analysis_result, research_result = await asyncio.gather(
            strategy_task, copy_task, analysis_task, research_task
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Full agency analysis completed in {processing_time:.2f}s")
        
        return {
            "analysis_complete": True,
            "processing_time": processing_time,
            "website_url": website_url,
            "specialists_used": 4,
            "results": {
                "strategy": strategy_result,
                "copywriting": copy_result,
                "analysis": analysis_result,
                "research": research_result
            },
            "next_steps": [
                "Connect ad accounts for implementation",
                "Set up conversion tracking",
                "Launch initial campaigns with AI recommendations",
                "Enable autonomous optimization agents"
            ]
        }
        
    except Exception as e:
        logger.exception("Full agency analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full analysis failed: {str(e)}"
        )


def get_specialization(specialist_name: str) -> str:
    """Get specialist's area of expertise."""
    specializations = {
        "strategist": "Campaign Strategy & Planning",
        "copywriter": "Ad Copy & Creative Development", 
        "analyst": "Performance Analysis & Optimization",
        "researcher": "Market Intelligence & Competitive Research"
    }
    return specializations.get(specialist_name, "General AI Assistant")


def get_capabilities(specialist_name: str) -> List[str]:
    """Get specialist's specific capabilities."""
    capabilities = {
        "strategist": [
            "Multi-platform campaign planning",
            "Budget allocation optimization",
            "Audience targeting strategy",
            "Performance forecasting",
            "Competitive positioning"
        ],
        "copywriter": [
            "High-converting ad copy creation",
            "A/B testing variations",
            "Platform-specific optimization",
            "Emotional trigger integration",
            "CTA optimization"
        ],
        "analyst": [
            "Performance data analysis",
            "Optimization recommendations",
            "ROI forecasting",
            "Attribution analysis",
            "Conversion optimization"
        ],
        "researcher": [
            "Market trend analysis",
            "Competitive intelligence",
            "Keyword opportunity discovery",
            "Industry insights",
            "Audience research"
        ]
    }
    return capabilities.get(specialist_name, ["General analysis"])
