"""Data estimation utilities for company size, revenue, and other metrics."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class CompanySize(Enum):
    """Company size categories."""

    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class RevenueRange(Enum):
    """Revenue range categories."""

    UNDER_1M = "under_1m"
    RANGE_1M_10M = "1m_10m"
    RANGE_10M_50M = "10m_50m"
    RANGE_50M_100M = "50m_100m"
    RANGE_100M_500M = "100m_500m"
    RANGE_500M_1B = "500m_1b"
    OVER_1B = "over_1b"


class Industry(Enum):
    """Industry categories for estimation."""

    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    EDUCATION = "education"
    MARKETING = "marketing"
    CONSULTING = "consulting"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    MEDIA = "media"
    RETAIL = "retail"
    AUTOMOTIVE = "automotive"
    ENERGY = "energy"
    AGRICULTURE = "agriculture"
    OTHER = "other"


@dataclass
class EstimationResult:
    """Result of data estimation."""

    original_data: Dict[str, Any]
    estimated_data: Dict[str, Any]
    confidence_score: float
    estimation_methods: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class CompanySizeEstimator:
    """Estimate company size based on various indicators."""

    def __init__(self):
        # Employee count ranges for each size category
        self.size_ranges = {
            CompanySize.STARTUP: (1, 10),
            CompanySize.SMALL: (11, 50),
            CompanySize.MEDIUM: (51, 250),
            CompanySize.LARGE: (251, 1000),
            CompanySize.ENTERPRISE: (1001, float("inf")),
        }

        # Keywords that indicate company size
        self.size_keywords = {
            CompanySize.STARTUP: [
                "startup",
                "founded",
                "early stage",
                "seed",
                "pre-seed",
                "stealth",
                "emerging",
                "new venture",
                "bootstrap",
            ],
            CompanySize.SMALL: [
                "small",
                "boutique",
                "local",
                "family",
                "independent",
                "artisan",
                "craft",
                "niche",
                "specialized",
            ],
            CompanySize.MEDIUM: [
                "growing",
                "expanding",
                "regional",
                "mid-size",
                "established",
                "mature",
                "scaling",
            ],
            CompanySize.LARGE: [
                "large",
                "major",
                "leading",
                "prominent",
                "significant",
                "substantial",
                "nationwide",
                "multi-location",
            ],
            CompanySize.ENTERPRISE: [
                "enterprise",
                "global",
                "international",
                "fortune",
                "multinational",
                "corporation",
                "conglomerate",
                "worldwide",
                "industry leader",
                "market leader",
            ],
        }

        # Technology indicators that suggest company size
        self.tech_size_indicators = {
            CompanySize.STARTUP: [
                "mvp",
                "prototype",
                "beta",
                "stealth mode",
                "pre-launch",
                "proof of concept",
            ],
            CompanySize.SMALL: [
                "wordpress",
                "squarespace",
                "wix",
                "shopify basic",
                "basic hosting",
                "shared hosting",
            ],
            CompanySize.MEDIUM: [
                "dedicated server",
                "cloud hosting",
                "cdn",
                "professional email",
                "crm system",
            ],
            CompanySize.LARGE: [
                "enterprise software",
                "custom development",
                "multiple domains",
                "advanced analytics",
            ],
            CompanySize.ENTERPRISE: [
                "enterprise architecture",
                "microservices",
                "kubernetes",
                "enterprise security",
                "data centers",
                "global infrastructure",
            ],
        }

    def estimate_size(self, company_data: Dict[str, Any]) -> EstimationResult:
        """Estimate company size from available data."""
        estimated_data = company_data.copy()
        estimation_methods = []
        confidence_scores = []
        errors: List[str] = []

        try:
            # Method 1: Direct employee count
            if "employee_count" in company_data:
                size_from_count = self._size_from_employee_count(
                    company_data["employee_count"]
                )
                if size_from_count:
                    estimated_data["estimated_size"] = size_from_count.value
                    estimation_methods.append("employee_count")
                    confidence_scores.append(0.9)

            # Method 2: Keywords in description
            description = company_data.get("description", "")
            if description:
                size_from_keywords = self._size_from_keywords(description)
                if size_from_keywords:
                    if "estimated_size" not in estimated_data:
                        estimated_data["estimated_size"] = size_from_keywords.value
                    estimation_methods.append("keyword_analysis")
                    confidence_scores.append(0.6)

            # Method 3: Technology stack analysis
            technologies = company_data.get("technologies", [])
            if technologies:
                size_from_tech = self._size_from_technologies(technologies)
                if size_from_tech:
                    if "estimated_size" not in estimated_data:
                        estimated_data["estimated_size"] = size_from_tech.value
                    estimation_methods.append("technology_analysis")
                    confidence_scores.append(0.5)

            # Method 4: Website complexity analysis
            website_data = self._extract_website_complexity_indicators(company_data)
            if website_data:
                size_from_website = self._size_from_website_complexity(website_data)
                if size_from_website:
                    if "estimated_size" not in estimated_data:
                        estimated_data["estimated_size"] = size_from_website.value
                    estimation_methods.append("website_complexity")
                    confidence_scores.append(0.4)

            # Method 5: Industry and location analysis
            industry = company_data.get("industry")
            location = company_data.get("location") or company_data.get("address", "")
            if industry or location:
                size_from_context = self._size_from_context(industry, location)
                if size_from_context:
                    if "estimated_size" not in estimated_data:
                        estimated_data["estimated_size"] = size_from_context.value
                    estimation_methods.append("context_analysis")
                    confidence_scores.append(0.3)

            # Calculate overall confidence
            confidence = (
                statistics.mean(confidence_scores) if confidence_scores else 0.0
            )

            # Add employee count range estimate
            if "estimated_size" in estimated_data:
                size_enum = CompanySize(estimated_data["estimated_size"])
                min_employees, max_employees = self.size_ranges[size_enum]
                estimated_data["estimated_employee_range"] = {
                    "min": min_employees,
                    "max": max_employees if max_employees != float("inf") else 10000,
                }

            return EstimationResult(
                original_data=company_data,
                estimated_data=estimated_data,
                confidence_score=confidence,
                estimation_methods=estimation_methods,
                metadata={
                    "method_count": len(estimation_methods),
                    "confidence_scores": confidence_scores,
                },
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Error estimating company size: {e}")
            errors.append(f"Size estimation failed: {str(e)}")

            return EstimationResult(
                original_data=company_data,
                estimated_data=estimated_data,
                confidence_score=0.0,
                estimation_methods=estimation_methods,
                errors=errors,
            )

    def _size_from_employee_count(self, employee_count: int) -> Optional[CompanySize]:
        """Determine size category from employee count."""
        for size, (min_count, max_count) in self.size_ranges.items():
            if min_count <= employee_count <= max_count:
                return CompanySize(size) if isinstance(size, str) else size
        return None

    def _size_from_keywords(self, text: str) -> Optional[CompanySize]:
        """Determine size category from keywords in text."""
        text_lower = text.lower()
        size_scores = {}

        for size, keywords in self.size_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            if score > 0:
                size_scores[size] = score

        if size_scores:
            result = max(size_scores, key=lambda x: size_scores[x])
            return CompanySize(result) if isinstance(result, str) else result
        return None

    def _size_from_technologies(self, technologies: List[str]) -> Optional[CompanySize]:
        """Determine size category from technology stack."""
        tech_text = " ".join(technologies).lower()
        size_scores = {}

        for size, indicators in self.tech_size_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in tech_text:
                    score += 1
            if score > 0:
                size_scores[size] = score

        if size_scores:
            result = max(size_scores, key=lambda x: size_scores[x])
            return CompanySize(result) if isinstance(result, str) else result
        return None

    def _extract_website_complexity_indicators(
        self, company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract website complexity indicators."""
        indicators: Dict[str, Any] = {}

        # Check for multiple domains/subdomains
        website = company_data.get("website", "")
        if website:
            indicators["has_website"] = True

            # Check for HTTPS
            indicators["has_https"] = website.startswith("https://")

            # Check for subdomain complexity
            domain_parts = (
                website.replace("https://", "").replace("http://", "").split(".")
            )
            indicators["subdomain_count"] = (
                len(domain_parts) - 2 if len(domain_parts) > 2 else 0
            )

        # Check for social media presence
        social_fields = ["linkedin_url", "twitter_url", "facebook_url", "instagram_url"]
        social_count = sum(1 for field in social_fields if company_data.get(field))
        indicators["social_media_count"] = social_count

        # Check for professional email domain
        email = company_data.get("email", "")
        if email and "@" in email:
            email_domain = email.split("@")[1].lower()
            generic_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
            indicators["has_professional_email"] = email_domain not in generic_domains

        return indicators

    def _size_from_website_complexity(
        self, website_data: Dict[str, Any]
    ) -> Optional[CompanySize]:
        """Determine size category from website complexity."""
        complexity_score = 0

        if website_data.get("has_website"):
            complexity_score += 1

        if website_data.get("has_https"):
            complexity_score += 1

        if website_data.get("has_professional_email"):
            complexity_score += 2

        social_count = website_data.get("social_media_count", 0)
        if social_count >= 3:
            complexity_score += 2
        elif social_count >= 1:
            complexity_score += 1

        subdomain_count = website_data.get("subdomain_count", 0)
        if subdomain_count > 0:
            complexity_score += 1

        # Map complexity score to size
        if complexity_score >= 6:
            return CompanySize.LARGE
        elif complexity_score >= 4:
            return CompanySize.MEDIUM
        elif complexity_score >= 2:
            return CompanySize.SMALL
        else:
            return CompanySize.STARTUP

    def _size_from_context(
        self, industry: Optional[str], location: str
    ) -> Optional[CompanySize]:
        """Determine size category from industry and location context."""
        # This is a simplified heuristic
        # In practice, you might use more sophisticated industry data

        if not industry and not location:
            return None

        # Industry-based heuristics
        if industry:
            industry_lower = industry.lower()

            # Industries that tend to have larger companies
            large_industries = [
                "finance",
                "banking",
                "insurance",
                "automotive",
                "energy",
            ]
            if any(ind in industry_lower for ind in large_industries):
                return CompanySize.LARGE

            # Industries that tend to have smaller companies
            small_industries = ["consulting", "design", "marketing", "freelance"]
            if any(ind in industry_lower for ind in small_industries):
                return CompanySize.SMALL

        # Location-based heuristics
        if location:
            location_lower = location.lower()

            # Major business hubs suggest larger companies
            major_hubs = ["new york", "san francisco", "london", "tokyo", "singapore"]
            if any(hub in location_lower for hub in major_hubs):
                return CompanySize.MEDIUM  # Conservative estimate

        return None


class RevenueEstimator:
    """Estimate company revenue based on various indicators."""

    def __init__(self):
        # Revenue ranges for each category (in USD)
        self.revenue_ranges = {
            RevenueRange.UNDER_1M: (0, 1_000_000),
            RevenueRange.RANGE_1M_10M: (1_000_000, 10_000_000),
            RevenueRange.RANGE_10M_50M: (10_000_000, 50_000_000),
            RevenueRange.RANGE_50M_100M: (50_000_000, 100_000_000),
            RevenueRange.RANGE_100M_500M: (100_000_000, 500_000_000),
            RevenueRange.RANGE_500M_1B: (500_000_000, 1_000_000_000),
            RevenueRange.OVER_1B: (1_000_000_000, float("inf")),
        }

        # Industry revenue multipliers (revenue per employee)
        self.industry_multipliers = {
            "technology": 200_000,
            "finance": 300_000,
            "healthcare": 150_000,
            "consulting": 180_000,
            "manufacturing": 120_000,
            "retail": 80_000,
            "education": 60_000,
            "nonprofit": 40_000,
        }

        # Size-based revenue estimates
        self.size_revenue_estimates = {
            CompanySize.STARTUP: (0, 500_000),
            CompanySize.SMALL: (100_000, 5_000_000),
            CompanySize.MEDIUM: (1_000_000, 50_000_000),
            CompanySize.LARGE: (10_000_000, 500_000_000),
            CompanySize.ENTERPRISE: (50_000_000, float("inf")),
        }

    def estimate_revenue(self, company_data: Dict[str, Any]) -> EstimationResult:
        """Estimate company revenue from available data."""
        estimated_data = company_data.copy()
        estimation_methods = []
        confidence_scores = []
        errors: List[str] = []

        try:
            # Method 1: Employee count and industry
            employee_count = company_data.get("employee_count")
            industry = company_data.get("industry", "").lower()

            if employee_count and industry:
                revenue_from_employees = self._revenue_from_employees_and_industry(
                    employee_count, industry
                )
                if revenue_from_employees:
                    estimated_data["estimated_revenue_range"] = revenue_from_employees
                    estimation_methods.append("employee_industry_model")
                    confidence_scores.append(0.7)

            # Method 2: Company size category
            company_size = company_data.get("estimated_size")
            if company_size:
                revenue_from_size = self._revenue_from_size(company_size)
                if revenue_from_size:
                    if "estimated_revenue_range" not in estimated_data:
                        estimated_data["estimated_revenue_range"] = revenue_from_size
                    estimation_methods.append("size_based_model")
                    confidence_scores.append(0.5)

            # Method 3: Technology stack analysis
            technologies = company_data.get("technologies", [])
            if technologies:
                revenue_from_tech = self._revenue_from_technologies(technologies)
                if revenue_from_tech:
                    if "estimated_revenue_range" not in estimated_data:
                        estimated_data["estimated_revenue_range"] = revenue_from_tech
                    estimation_methods.append("technology_analysis")
                    confidence_scores.append(0.4)

            # Method 4: Funding information (if available)
            funding = company_data.get("funding_amount")
            if funding:
                revenue_from_funding = self._revenue_from_funding(funding)
                if revenue_from_funding:
                    if "estimated_revenue_range" not in estimated_data:
                        estimated_data["estimated_revenue_range"] = revenue_from_funding
                    estimation_methods.append("funding_based_model")
                    confidence_scores.append(0.6)

            # Calculate overall confidence
            confidence = (
                statistics.mean(confidence_scores) if confidence_scores else 0.0
            )

            # Add revenue category
            if "estimated_revenue_range" in estimated_data:
                revenue_range = estimated_data["estimated_revenue_range"]
                category = self._categorize_revenue_range(revenue_range)
                estimated_data["estimated_revenue_category"] = category.value

            return EstimationResult(
                original_data=company_data,
                estimated_data=estimated_data,
                confidence_score=confidence,
                estimation_methods=estimation_methods,
                metadata={
                    "method_count": len(estimation_methods),
                    "confidence_scores": confidence_scores,
                },
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Error estimating revenue: {e}")
            errors.append(f"Revenue estimation failed: {str(e)}")

            return EstimationResult(
                original_data=company_data,
                estimated_data=estimated_data,
                confidence_score=0.0,
                estimation_methods=estimation_methods,
                errors=errors,
            )

    def _revenue_from_employees_and_industry(
        self, employee_count: int, industry: str
    ) -> Optional[Dict[str, int]]:
        """Estimate revenue from employee count and industry."""
        # Find industry multiplier
        multiplier = self.industry_multipliers.get(
            industry, 150_000
        )  # Default multiplier

        # Calculate base revenue estimate
        base_revenue = employee_count * multiplier

        # Add variance (±50%)
        min_revenue = int(base_revenue * 0.5)
        max_revenue = int(base_revenue * 1.5)

        return {"min": min_revenue, "max": max_revenue, "estimate": base_revenue}

    def _revenue_from_size(self, company_size: str) -> Optional[Dict[str, int]]:
        """Estimate revenue from company size category."""
        try:
            size_enum = CompanySize(company_size)
            min_revenue, max_revenue = self.size_revenue_estimates[size_enum]

            # Calculate midpoint estimate
            if max_revenue == float("inf"):
                estimate = min_revenue * 2  # Conservative estimate for large companies
                max_revenue = min_revenue * 10
            else:
                estimate = (min_revenue + max_revenue) // 2

            return {
                "min": int(min_revenue),
                "max": int(max_revenue),
                "estimate": int(estimate),
            }
        except ValueError:
            return None

    def _revenue_from_technologies(
        self, technologies: List[str]
    ) -> Optional[Dict[str, int]]:
        """Estimate revenue from technology stack complexity."""
        tech_text = " ".join(technologies).lower()

        # Technology sophistication indicators
        enterprise_tech = [
            "kubernetes",
            "microservices",
            "enterprise",
            "oracle",
            "salesforce",
            "sap",
            "aws enterprise",
            "azure enterprise",
        ]

        mid_tier_tech = [
            "aws",
            "azure",
            "google cloud",
            "docker",
            "redis",
            "postgresql",
            "mongodb",
            "elasticsearch",
        ]

        basic_tech = [
            "wordpress",
            "shopify",
            "squarespace",
            "wix",
            "basic hosting",
            "shared hosting",
        ]

        enterprise_score = sum(1 for tech in enterprise_tech if tech in tech_text)
        mid_tier_score = sum(1 for tech in mid_tier_tech if tech in tech_text)
        basic_score = sum(1 for tech in basic_tech if tech in tech_text)

        if enterprise_score > 0:
            return {"min": 10_000_000, "max": 500_000_000, "estimate": 50_000_000}
        elif mid_tier_score > 2:
            return {"min": 1_000_000, "max": 50_000_000, "estimate": 10_000_000}
        elif mid_tier_score > 0:
            return {"min": 100_000, "max": 10_000_000, "estimate": 2_000_000}
        elif basic_score > 0:
            return {"min": 10_000, "max": 1_000_000, "estimate": 200_000}

        return None

    def _revenue_from_funding(self, funding_amount: int) -> Optional[Dict[str, int]]:
        """Estimate revenue from funding amount."""
        # Typical revenue multiples for funding
        # Early stage: 0.1-0.5x funding
        # Growth stage: 0.5-2x funding
        # Late stage: 1-5x funding

        if funding_amount < 1_000_000:  # Seed/early stage
            multiplier_range = (0.1, 0.5)
        elif funding_amount < 10_000_000:  # Series A/B
            multiplier_range = (0.3, 1.5)
        else:  # Later stage
            multiplier_range = (0.8, 3.0)

        min_revenue = int(funding_amount * multiplier_range[0])
        max_revenue = int(funding_amount * multiplier_range[1])
        estimate = int(funding_amount * statistics.mean(multiplier_range))

        return {"min": min_revenue, "max": max_revenue, "estimate": estimate}

    def _categorize_revenue_range(self, revenue_range: Dict[str, int]) -> RevenueRange:
        """Categorize revenue range into predefined categories."""
        estimate = revenue_range.get("estimate", revenue_range.get("max", 0))

        for category, (min_val, max_val) in self.revenue_ranges.items():
            if min_val <= estimate <= max_val:
                return RevenueRange(category) if isinstance(category, str) else category

        return RevenueRange.UNDER_1M


class DataEstimator:
    """Main estimation orchestrator."""

    def __init__(self):
        self.size_estimator = CompanySizeEstimator()
        self.revenue_estimator = RevenueEstimator()

    def estimate_company_metrics(
        self, company_data: Dict[str, Any]
    ) -> EstimationResult:
        """Estimate various company metrics."""
        try:
            # Start with size estimation
            size_result = self.size_estimator.estimate_size(company_data)

            # Use size estimation for revenue estimation
            enhanced_data = size_result.estimated_data.copy()
            revenue_result = self.revenue_estimator.estimate_revenue(enhanced_data)

            # Combine results
            final_data = revenue_result.estimated_data.copy()

            # Combine estimation methods and confidence scores
            all_methods = (
                size_result.estimation_methods + revenue_result.estimation_methods
            )
            all_errors = size_result.errors + revenue_result.errors

            # Calculate combined confidence
            size_confidence = size_result.confidence_score
            revenue_confidence = revenue_result.confidence_score

            if size_confidence > 0 and revenue_confidence > 0:
                combined_confidence = (size_confidence + revenue_confidence) / 2
            elif size_confidence > 0:
                combined_confidence = (
                    size_confidence * 0.8
                )  # Slight penalty for missing revenue
            elif revenue_confidence > 0:
                combined_confidence = (
                    revenue_confidence * 0.8
                )  # Slight penalty for missing size
            else:
                combined_confidence = 0.0

            return EstimationResult(
                original_data=company_data,
                estimated_data=final_data,
                confidence_score=combined_confidence,
                estimation_methods=all_methods,
                metadata={
                    "size_estimation": size_result.metadata,
                    "revenue_estimation": revenue_result.metadata,
                    "total_methods": len(all_methods),
                },
                errors=all_errors,
            )

        except Exception as e:
            logger.error(f"Error in company metrics estimation: {e}")
            return EstimationResult(
                original_data=company_data,
                estimated_data=company_data.copy(),
                confidence_score=0.0,
                estimation_methods=[],
                errors=[f"Estimation failed: {str(e)}"],
            )

    def estimate_contact_value(
        self,
        contact_data: Dict[str, Any],
        company_data: Optional[Dict[str, Any]] = None,
    ) -> EstimationResult:
        """Estimate contact value/priority based on role and company."""
        estimated_data = contact_data.copy()
        estimation_methods = []
        errors: List[str] = []

        try:
            # Base score
            value_score = 0.5

            # Job title analysis
            job_title = contact_data.get("job_title", "").lower()

            # Executive roles get highest scores
            executive_keywords = [
                "ceo",
                "cto",
                "cfo",
                "coo",
                "president",
                "founder",
                "owner",
            ]
            if any(keyword in job_title for keyword in executive_keywords):
                value_score += 0.4
                estimation_methods.append("executive_role")

            # Decision maker roles
            decision_maker_keywords = [
                "director",
                "vp",
                "vice president",
                "head",
                "manager",
            ]
            if any(keyword in job_title for keyword in decision_maker_keywords):
                value_score += 0.3
                estimation_methods.append("decision_maker_role")

            # Influencer roles
            influencer_keywords = ["lead", "senior", "principal", "architect"]
            if any(keyword in job_title for keyword in influencer_keywords):
                value_score += 0.2
                estimation_methods.append("influencer_role")

            # Company size factor
            if company_data:
                company_size = company_data.get("estimated_size")
                if company_size == CompanySize.ENTERPRISE.value:
                    value_score += 0.2
                elif company_size == CompanySize.LARGE.value:
                    value_score += 0.15
                elif company_size == CompanySize.MEDIUM.value:
                    value_score += 0.1
                estimation_methods.append("company_size_factor")

            # Seniority level factor
            seniority = contact_data.get("seniority_level", "").lower()
            if seniority == "executive":
                value_score += 0.15
            elif seniority == "senior":
                value_score += 0.1
            elif seniority == "mid":
                value_score += 0.05

            if seniority:
                estimation_methods.append("seniority_analysis")

            # Normalize score
            value_score = min(value_score, 1.0)

            # Categorize contact value
            if value_score >= 0.8:
                contact_priority = "high"
            elif value_score >= 0.6:
                contact_priority = "medium"
            else:
                contact_priority = "low"

            estimated_data["estimated_value_score"] = value_score
            estimated_data["contact_priority"] = contact_priority

            confidence = 0.7 if estimation_methods else 0.1

            return EstimationResult(
                original_data=contact_data,
                estimated_data=estimated_data,
                confidence_score=confidence,
                estimation_methods=estimation_methods,
                metadata={"value_score": value_score, "priority": contact_priority},
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Error estimating contact value: {e}")
            errors.append(f"Contact value estimation failed: {str(e)}")

            return EstimationResult(
                original_data=contact_data,
                estimated_data=estimated_data,
                confidence_score=0.0,
                estimation_methods=estimation_methods,
                errors=errors,
            )
