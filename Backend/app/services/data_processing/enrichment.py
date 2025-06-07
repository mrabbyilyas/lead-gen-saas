"""Data enrichment utilities for companies and contacts."""

import re
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TechnologyCategory(Enum):
    """Technology categories for classification."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    ECOMMERCE = "ecommerce"
    CMS = "cms"
    HOSTING = "hosting"
    CDN = "cdn"
    SECURITY = "security"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    UNKNOWN = "unknown"


@dataclass
class TechnologyInfo:
    """Information about detected technology."""

    name: str
    category: TechnologyCategory
    confidence: float
    version: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    detection_method: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnrichmentResult:
    """Result of data enrichment."""

    original_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    technologies: List[TechnologyInfo] = field(default_factory=list)
    confidence_score: float = 0.0
    sources: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataEnrichmentService:
    """Service for enriching company data with additional information."""

    def __init__(self):
        self.technology_detector = TechnologyDetector()

    async def enrich_company_data(
        self, company_data: Dict[str, Any]
    ) -> EnrichmentResult:
        """Enrich company data with additional information."""
        try:
            enriched_data = company_data.copy()
            technologies = []
            sources = []
            errors = []

            # Try to detect technologies from website
            if "website" in company_data and company_data["website"]:
                try:
                    detected_techs = await self.technology_detector.detect_from_website(
                        company_data["website"]
                    )
                    technologies.extend(detected_techs)
                    sources.append("website_analysis")
                except Exception as e:
                    errors.append(f"Website analysis failed: {str(e)}")

            # Calculate confidence score
            confidence_score = len(technologies) * 0.1 if technologies else 0.0
            confidence_score = min(confidence_score, 1.0)

            return EnrichmentResult(
                original_data=company_data,
                enriched_data=enriched_data,
                technologies=technologies,
                confidence_score=confidence_score,
                sources=sources,
                errors=errors,
                metadata={"enrichment_timestamp": datetime.now().isoformat()},
            )
        except Exception as e:
            return EnrichmentResult(
                original_data=company_data,
                enriched_data=company_data,
                technologies=[],
                confidence_score=0.0,
                sources=[],
                errors=[f"Enrichment failed: {str(e)}"],
                metadata={},
            )


class TechnologyDetector:
    """Detect technologies used by companies from their websites."""

    def __init__(self):
        # Technology signatures for detection
        self.technology_signatures = {
            # Frontend Frameworks
            "React": {
                "category": TechnologyCategory.FRONTEND,
                "patterns": [r"react", r"_react", r"React\."],
                "headers": ["x-powered-by"],
                "meta_tags": ["generator"],
                "scripts": [r"react\.", r"react-dom"],
                "description": "JavaScript library for building user interfaces",
            },
            "Vue.js": {
                "category": TechnologyCategory.FRONTEND,
                "patterns": [r"vue\.js", r"vuejs", r"__vue__"],
                "scripts": [r"vue\.", r"vue@"],
                "description": "Progressive JavaScript framework",
            },
            "Angular": {
                "category": TechnologyCategory.FRONTEND,
                "patterns": [r"angular", r"ng-"],
                "scripts": [r"angular\.", r"@angular"],
                "description": "Platform for building mobile and desktop web applications",
            },
            "jQuery": {
                "category": TechnologyCategory.FRONTEND,
                "patterns": [r"jquery", r"\$\("],
                "scripts": [r"jquery"],
                "description": "Fast, small, and feature-rich JavaScript library",
            },
            # Backend Technologies
            "Node.js": {
                "category": TechnologyCategory.BACKEND,
                "headers": ["x-powered-by"],
                "patterns": [r"node\.js", r"express"],
                "description": "JavaScript runtime built on Chrome's V8 JavaScript engine",
            },
            "Django": {
                "category": TechnologyCategory.BACKEND,
                "headers": ["x-powered-by", "server"],
                "patterns": [r"django", r"csrftoken"],
                "description": "High-level Python web framework",
            },
            "Flask": {
                "category": TechnologyCategory.BACKEND,
                "headers": ["x-powered-by", "server"],
                "patterns": [r"flask"],
                "description": "Lightweight WSGI web application framework",
            },
            "Ruby on Rails": {
                "category": TechnologyCategory.BACKEND,
                "headers": ["x-powered-by"],
                "patterns": [r"rails", r"ruby"],
                "description": "Server-side web application framework",
            },
            "PHP": {
                "category": TechnologyCategory.BACKEND,
                "headers": ["x-powered-by", "server"],
                "patterns": [r"php", r"PHPSESSID"],
                "description": "Popular general-purpose scripting language",
            },
            "ASP.NET": {
                "category": TechnologyCategory.BACKEND,
                "headers": ["x-powered-by", "x-aspnet-version"],
                "patterns": [r"asp\.net", r"__VIEWSTATE"],
                "description": "Web framework for building modern web apps",
            },
            # CMS
            "WordPress": {
                "category": TechnologyCategory.CMS,
                "patterns": [r"wp-content", r"wordpress", r"wp-includes"],
                "meta_tags": ["generator"],
                "description": "Content management system",
            },
            "Drupal": {
                "category": TechnologyCategory.CMS,
                "patterns": [r"drupal", r"sites/default"],
                "meta_tags": ["generator"],
                "description": "Content management framework",
            },
            "Joomla": {
                "category": TechnologyCategory.CMS,
                "patterns": [r"joomla", r"option=com_"],
                "meta_tags": ["generator"],
                "description": "Content management system",
            },
            "Shopify": {
                "category": TechnologyCategory.ECOMMERCE,
                "patterns": [r"shopify", r"myshopify\.com"],
                "headers": ["x-shopify-stage"],
                "description": "E-commerce platform",
            },
            # Analytics
            "Google Analytics": {
                "category": TechnologyCategory.ANALYTICS,
                "patterns": [r"google-analytics", r"gtag", r"ga\("],
                "scripts": [r"googletagmanager", r"google-analytics"],
                "description": "Web analytics service",
            },
            "Facebook Pixel": {
                "category": TechnologyCategory.ANALYTICS,
                "patterns": [r"facebook\.com/tr", r"fbq\("],
                "scripts": [r"connect\.facebook\.net"],
                "description": "Analytics tool for Facebook ads",
            },
            "Hotjar": {
                "category": TechnologyCategory.ANALYTICS,
                "patterns": [r"hotjar"],
                "scripts": [r"static\.hotjar\.com"],
                "description": "Behavior analytics and user feedback",
            },
            # CDN & Hosting
            "Cloudflare": {
                "category": TechnologyCategory.CDN,
                "headers": ["cf-ray", "server"],
                "patterns": [r"cloudflare"],
                "description": "Content delivery network",
            },
            "Amazon CloudFront": {
                "category": TechnologyCategory.CDN,
                "headers": ["x-amz-cf-id", "via"],
                "description": "Content delivery network",
            },
            "Netlify": {
                "category": TechnologyCategory.HOSTING,
                "headers": ["x-nf-request-id"],
                "patterns": [r"netlify"],
                "description": "Web hosting and automation platform",
            },
            "Vercel": {
                "category": TechnologyCategory.HOSTING,
                "headers": ["x-vercel-id"],
                "patterns": [r"vercel"],
                "description": "Frontend cloud platform",
            },
            # Payment
            "Stripe": {
                "category": TechnologyCategory.PAYMENT,
                "patterns": [r"stripe", r"js\.stripe\.com"],
                "scripts": [r"js\.stripe\.com"],
                "description": "Payment processing platform",
            },
            "PayPal": {
                "category": TechnologyCategory.PAYMENT,
                "patterns": [r"paypal", r"paypalobjects"],
                "scripts": [r"paypal"],
                "description": "Online payment system",
            },
            # Marketing
            "Mailchimp": {
                "category": TechnologyCategory.MARKETING,
                "patterns": [r"mailchimp", r"mc\.us"],
                "description": "Email marketing platform",
            },
            "HubSpot": {
                "category": TechnologyCategory.MARKETING,
                "patterns": [r"hubspot", r"hs-analytics"],
                "scripts": [r"js\.hs-analytics\.net"],
                "description": "Inbound marketing and sales platform",
            },
        }

    async def detect_from_website(
        self, url: str, timeout: int = 30
    ) -> List[TechnologyInfo]:
        """Detect technologies from website analysis."""
        technologies: List[TechnologyInfo] = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; TechDetector/1.0)"
                    },
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}: {response.status}")
                        return technologies

                    content = await response.text()
                    headers = dict(response.headers)

                    # Analyze headers
                    header_techs = self._analyze_headers(headers)
                    technologies.extend(header_techs)

                    # Analyze HTML content
                    content_techs = self._analyze_content(content)
                    technologies.extend(content_techs)

                    # Analyze scripts and meta tags
                    soup = BeautifulSoup(content, "html.parser")
                    script_techs = self._analyze_scripts(soup)
                    technologies.extend(script_techs)

                    meta_techs = self._analyze_meta_tags(soup)
                    technologies.extend(meta_techs)

        except asyncio.TimeoutError:
            logger.error(f"Timeout while analyzing {url}")
        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")

        # Remove duplicates and sort by confidence
        unique_techs = self._deduplicate_technologies(technologies)
        return sorted(unique_techs, key=lambda x: x.confidence, reverse=True)

    def _analyze_headers(self, headers: Dict[str, str]) -> List[TechnologyInfo]:
        """Analyze HTTP headers for technology signatures."""
        technologies = []

        for tech_name, tech_info in self.technology_signatures.items():
            if "headers" not in tech_info:
                continue

            for header_name in tech_info["headers"]:
                header_value = headers.get(header_name, "").lower()
                if header_value:
                    # Check patterns in header value
                    patterns = tech_info.get("patterns", [])
                    for pattern in patterns:
                        if re.search(pattern, header_value, re.IGNORECASE):
                            technologies.append(
                                TechnologyInfo(
                                    name=tech_name,
                                    category=tech_info["category"],
                                    confidence=0.8,
                                    detection_method="header",
                                    description=tech_info.get("description", ""),
                                    metadata={
                                        "header": header_name,
                                        "value": header_value,
                                    },
                                )
                            )
                            break

        return technologies

    def _analyze_content(self, content: str) -> List[TechnologyInfo]:
        """Analyze HTML content for technology signatures."""
        technologies = []

        for tech_name, tech_info in self.technology_signatures.items():
            patterns = tech_info.get("patterns", [])

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    confidence = min(0.7 + len(matches) * 0.1, 0.9)
                    technologies.append(
                        TechnologyInfo(
                            name=tech_name,
                            category=tech_info["category"],
                            confidence=confidence,
                            detection_method="content",
                            description=tech_info.get("description", ""),
                            metadata={"matches": len(matches)},
                        )
                    )
                    break

        return technologies

    def _analyze_scripts(self, soup: BeautifulSoup) -> List[TechnologyInfo]:
        """Analyze script tags for technology signatures."""
        technologies = []

        script_tags = soup.find_all("script", src=True)
        script_content = " ".join([script.get("src", "") for script in script_tags])

        # Also check inline scripts
        inline_scripts = soup.find_all("script", src=False)
        inline_content = " ".join([script.get_text() for script in inline_scripts])

        all_script_content = script_content + " " + inline_content

        for tech_name, tech_info in self.technology_signatures.items():
            script_patterns = tech_info.get("scripts", [])

            for pattern in script_patterns:
                if re.search(pattern, all_script_content, re.IGNORECASE):
                    technologies.append(
                        TechnologyInfo(
                            name=tech_name,
                            category=tech_info["category"],
                            confidence=0.85,
                            detection_method="script",
                            description=tech_info.get("description", ""),
                            metadata={"script_count": len(script_tags)},
                        )
                    )
                    break

        return technologies

    def _analyze_meta_tags(self, soup: BeautifulSoup) -> List[TechnologyInfo]:
        """Analyze meta tags for technology signatures."""
        technologies = []

        meta_tags = soup.find_all("meta")

        for tech_name, tech_info in self.technology_signatures.items():
            meta_tag_names = tech_info.get("meta_tags", [])

            for meta_name in meta_tag_names:
                for meta_tag in meta_tags:
                    if meta_tag.get("name", "").lower() == meta_name:
                        content = meta_tag.get("content", "").lower()
                        patterns = tech_info.get("patterns", [])

                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                technologies.append(
                                    TechnologyInfo(
                                        name=tech_name,
                                        category=tech_info["category"],
                                        confidence=0.9,
                                        detection_method="meta_tag",
                                        description=tech_info.get("description", ""),
                                        metadata={
                                            "meta_name": meta_name,
                                            "content": content,
                                        },
                                    )
                                )
                                break

        return technologies

    def _deduplicate_technologies(
        self, technologies: List[TechnologyInfo]
    ) -> List[TechnologyInfo]:
        """Remove duplicate technology detections."""
        seen = set()
        unique_techs = []

        for tech in technologies:
            if tech.name not in seen:
                seen.add(tech.name)
                unique_techs.append(tech)
            else:
                # Update confidence if higher
                for existing_tech in unique_techs:
                    if (
                        existing_tech.name == tech.name
                        and tech.confidence > existing_tech.confidence
                    ):
                        existing_tech.confidence = tech.confidence
                        existing_tech.detection_method = tech.detection_method
                        break

        return unique_techs


class CompanyEnricher:
    """Enrich company data with additional information."""

    def __init__(self):
        self.tech_detector = TechnologyDetector()

        # Industry keywords for classification
        self.industry_keywords = {
            "Technology": [
                "software",
                "tech",
                "ai",
                "machine learning",
                "saas",
                "cloud",
                "data",
            ],
            "Healthcare": [
                "health",
                "medical",
                "pharma",
                "biotech",
                "hospital",
                "clinic",
            ],
            "Finance": [
                "bank",
                "finance",
                "fintech",
                "investment",
                "insurance",
                "trading",
            ],
            "E-commerce": ["ecommerce", "retail", "shopping", "marketplace", "store"],
            "Education": ["education", "learning", "school", "university", "training"],
            "Marketing": ["marketing", "advertising", "agency", "digital marketing"],
            "Consulting": ["consulting", "advisory", "services", "strategy"],
            "Manufacturing": ["manufacturing", "production", "factory", "industrial"],
            "Real Estate": ["real estate", "property", "construction", "development"],
            "Media": ["media", "publishing", "news", "entertainment", "content"],
        }

    async def enrich_company(self, company_data: Dict[str, Any]) -> EnrichmentResult:
        """Enrich company data with additional information."""
        enriched_data = company_data.copy()
        technologies = []
        sources = []
        errors = []

        try:
            # Detect technologies from website
            website = company_data.get("website") or company_data.get("domain")
            if website:
                if not website.startswith(("http://", "https://")):
                    website = f"https://{website}"

                try:
                    detected_techs = await self.tech_detector.detect_from_website(
                        website
                    )
                    technologies.extend(detected_techs)
                    sources.append("website_analysis")
                except Exception as e:
                    errors.append(f"Technology detection failed: {str(e)}")

            # Infer industry from description and name
            industry = self._infer_industry(company_data)
            if industry and not enriched_data.get("industry"):
                enriched_data["industry"] = industry
                sources.append("industry_inference")

            # Estimate company size from description
            company_size = self._estimate_company_size(company_data)
            if company_size:
                enriched_data["estimated_size"] = company_size
                sources.append("size_estimation")

            # Extract social media links
            social_links = self._extract_social_links(company_data)
            if social_links:
                enriched_data.update(social_links)
                sources.append("social_extraction")

            # Normalize and clean data
            enriched_data = self._normalize_company_data(enriched_data)

            # Calculate confidence score
            confidence = self._calculate_confidence(enriched_data, technologies)

            return EnrichmentResult(
                original_data=company_data,
                enriched_data=enriched_data,
                technologies=technologies,
                confidence_score=confidence,
                sources=sources,
                errors=errors,
                metadata={
                    "enrichment_fields": len(
                        [k for k in enriched_data.keys() if k not in company_data]
                    ),
                    "technology_count": len(technologies),
                },
            )

        except Exception as e:
            logger.error(f"Error enriching company data: {e}")
            errors.append(f"Enrichment failed: {str(e)}")

            return EnrichmentResult(
                original_data=company_data,
                enriched_data=enriched_data,
                technologies=technologies,
                confidence_score=0.1,
                sources=sources,
                errors=errors,
            )

    def _infer_industry(self, company_data: Dict[str, Any]) -> Optional[str]:
        """Infer industry from company name and description."""
        text_to_analyze = " ".join(
            [
                company_data.get("name", ""),
                company_data.get("description", ""),
                company_data.get("industry", ""),
            ]
        ).lower()

        industry_scores = {}

        for industry, keywords in self.industry_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_to_analyze:
                    score += 1

            if score > 0:
                industry_scores[industry] = score

        if industry_scores:
            result = max(industry_scores, key=lambda x: industry_scores[x])
            return str(result) if result is not None else None

        return None

    def _estimate_company_size(self, company_data: Dict[str, Any]) -> Optional[str]:
        """Estimate company size from available data."""
        description = company_data.get("description", "").lower()

        # Size indicators
        size_indicators = {
            "startup": ["startup", "founded", "early stage", "seed"],
            "small": ["small", "boutique", "local", "family"],
            "medium": ["growing", "expanding", "regional"],
            "large": [
                "enterprise",
                "global",
                "international",
                "fortune",
                "multinational",
            ],
            "enterprise": ["corporation", "inc.", "corp.", "enterprise", "worldwide"],
        }

        for size, indicators in size_indicators.items():
            for indicator in indicators:
                if indicator in description:
                    return size

        return None

    def _extract_social_links(self, company_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract social media links from company data."""
        social_links = {}

        # Check existing fields
        linkedin_url = company_data.get("linkedin_url")
        if linkedin_url:
            social_links["linkedin_url"] = linkedin_url

        # Extract from description or other text fields
        text_fields = [
            company_data.get("description", ""),
            company_data.get("website", ""),
        ]

        text = " ".join(text_fields)

        # Social media patterns
        social_patterns = {
            "twitter_url": r"https?://(?:www\.)?twitter\.com/[a-zA-Z0-9_]+",
            "facebook_url": r"https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.]+",
            "instagram_url": r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+",
            "youtube_url": r"https?://(?:www\.)?youtube\.com/[a-zA-Z0-9_]+",
        }

        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                social_links[platform] = matches[0]

        return social_links

    def _normalize_company_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize company data fields."""
        normalized = data.copy()

        # Ensure website has protocol
        if "website" in normalized and normalized["website"]:
            website = normalized["website"]
            if not website.startswith(("http://", "https://")):
                normalized["website"] = f"https://{website}"

        # Extract domain from website if not present
        if "website" in normalized and not normalized.get("domain"):
            try:
                parsed = urlparse(normalized["website"])
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                normalized["domain"] = domain
            except Exception:
                pass

        return normalized

    def _calculate_confidence(
        self, enriched_data: Dict[str, Any], technologies: List[TechnologyInfo]
    ) -> float:
        """Calculate confidence score for enriched data."""
        base_score = 0.5

        # Add points for each enriched field
        enrichment_fields = ["industry", "estimated_size", "domain"]
        for field_name in enrichment_fields:
            if enriched_data.get(field_name):
                base_score += 0.1

        # Add points for technology detection
        if technologies:
            tech_confidence = sum(tech.confidence for tech in technologies) / len(
                technologies
            )
            base_score += tech_confidence * 0.3

        # Add points for social media links
        social_fields = ["linkedin_url", "twitter_url", "facebook_url"]
        social_count = sum(1 for field in social_fields if enriched_data.get(field))
        base_score += social_count * 0.05

        return min(base_score, 1.0)


class ContactEnricher:
    """Enrich contact data with additional information."""

    def __init__(self):
        # Job title categories
        self.job_categories = {
            "Executive": ["ceo", "cto", "cfo", "coo", "president", "founder", "owner"],
            "Management": [
                "manager",
                "director",
                "head",
                "lead",
                "supervisor",
                "chief",
            ],
            "Sales": ["sales", "account", "business development", "revenue"],
            "Marketing": ["marketing", "brand", "content", "social media", "seo"],
            "Engineering": [
                "engineer",
                "developer",
                "programmer",
                "architect",
                "devops",
            ],
            "Design": ["designer", "ux", "ui", "creative", "art"],
            "Operations": ["operations", "logistics", "supply chain", "admin"],
            "HR": ["hr", "human resources", "recruiter", "talent"],
            "Finance": ["finance", "accounting", "controller", "analyst"],
            "Legal": ["legal", "counsel", "attorney", "compliance"],
        }

    def enrich_contact(self, contact_data: Dict[str, Any]) -> EnrichmentResult:
        """Enrich contact data with additional information."""
        enriched_data = contact_data.copy()
        sources = []
        errors: List[str] = []

        try:
            # Categorize job title
            job_category = self._categorize_job_title(contact_data.get("job_title", ""))
            if job_category:
                enriched_data["job_category"] = job_category
                sources.append("job_categorization")

            # Determine seniority level
            seniority = self._determine_seniority(contact_data.get("job_title", ""))
            if seniority:
                enriched_data["seniority_level"] = seniority
                sources.append("seniority_analysis")

            # Extract name components if full name provided
            if "full_name" in contact_data and not contact_data.get("first_name"):
                name_parts = self._parse_full_name(contact_data["full_name"])
                enriched_data.update(name_parts)
                sources.append("name_parsing")

            # Infer gender from first name (optional)
            gender = self._infer_gender(enriched_data.get("first_name", ""))
            if gender:
                enriched_data["inferred_gender"] = gender
                sources.append("gender_inference")

            # Calculate confidence score
            confidence = self._calculate_contact_confidence(enriched_data)

            return EnrichmentResult(
                original_data=contact_data,
                enriched_data=enriched_data,
                confidence_score=confidence,
                sources=sources,
                errors=errors,
                metadata={
                    "enrichment_fields": len(
                        [k for k in enriched_data.keys() if k not in contact_data]
                    )
                },
            )

        except Exception as e:
            logger.error(f"Error enriching contact data: {e}")
            errors.append(f"Contact enrichment failed: {str(e)}")

            return EnrichmentResult(
                original_data=contact_data,
                enriched_data=enriched_data,
                confidence_score=0.1,
                sources=sources,
                errors=errors,
            )

    def _categorize_job_title(self, job_title: str) -> Optional[str]:
        """Categorize job title into functional area."""
        if not job_title:
            return None

        job_title_lower = job_title.lower()

        for category, keywords in self.job_categories.items():
            for keyword in keywords:
                if keyword in job_title_lower:
                    return str(category) if category is not None else "Other"

        return "Other"

    def _determine_seniority(self, job_title: str) -> Optional[str]:
        """Determine seniority level from job title."""
        if not job_title:
            return None

        job_title_lower = job_title.lower()

        # Executive level
        executive_keywords = [
            "ceo",
            "cto",
            "cfo",
            "coo",
            "president",
            "founder",
            "owner",
            "partner",
        ]
        if any(keyword in job_title_lower for keyword in executive_keywords):
            return "Executive"

        # Senior level
        senior_keywords = [
            "senior",
            "sr",
            "principal",
            "lead",
            "head",
            "director",
            "vp",
            "vice president",
        ]
        if any(keyword in job_title_lower for keyword in senior_keywords):
            return "Senior"

        # Mid level
        mid_keywords = ["manager", "supervisor", "coordinator", "specialist"]
        if any(keyword in job_title_lower for keyword in mid_keywords):
            return "Mid"

        # Junior level
        junior_keywords = [
            "junior",
            "jr",
            "associate",
            "assistant",
            "intern",
            "trainee",
        ]
        if any(keyword in job_title_lower for keyword in junior_keywords):
            return "Junior"

        return "Mid"  # Default to mid-level

    def _parse_full_name(self, full_name: str) -> Dict[str, str]:
        """Parse full name into first and last name components."""
        if not full_name:
            return {}

        # Clean and split name
        name_parts = full_name.strip().split()

        if len(name_parts) == 1:
            return {"first_name": name_parts[0]}
        elif len(name_parts) == 2:
            return {"first_name": name_parts[0], "last_name": name_parts[1]}
        elif len(name_parts) > 2:
            return {"first_name": name_parts[0], "last_name": " ".join(name_parts[1:])}

        return {}

    def _infer_gender(self, first_name: str) -> Optional[str]:
        """Infer gender from first name (basic implementation)."""
        if not first_name:
            return None

        # This is a very basic implementation
        # In production, you might want to use a more comprehensive name database
        male_names = {
            "john",
            "michael",
            "david",
            "james",
            "robert",
            "william",
            "richard",
            "thomas",
            "christopher",
            "daniel",
            "matthew",
            "anthony",
            "mark",
            "donald",
            "steven",
            "paul",
            "andrew",
            "joshua",
            "kenneth",
            "kevin",
        }

        female_names = {
            "mary",
            "patricia",
            "jennifer",
            "linda",
            "elizabeth",
            "barbara",
            "susan",
            "jessica",
            "sarah",
            "karen",
            "nancy",
            "lisa",
            "betty",
            "helen",
            "sandra",
            "donna",
            "carol",
            "ruth",
            "sharon",
            "michelle",
        }

        first_name_lower = first_name.lower()

        if first_name_lower in male_names:
            return "Male"
        elif first_name_lower in female_names:
            return "Female"

        return None

    def _calculate_contact_confidence(self, enriched_data: Dict[str, Any]) -> float:
        """Calculate confidence score for enriched contact data."""
        base_score = 0.5

        # Required fields
        required_fields = ["first_name", "last_name", "email"]
        for field_name in required_fields:
            if enriched_data.get(field_name):
                base_score += 0.1

        # Optional enriched fields
        optional_fields = ["job_title", "job_category", "seniority_level", "phone"]
        for field_name in optional_fields:
            if enriched_data.get(field_name):
                base_score += 0.05

        return min(base_score, 1.0)
