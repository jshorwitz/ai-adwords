"""Real website analysis and content extraction."""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebsiteAnalyzer:
    """Analyzes websites for content, structure, and advertising potential."""
    
    def __init__(self):
        self.session = None
        self.user_agent = "AI AdWords Analyzer/1.0 (https://ai-adwords.com)"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_website(self, url: str) -> Dict[str, Any]:
        """Comprehensive website analysis."""
        
        try:
            logger.info(f"🔍 Analyzing website: {url}")
            
            # Fetch and parse website
            content = await self.fetch_website_content(url)
            if not content:
                raise Exception("Failed to fetch website content")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract all information
            analysis = {
                'url': url,
                'domain': urlparse(url).netloc,
                'title': self.extract_title(soup),
                'description': self.extract_description(soup),
                'keywords': self.extract_keywords(soup),
                'industry': self.detect_industry(soup, content),
                'business_type': self.detect_business_type(soup, content),
                'content_analysis': await self.analyze_content(soup, content),
                'seo_analysis': self.analyze_seo(soup),
                'social_links': self.extract_social_links(soup),
                'contact_info': self.extract_contact_info(soup),
                'technologies': self.detect_technologies(soup, content),
                'advertising_potential': self.assess_advertising_potential(soup, content)
            }
            
            logger.info(f"✅ Website analysis completed for {analysis['domain']}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Website analysis failed for {url}: {e}")
            raise
    
    async def fetch_website_content(self, url: str) -> Optional[str]:
        """Fetch website HTML content."""
        
        try:
            async with self.session.get(url, ssl=False) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Website returned status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else "Unknown Title"
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:200] + "..."
        
        return "No description available"
    
    def extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags and content."""
        keywords = []
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords.extend([k.strip() for k in meta_keywords.get('content', '').split(',')])
        
        # Extract from headings
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text().strip()
            if text and len(text.split()) <= 4:  # Short phrases only
                keywords.append(text.lower())
        
        # Extract from title
        title = self.extract_title(soup)
        title_words = re.findall(r'\b\w{3,}\b', title.lower())
        keywords.extend(title_words)
        
        # Clean and deduplicate
        keywords = list(set([k for k in keywords if k and len(k) > 2]))
        return keywords[:20]  # Limit to top 20
    
    def detect_industry(self, soup: BeautifulSoup, content: str) -> str:
        """Detect website industry from content."""
        
        content_lower = content.lower()
        
        industry_patterns = {
            'E-commerce': ['shop', 'store', 'buy', 'cart', 'product', 'ecommerce', 'retail'],
            'SaaS': ['saas', 'software', 'platform', 'api', 'cloud', 'subscription'],
            'Technology': ['tech', 'development', 'programming', 'software', 'digital'],
            'Finance': ['bank', 'finance', 'investment', 'money', 'financial', 'trading'],
            'Healthcare': ['health', 'medical', 'doctor', 'hospital', 'therapy', 'wellness'],
            'Education': ['education', 'learn', 'course', 'training', 'school', 'university'],
            'Real Estate': ['real estate', 'property', 'homes', 'rent', 'mortgage'],
            'Travel': ['travel', 'hotel', 'flight', 'vacation', 'tourism', 'booking'],
            'Food & Beverage': ['food', 'restaurant', 'recipe', 'cooking', 'dining'],
            'Fitness': ['fitness', 'gym', 'workout', 'exercise', 'health', 'nutrition']
        }
        
        industry_scores = {}
        for industry, patterns in industry_patterns.items():
            score = sum(content_lower.count(pattern) for pattern in patterns)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        
        return "Technology"  # Default
    
    def detect_business_type(self, soup: BeautifulSoup, content: str) -> str:
        """Detect B2B vs B2C business type."""
        
        content_lower = content.lower()
        
        b2b_indicators = ['enterprise', 'business', 'corporate', 'api', 'integration', 'enterprise', 'professional']
        b2c_indicators = ['consumer', 'personal', 'individual', 'family', 'home', 'lifestyle']
        
        b2b_score = sum(content_lower.count(indicator) for indicator in b2b_indicators)
        b2c_score = sum(content_lower.count(indicator) for indicator in b2c_indicators)
        
        return "B2B" if b2b_score > b2c_score else "B2C"
    
    async def analyze_content(self, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Analyze website content for advertising insights."""
        
        # Extract value propositions
        value_props = []
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text().strip()
            if any(word in text.lower() for word in ['best', 'leading', 'top', 'premium', 'expert']):
                value_props.append(text)
        
        # Extract CTAs
        ctas = []
        for button in soup.find_all(['button', 'a']):
            text = button.get_text().strip()
            if any(word in text.lower() for word in ['sign up', 'get started', 'try', 'demo', 'contact', 'buy']):
                ctas.append(text)
        
        # Analyze content themes
        themes = self.extract_content_themes(content)
        
        return {
            'value_propositions': value_props[:5],
            'call_to_actions': ctas[:5],
            'content_themes': themes,
            'word_count': len(content.split()),
            'readability_score': self.calculate_readability(content)
        }
    
    def extract_content_themes(self, content: str) -> List[str]:
        """Extract main content themes."""
        
        # Simple theme extraction based on word frequency
        words = re.findall(r'\b\w{4,}\b', content.lower())
        
        # Filter out common words
        stop_words = {'that', 'with', 'this', 'they', 'your', 'from', 'have', 'more', 'will', 'been', 'were'}
        words = [w for w in words if w not in stop_words]
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top themes
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in top_words[:10] if count >= 3]
    
    def analyze_seo(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze SEO elements."""
        
        return {
            'has_meta_description': bool(soup.find('meta', attrs={'name': 'description'})),
            'has_meta_keywords': bool(soup.find('meta', attrs={'name': 'keywords'})),
            'heading_structure': {
                'h1_count': len(soup.find_all('h1')),
                'h2_count': len(soup.find_all('h2')),
                'h3_count': len(soup.find_all('h3'))
            },
            'image_alt_tags': len([img for img in soup.find_all('img') if img.get('alt')]),
            'total_images': len(soup.find_all('img')),
            'internal_links': len([a for a in soup.find_all('a') if a.get('href', '').startswith('/')]),
            'external_links': len([a for a in soup.find_all('a') if a.get('href', '').startswith('http')])
        }
    
    def extract_social_links(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract social media links."""
        
        social_patterns = {
            'facebook': r'facebook\.com/[\w\.-]+',
            'twitter': r'twitter\.com/[\w\.-]+',
            'x': r'x\.com/[\w\.-]+',
            'linkedin': r'linkedin\.com/[\w\.-/]+',
            'instagram': r'instagram\.com/[\w\.-]+',
            'youtube': r'youtube\.com/[\w\.-/]+',
            'reddit': r'reddit\.com/[\w\.-/]+'
        }
        
        social_links = {}
        page_html = str(soup)
        
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, page_html)
            social_links[platform] = f"https://{match.group()}" if match else None
        
        return social_links
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract contact information."""
        
        page_text = soup.get_text()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        
        # Extract phone
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, page_text)
        
        return {
            'email': emails[0] if emails else None,
            'phone': phones[0] if phones else None,
            'has_contact_form': bool(soup.find('form')),
            'contact_page': bool(any('contact' in link.get('href', '').lower() 
                                    for link in soup.find_all('a') if link.get('href')))
        }
    
    def detect_technologies(self, soup: BeautifulSoup, content: str) -> List[str]:
        """Detect technologies used on the website."""
        
        technologies = []
        
        # Check for common platforms/frameworks
        tech_patterns = {
            'WordPress': ['wp-content', 'wp-includes', 'wordpress'],
            'Shopify': ['shopify', 'shopify.com', 'myshopify'],
            'React': ['react', '__REACT_DEVTOOLS_GLOBAL_HOOK__'],
            'Angular': ['angular', 'ng-'],
            'Vue.js': ['vue', '__vue__'],
            'jQuery': ['jquery', '$.'],
            'Bootstrap': ['bootstrap', 'btn-'],
            'Tailwind': ['tailwind', 'tw-'],
            'Google Analytics': ['google-analytics', 'gtag', 'UA-'],
            'Google Tag Manager': ['googletagmanager', 'GTM-'],
            'Facebook Pixel': ['facebook.com/tr', 'fbevents'],
            'Stripe': ['stripe', 'sk_live_', 'pk_live_'],
            'PayPal': ['paypal', 'paypalobjects'],
            'Salesforce': ['salesforce', 'sfdc'],
            'HubSpot': ['hubspot', 'hs-'],
            'Intercom': ['intercom', 'intercom.io'],
            'Zendesk': ['zendesk', 'zdassets']
        }
        
        content_lower = content.lower()
        page_html = str(soup).lower()
        
        for tech, patterns in tech_patterns.items():
            if any(pattern in content_lower or pattern in page_html for pattern in patterns):
                technologies.append(tech)
        
        return technologies
    
    def assess_advertising_potential(self, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Assess website's advertising readiness and potential."""
        
        # Check for existing advertising elements
        has_google_ads = bool(re.search(r'googleads|adwords|googlesyndication', content, re.I))
        has_facebook_ads = bool(re.search(r'facebook.*ads|fbevents', content, re.I))
        has_analytics = bool(re.search(r'google-analytics|gtag|segment|mixpanel', content, re.I))
        
        # Check for conversion elements
        has_forms = bool(soup.find_all('form'))
        has_ecommerce = bool(re.search(r'cart|checkout|buy|purchase|shop', content, re.I))
        has_signup = bool(re.search(r'sign.?up|register|join', content, re.I))
        
        # Calculate potential score
        potential_score = 0
        if has_analytics: potential_score += 20
        if has_forms: potential_score += 15
        if has_ecommerce: potential_score += 25
        if has_signup: potential_score += 20
        if has_google_ads: potential_score += 10
        if has_facebook_ads: potential_score += 10
        
        return {
            'advertising_readiness_score': potential_score,
            'has_existing_ads': has_google_ads or has_facebook_ads,
            'has_analytics_tracking': has_analytics,
            'has_conversion_elements': has_forms or has_ecommerce or has_signup,
            'ecommerce_enabled': has_ecommerce,
            'lead_generation_ready': has_forms and has_signup,
            'recommended_platforms': self.recommend_ad_platforms(potential_score, has_ecommerce)
        }
    
    def recommend_ad_platforms(self, score: int, is_ecommerce: bool) -> List[str]:
        """Recommend advertising platforms based on website analysis."""
        
        platforms = []
        
        if score >= 60:
            platforms.append("Google Ads")
            
        if is_ecommerce:
            platforms.extend(["Facebook Ads", "Instagram Ads"])
        
        if score >= 40:
            platforms.append("Reddit Ads")
            
        if score >= 50:
            platforms.append("X (Twitter) Ads")
            
        if score >= 80:
            platforms.extend(["LinkedIn Ads", "TikTok Ads"])
        
        return platforms or ["Google Ads"]  # Default recommendation
    
    def calculate_readability(self, content: str) -> int:
        """Calculate basic readability score."""
        
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        
        if sentences == 0:
            return 50  # Default
        
        avg_words_per_sentence = words / sentences
        
        # Simple readability score (lower is better)
        if avg_words_per_sentence <= 15:
            return 90  # Very readable
        elif avg_words_per_sentence <= 20:
            return 75  # Good
        elif avg_words_per_sentence <= 25:
            return 60  # Average
        else:
            return 40  # Difficult
    
    async def get_page_speed_insights(self, url: str) -> Dict[str, Any]:
        """Get page speed insights (requires Google PageSpeed API)."""
        
        try:
            api_key = os.getenv('GOOGLE_PAGESPEED_API_KEY')
            if not api_key:
                return {'error': 'PageSpeed API key not configured'}
            
            api_url = f"https://www.googleapis.com/pagespeed/v5/runPagespeed"
            params = {
                'url': url,
                'key': api_key,
                'category': 'performance',
                'strategy': 'mobile'
            }
            
            async with self.session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'performance_score': data.get('lighthouseResult', {}).get('categories', {}).get('performance', {}).get('score', 0) * 100,
                        'loading_time': data.get('loadingExperience', {}).get('metrics', {}).get('FIRST_CONTENTFUL_PAINT_MS', {}).get('percentile', 0),
                        'recommendations': self.extract_speed_recommendations(data)
                    }
        except Exception as e:
            logger.warning(f"PageSpeed analysis failed: {e}")
        
        return {'error': 'PageSpeed analysis unavailable'}
    
    def extract_speed_recommendations(self, pagespeed_data: Dict) -> List[str]:
        """Extract speed optimization recommendations."""
        
        recommendations = []
        audits = pagespeed_data.get('lighthouseResult', {}).get('audits', {})
        
        for audit_key, audit_data in audits.items():
            if audit_data.get('score', 1) < 0.9 and audit_data.get('title'):
                recommendations.append(audit_data['title'])
        
        return recommendations[:5]  # Top 5 recommendations


# Usage example and testing function
async def analyze_website_example(url: str) -> Dict[str, Any]:
    """Example usage of website analyzer."""
    
    async with WebsiteAnalyzer() as analyzer:
        return await analyzer.analyze_website(url)


# Quick test function
async def test_website_analysis():
    """Test the website analyzer with a real website."""
    
    test_urls = [
        "https://sourcegraph.com",
        "https://shopify.com", 
        "https://vercel.com"
    ]
    
    for url in test_urls:
        try:
            print(f"\n🔍 Analyzing {url}...")
            result = await analyze_website_example(url)
            print(f"✅ Title: {result['title']}")
            print(f"✅ Industry: {result['industry']}")
            print(f"✅ Keywords: {result['keywords'][:5]}")
            print(f"✅ Ad Potential: {result['advertising_potential']['advertising_readiness_score']}/100")
        except Exception as e:
            print(f"❌ Failed to analyze {url}: {e}")


if __name__ == "__main__":
    asyncio.run(test_website_analysis())
