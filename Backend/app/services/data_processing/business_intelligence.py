"""Business Intelligence Module for Lead Generation System.

This module provides comprehensive business intelligence capabilities including:
- Growth signal detection and analysis
- Technology stack analysis and insights
- Pain point identification
- Competitive landscape analysis
- Market trend analysis
- Business opportunity scoring
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GrowthSignalType(Enum):
    """Types of growth signals."""

    HIRING = "hiring"
    FUNDING = "funding"
    EXPANSION = "expansion"
    NEW_PRODUCT = "new_product"
    PARTNERSHIP = "partnership"
    ACQUISITION = "acquisition"
    IPO = "ipo"
    REVENUE_GROWTH = "revenue_growth"
    MARKET_EXPANSION = "market_expansion"
    OFFICE_EXPANSION = "office_expansion"
    TEAM_GROWTH = "team_growth"
    TECHNOLOGY_UPGRADE = "technology_upgrade"


class PainPointCategory(Enum):
    """Categories of business pain points."""

    SCALING = "scaling"
    TECHNOLOGY = "technology"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    COST_OPTIMIZATION = "cost_optimization"
    TALENT_ACQUISITION = "talent_acquisition"
    CUSTOMER_ACQUISITION = "customer_acquisition"
    DATA_MANAGEMENT = "data_management"
    AUTOMATION = "automation"
    DIGITAL_TRANSFORMATION = "digital_transformation"


class CompetitorRelationship(Enum):
    """Types of competitive relationships."""

    DIRECT_COMPETITOR = "direct_competitor"
    INDIRECT_COMPETITOR = "indirect_competitor"
    SUBSTITUTE = "substitute"
    COMPLEMENTARY = "complementary"
    PARTNER = "partner"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"


class TechnologyMaturity(Enum):
    """Technology maturity levels."""

    EMERGING = "emerging"
    GROWING = "growing"
    MATURE = "mature"
    DECLINING = "declining"
    LEGACY = "legacy"


@dataclass
class GrowthSignal:
    """Represents a detected growth signal."""

    signal_type: GrowthSignalType
    description: str
    confidence: float  # 0.0 to 1.0
    source: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    impact_score: float = 0.0  # 0.0 to 1.0
    timeframe: Optional[str] = None
    evidence: List[str] = field(default_factory=list)


@dataclass
class PainPoint:
    """Represents an identified business pain point."""

    category: PainPointCategory
    description: str
    confidence: float  # 0.0 to 1.0
    source: str
    severity: float = 0.5  # 0.0 to 1.0
    urgency: float = 0.5  # 0.0 to 1.0
    detected_at: datetime = field(default_factory=datetime.utcnow)
    keywords: List[str] = field(default_factory=list)
    potential_solutions: List[str] = field(default_factory=list)


@dataclass
class CompetitorInfo:
    """Information about a competitor."""

    name: str
    relationship: CompetitorRelationship
    market_position: str  # "leader", "challenger", "follower", "niche"
    confidence: float  # 0.0 to 1.0
    source: str
    website: Optional[str] = None
    description: Optional[str] = None
    market_share: Optional[float] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class TechnologyInsight:
    """Insights about technology usage."""

    technology: str
    category: str
    maturity: TechnologyMaturity
    adoption_trend: str  # "increasing", "stable", "decreasing"
    market_penetration: float  # 0.0 to 1.0
    competitive_advantage: float  # 0.0 to 1.0
    risk_level: float  # 0.0 to 1.0
    alternatives: List[str] = field(default_factory=list)
    integration_complexity: float = 0.5  # 0.0 to 1.0


@dataclass
class BusinessIntelligenceResult:
    """Complete business intelligence analysis result."""

    company_id: str
    analysis_date: datetime = field(default_factory=datetime.utcnow)
    growth_signals: List[GrowthSignal] = field(default_factory=list)
    pain_points: List[PainPoint] = field(default_factory=list)
    competitors: List[CompetitorInfo] = field(default_factory=list)
    technology_insights: List[TechnologyInsight] = field(default_factory=list)
    overall_growth_score: float = 0.0
    opportunity_score: float = 0.0
    risk_score: float = 0.0
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GrowthSignalDetector:
    """Detects growth signals from company data."""

    # Growth signal patterns
    HIRING_PATTERNS = [
        r"hiring\s+\d+",
        r"\d+\s+new\s+hires?",
        r"expanding\s+team",
        r"job\s+openings?",
        r"we[''']re\s+hiring",
        r"join\s+our\s+team",
        r"career\s+opportunities",
        r"talent\s+acquisition",
        r"headcount\s+growth",
        r"recruiting",
    ]

    FUNDING_PATTERNS = [
        r"series\s+[a-z]\s+funding",
        r"\$\d+[mk]?\s+raised?",
        r"investment\s+round",
        r"venture\s+capital",
        r"seed\s+funding",
        r"angel\s+investment",
        r"ipo\s+filing",
        r"public\s+offering",
        r"funding\s+announcement",
        r"capital\s+raise",
    ]

    EXPANSION_PATTERNS = [
        r"new\s+office",
        r"expanding\s+to",
        r"international\s+expansion",
        r"global\s+presence",
        r"new\s+location",
        r"opening\s+in",
        r"market\s+expansion",
        r"geographic\s+growth",
    ]

    PRODUCT_PATTERNS = [
        r"new\s+product",
        r"product\s+launch",
        r"feature\s+release",
        r"beta\s+launch",
        r"coming\s+soon",
        r"product\s+update",
        r"innovation",
        r"breakthrough",
        r"next\s+generation",
    ]

    PARTNERSHIP_PATTERNS = [
        r"partnership\s+with",
        r"strategic\s+alliance",
        r"collaboration",
        r"joint\s+venture",
        r"integration\s+with",
        r"partner\s+with",
        r"ecosystem\s+partner",
        r"technology\s+partner",
    ]

    ACQUISITION_PATTERNS = [
        r"acquired\s+by",
        r"acquisition\s+of",
        r"merger\s+with",
        r"bought\s+by",
        r"purchased\s+by",
        r"takeover",
        r"consolidation",
        r"strategic\s+acquisition",
    ]

    @classmethod
    def detect_growth_signals(cls, company_data: Dict[str, Any]) -> List[GrowthSignal]:
        """Detect growth signals from company data."""
        signals = []

        # Analyze description and news
        text_sources = [
            (company_data.get("description", ""), "company_description"),
            (company_data.get("about", ""), "about_section"),
            (" ".join(company_data.get("news", [])), "news_articles"),
            (" ".join(company_data.get("press_releases", [])), "press_releases"),
            (company_data.get("recent_updates", ""), "recent_updates"),
        ]

        for text, source in text_sources:
            if not text:
                continue

            text_lower = text.lower()

            # Detect hiring signals
            signals.extend(cls._detect_hiring_signals(text_lower, source))

            # Detect funding signals
            signals.extend(cls._detect_funding_signals(text_lower, source))

            # Detect expansion signals
            signals.extend(cls._detect_expansion_signals(text_lower, source))

            # Detect product signals
            signals.extend(cls._detect_product_signals(text_lower, source))

            # Detect partnership signals
            signals.extend(cls._detect_partnership_signals(text_lower, source))

            # Detect acquisition signals
            signals.extend(cls._detect_acquisition_signals(text_lower, source))

        # Analyze employee count growth
        signals.extend(cls._detect_employee_growth(company_data))

        # Analyze technology adoption
        signals.extend(cls._detect_technology_signals(company_data))

        return signals

    @classmethod
    def _detect_hiring_signals(cls, text: str, source: str) -> List[GrowthSignal]:
        """Detect hiring-related growth signals."""
        signals = []

        for pattern in cls.HIRING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                confidence = 0.7 if "hiring" in match.group().lower() else 0.6
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.HIRING,
                        description=f"Hiring activity detected: {match.group()}",
                        confidence=confidence,
                        source=source,
                        impact_score=0.6,
                        evidence=[match.group()],
                    )
                )

        return signals

    @classmethod
    def _detect_funding_signals(cls, text: str, source: str) -> List[GrowthSignal]:
        """Detect funding-related growth signals."""
        signals = []

        for pattern in cls.FUNDING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                confidence = 0.8 if "funding" in match.group().lower() else 0.7
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.FUNDING,
                        description=f"Funding activity detected: {match.group()}",
                        confidence=confidence,
                        source=source,
                        impact_score=0.8,
                        evidence=[match.group()],
                    )
                )

        return signals

    @classmethod
    def _detect_expansion_signals(cls, text: str, source: str) -> List[GrowthSignal]:
        """Detect expansion-related growth signals."""
        signals = []

        for pattern in cls.EXPANSION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.EXPANSION,
                        description=f"Expansion activity detected: {match.group()}",
                        confidence=0.7,
                        source=source,
                        impact_score=0.7,
                        evidence=[match.group()],
                    )
                )

        return signals

    @classmethod
    def _detect_product_signals(cls, text: str, source: str) -> List[GrowthSignal]:
        """Detect product-related growth signals."""
        signals = []

        for pattern in cls.PRODUCT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.NEW_PRODUCT,
                        description=f"Product development detected: {match.group()}",
                        confidence=0.6,
                        source=source,
                        impact_score=0.5,
                        evidence=[match.group()],
                    )
                )

        return signals

    @classmethod
    def _detect_partnership_signals(cls, text: str, source: str) -> List[GrowthSignal]:
        """Detect partnership-related growth signals."""
        signals = []

        for pattern in cls.PARTNERSHIP_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.PARTNERSHIP,
                        description=f"Partnership activity detected: {match.group()}",
                        confidence=0.7,
                        source=source,
                        impact_score=0.6,
                        evidence=[match.group()],
                    )
                )

        return signals

    @classmethod
    def _detect_acquisition_signals(cls, text: str, source: str) -> List[GrowthSignal]:
        """Detect acquisition-related growth signals."""
        signals = []

        for pattern in cls.ACQUISITION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.ACQUISITION,
                        description=f"Acquisition activity detected: {match.group()}",
                        confidence=0.8,
                        source=source,
                        impact_score=0.7,
                        evidence=[match.group()],
                    )
                )

        return signals

    @classmethod
    def _detect_employee_growth(
        cls, company_data: Dict[str, Any]
    ) -> List[GrowthSignal]:
        """Detect employee growth signals."""
        signals = []

        current_count = company_data.get("employee_count")
        previous_count = company_data.get("previous_employee_count")

        if current_count and previous_count and current_count > previous_count:
            growth_rate = (current_count - previous_count) / previous_count
            if growth_rate > 0.1:  # 10% growth
                signals.append(
                    GrowthSignal(
                        signal_type=GrowthSignalType.TEAM_GROWTH,
                        description=f"Employee growth: {previous_count} to {current_count} ({growth_rate:.1%})",
                        confidence=0.9,
                        source="employee_data",
                        impact_score=min(growth_rate, 1.0),
                        evidence=[f"Employee count increased by {growth_rate:.1%}"],
                    )
                )

        return signals

    @classmethod
    def _detect_technology_signals(
        cls, company_data: Dict[str, Any]
    ) -> List[GrowthSignal]:
        """Detect technology adoption signals."""
        signals: List[GrowthSignal] = []

        technologies = company_data.get("technologies", [])
        if not technologies:
            return signals

        # Modern/emerging technologies indicate growth
        modern_tech = [
            "kubernetes",
            "docker",
            "microservices",
            "serverless",
            "machine learning",
            "ai",
            "blockchain",
            "cloud native",
            "react",
            "vue",
            "angular",
            "node.js",
            "python",
            "go",
            "tensorflow",
            "pytorch",
            "aws",
            "azure",
            "gcp",
        ]

        tech_text = " ".join(technologies).lower()
        modern_count = sum(1 for tech in modern_tech if tech in tech_text)

        if modern_count >= 3:
            signals.append(
                GrowthSignal(
                    signal_type=GrowthSignalType.TECHNOLOGY_UPGRADE,
                    description=f"Modern technology adoption detected ({modern_count} technologies)",
                    confidence=0.6,
                    source="technology_stack",
                    impact_score=min(modern_count / 10, 1.0),
                    evidence=[f"Uses {modern_count} modern technologies"],
                )
            )

        return signals


class PainPointDetector:
    """Detects business pain points from company data."""

    # Pain point patterns by category
    SCALING_PATTERNS = [
        r"scaling\s+challenges?",
        r"growth\s+pains?",
        r"capacity\s+issues?",
        r"infrastructure\s+limitations?",
        r"performance\s+bottlenecks?",
        r"resource\s+constraints?",
        r"scalability\s+concerns?",
    ]

    TECHNOLOGY_PATTERNS = [
        r"legacy\s+systems?",
        r"technical\s+debt",
        r"outdated\s+technology",
        r"system\s+integration",
        r"modernization",
        r"digital\s+transformation",
        r"technology\s+upgrade",
        r"platform\s+migration",
    ]

    SECURITY_PATTERNS = [
        r"security\s+concerns?",
        r"data\s+breach",
        r"cybersecurity",
        r"compliance\s+issues?",
        r"privacy\s+concerns?",
        r"vulnerability",
        r"security\s+audit",
        r"penetration\s+testing",
    ]

    INTEGRATION_PATTERNS = [
        r"integration\s+challenges?",
        r"data\s+silos?",
        r"system\s+fragmentation",
        r"api\s+limitations?",
        r"connectivity\s+issues?",
        r"interoperability",
        r"data\s+synchronization",
        r"workflow\s+automation",
    ]

    PERFORMANCE_PATTERNS = [
        r"performance\s+issues?",
        r"slow\s+response",
        r"downtime",
        r"latency\s+problems?",
        r"system\s+crashes?",
        r"reliability\s+concerns?",
        r"uptime\s+challenges?",
        r"load\s+balancing",
    ]

    COST_PATTERNS = [
        r"cost\s+optimization",
        r"budget\s+constraints?",
        r"expensive\s+infrastructure",
        r"operational\s+costs?",
        r"resource\s+efficiency",
        r"cost\s+reduction",
        r"roi\s+concerns?",
        r"financial\s+pressure",
    ]

    TALENT_PATTERNS = [
        r"talent\s+shortage",
        r"hiring\s+challenges?",
        r"skill\s+gaps?",
        r"recruitment\s+difficulties",
        r"retention\s+issues?",
        r"training\s+needs?",
        r"expertise\s+gaps?",
        r"team\s+building",
    ]

    DATA_PATTERNS = [
        r"data\s+quality",
        r"data\s+governance",
        r"data\s+management",
        r"analytics\s+challenges?",
        r"reporting\s+issues?",
        r"data\s+visualization",
        r"business\s+intelligence",
        r"data\s+strategy",
    ]

    @classmethod
    def detect_pain_points(cls, company_data: Dict[str, Any]) -> List[PainPoint]:
        """Detect pain points from company data."""
        pain_points = []

        # Analyze text sources
        text_sources = [
            (company_data.get("description", ""), "company_description"),
            (company_data.get("challenges", ""), "challenges_section"),
            (" ".join(company_data.get("job_postings", [])), "job_postings"),
            (" ".join(company_data.get("news", [])), "news_articles"),
            (company_data.get("about", ""), "about_section"),
        ]

        for text, source in text_sources:
            if not text:
                continue

            text_lower = text.lower()

            # Detect different categories of pain points
            pain_points.extend(cls._detect_scaling_pain_points(text_lower, source))
            pain_points.extend(cls._detect_technology_pain_points(text_lower, source))
            pain_points.extend(cls._detect_security_pain_points(text_lower, source))
            pain_points.extend(cls._detect_integration_pain_points(text_lower, source))
            pain_points.extend(cls._detect_performance_pain_points(text_lower, source))
            pain_points.extend(cls._detect_cost_pain_points(text_lower, source))
            pain_points.extend(cls._detect_talent_pain_points(text_lower, source))
            pain_points.extend(cls._detect_data_pain_points(text_lower, source))

        # Analyze technology stack for pain points
        pain_points.extend(cls._analyze_technology_pain_points(company_data))

        # Analyze company size for scaling pain points
        pain_points.extend(cls._analyze_size_based_pain_points(company_data))

        return pain_points

    @classmethod
    def _detect_scaling_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect scaling-related pain points."""
        pain_points = []

        for pattern in cls.SCALING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.SCALING,
                        description=f"Scaling challenge identified: {match.group()}",
                        confidence=0.7,
                        source=source,
                        severity=0.7,
                        urgency=0.6,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Cloud infrastructure scaling",
                            "Microservices architecture",
                            "Load balancing solutions",
                            "Performance optimization",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_technology_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect technology-related pain points."""
        pain_points = []

        for pattern in cls.TECHNOLOGY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.TECHNOLOGY,
                        description=f"Technology challenge identified: {match.group()}",
                        confidence=0.8,
                        source=source,
                        severity=0.6,
                        urgency=0.5,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Technology modernization",
                            "System migration",
                            "API development",
                            "Digital transformation strategy",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_security_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect security-related pain points."""
        pain_points = []

        for pattern in cls.SECURITY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.SECURITY,
                        description=f"Security concern identified: {match.group()}",
                        confidence=0.8,
                        source=source,
                        severity=0.8,
                        urgency=0.7,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Security audit",
                            "Penetration testing",
                            "Compliance framework",
                            "Security training",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_integration_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect integration-related pain points."""
        pain_points = []

        for pattern in cls.INTEGRATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.INTEGRATION,
                        description=f"Integration challenge identified: {match.group()}",
                        confidence=0.7,
                        source=source,
                        severity=0.6,
                        urgency=0.6,
                        keywords=[match.group()],
                        potential_solutions=[
                            "API integration platform",
                            "Data pipeline automation",
                            "Middleware solutions",
                            "System integration strategy",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_performance_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect performance-related pain points."""
        pain_points = []

        for pattern in cls.PERFORMANCE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.PERFORMANCE,
                        description=f"Performance issue identified: {match.group()}",
                        confidence=0.7,
                        source=source,
                        severity=0.7,
                        urgency=0.8,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Performance monitoring",
                            "Code optimization",
                            "Infrastructure scaling",
                            "Caching solutions",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_cost_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect cost-related pain points."""
        pain_points = []

        for pattern in cls.COST_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.COST_OPTIMIZATION,
                        description=f"Cost concern identified: {match.group()}",
                        confidence=0.6,
                        source=source,
                        severity=0.5,
                        urgency=0.6,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Cost optimization audit",
                            "Resource efficiency analysis",
                            "Cloud cost management",
                            "Process automation",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_talent_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect talent-related pain points."""
        pain_points = []

        for pattern in cls.TALENT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.TALENT_ACQUISITION,
                        description=f"Talent challenge identified: {match.group()}",
                        confidence=0.7,
                        source=source,
                        severity=0.6,
                        urgency=0.5,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Recruitment strategy",
                            "Training programs",
                            "Talent retention initiatives",
                            "Skills development",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _detect_data_pain_points(cls, text: str, source: str) -> List[PainPoint]:
        """Detect data-related pain points."""
        pain_points = []

        for pattern in cls.DATA_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain_points.append(
                    PainPoint(
                        category=PainPointCategory.DATA_MANAGEMENT,
                        description=f"Data challenge identified: {match.group()}",
                        confidence=0.7,
                        source=source,
                        severity=0.6,
                        urgency=0.5,
                        keywords=[match.group()],
                        potential_solutions=[
                            "Data governance framework",
                            "Analytics platform",
                            "Data quality tools",
                            "Business intelligence solution",
                        ],
                    )
                )

        return pain_points

    @classmethod
    def _analyze_technology_pain_points(
        cls, company_data: Dict[str, Any]
    ) -> List[PainPoint]:
        """Analyze technology stack for potential pain points."""
        pain_points: List[PainPoint] = []

        technologies = company_data.get("technologies", [])
        if not technologies:
            return pain_points

        tech_text = " ".join(technologies).lower()

        # Check for legacy technologies
        legacy_tech = [
            "jquery",
            "php",
            "mysql",
            "apache",
            "windows server",
            "internet explorer",
            "flash",
            "silverlight",
            "asp.net",
        ]

        legacy_count = sum(1 for tech in legacy_tech if tech in tech_text)

        if legacy_count >= 2:
            pain_points.append(
                PainPoint(
                    category=PainPointCategory.TECHNOLOGY,
                    description=f"Legacy technology stack detected ({legacy_count} legacy technologies)",
                    confidence=0.6,
                    source="technology_analysis",
                    severity=0.5,
                    urgency=0.4,
                    keywords=[f"{legacy_count} legacy technologies"],
                    potential_solutions=[
                        "Technology modernization roadmap",
                        "Gradual migration strategy",
                        "Modern framework adoption",
                    ],
                )
            )

        return pain_points

    @classmethod
    def _analyze_size_based_pain_points(
        cls, company_data: Dict[str, Any]
    ) -> List[PainPoint]:
        """Analyze company size for typical pain points."""
        pain_points: List[PainPoint] = []

        employee_count = company_data.get("employee_count")
        if not employee_count:
            return pain_points

        # Scaling pain points for growing companies
        if 50 <= employee_count <= 200:
            pain_points.append(
                PainPoint(
                    category=PainPointCategory.SCALING,
                    description="Mid-size company scaling challenges",
                    confidence=0.5,
                    source="size_analysis",
                    severity=0.6,
                    urgency=0.5,
                    keywords=["scaling", "growth"],
                    potential_solutions=[
                        "Process standardization",
                        "Infrastructure scaling",
                        "Team structure optimization",
                    ],
                )
            )

        return pain_points


class CompetitiveLandscapeAnalyzer:
    """Analyzes competitive landscape from company data."""

    # Common competitor indicators
    COMPETITOR_KEYWORDS = [
        "competitor",
        "alternative",
        "vs",
        "versus",
        "compared to",
        "similar to",
        "like",
        "rival",
        "competing",
        "market leader",
    ]

    # Market position indicators
    LEADER_INDICATORS = [
        "market leader",
        "industry leader",
        "leading",
        "#1",
        "number one",
        "dominant",
        "largest",
        "biggest",
        "top player",
    ]

    CHALLENGER_INDICATORS = [
        "challenger",
        "growing",
        "emerging",
        "rising",
        "up-and-coming",
        "fast-growing",
        "disruptor",
        "innovative",
    ]

    @classmethod
    def analyze_competitive_landscape(
        cls, company_data: Dict[str, Any]
    ) -> List[CompetitorInfo]:
        """Analyze competitive landscape from company data."""
        competitors = []

        # Analyze text sources for competitor mentions
        text_sources = [
            (company_data.get("description", ""), "company_description"),
            (company_data.get("about", ""), "about_section"),
            (" ".join(company_data.get("news", [])), "news_articles"),
            (company_data.get("competitive_analysis", ""), "competitive_analysis"),
        ]

        for text, source in text_sources:
            if not text:
                continue

            competitors.extend(cls._extract_competitors_from_text(text, source))

        # Analyze industry for known competitors
        industry = company_data.get("industry", "")
        if industry:
            competitors.extend(cls._get_industry_competitors(industry))

        # Analyze technology stack for competitors
        technologies = company_data.get("technologies", [])
        if technologies:
            competitors.extend(cls._get_technology_competitors(technologies))

        # Remove duplicates and merge information
        competitors = cls._merge_competitor_info(competitors)

        return competitors

    @classmethod
    def _extract_competitors_from_text(
        cls, text: str, source: str
    ) -> List[CompetitorInfo]:
        """Extract competitor information from text."""
        competitors = []
        text_lower = text.lower()

        # Look for competitor mentions
        for keyword in cls.COMPETITOR_KEYWORDS:
            pattern = rf"{keyword}\s+([A-Z][a-zA-Z\s]+?)(?:\s|\.|,|$)"
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                competitor_name = match.group(1).strip()
                if len(competitor_name) > 2 and len(competitor_name) < 50:
                    # Determine market position
                    market_position = cls._determine_market_position(
                        text_lower, competitor_name.lower()
                    )

                    # Determine relationship type
                    relationship = cls._determine_relationship(text_lower, keyword)

                    competitors.append(
                        CompetitorInfo(
                            name=competitor_name,
                            relationship=relationship,
                            market_position=market_position,
                            confidence=0.6,
                            source=source,
                        )
                    )

        return competitors

    @classmethod
    def _determine_market_position(cls, text: str, competitor_name: str) -> str:
        """Determine market position of competitor."""
        context = cls._get_context_around_name(text, competitor_name)

        for indicator in cls.LEADER_INDICATORS:
            if indicator in context:
                return "leader"

        for indicator in cls.CHALLENGER_INDICATORS:
            if indicator in context:
                return "challenger"

        return "follower"

    @classmethod
    def _determine_relationship(cls, text: str, keyword: str) -> CompetitorRelationship:
        """Determine relationship type based on context."""
        if keyword in ["competitor", "rival", "competing", "vs", "versus"]:
            return CompetitorRelationship.DIRECT_COMPETITOR
        elif keyword in ["alternative", "similar to", "like"]:
            return CompetitorRelationship.INDIRECT_COMPETITOR
        else:
            return CompetitorRelationship.DIRECT_COMPETITOR

    @classmethod
    def _get_context_around_name(cls, text: str, name: str, window: int = 50) -> str:
        """Get context around a competitor name."""
        index = text.find(name)
        if index == -1:
            return ""

        start = max(0, index - window)
        end = min(len(text), index + len(name) + window)

        return text[start:end]

    @classmethod
    def _get_industry_competitors(cls, industry: str) -> List[CompetitorInfo]:
        """Get known competitors based on industry."""
        # This would typically connect to a database of known competitors
        # For now, return empty list
        return []

    @classmethod
    def _get_technology_competitors(
        cls, technologies: List[str]
    ) -> List[CompetitorInfo]:
        """Get competitors based on technology stack."""
        # This would typically analyze technology usage patterns
        # For now, return empty list
        return []

    @classmethod
    def _merge_competitor_info(
        cls, competitors: List[CompetitorInfo]
    ) -> List[CompetitorInfo]:
        """Merge duplicate competitor information."""
        merged: Dict[str, CompetitorInfo] = {}

        for competitor in competitors:
            name_key = competitor.name.lower().strip()

            if name_key in merged:
                # Merge information
                existing = merged[name_key]
                existing.confidence = max(existing.confidence, competitor.confidence)
                if competitor.market_position != "follower":
                    existing.market_position = competitor.market_position
            else:
                merged[name_key] = competitor

        return list(merged.values())


class TechnologyStackAnalyzer:
    """Analyzes technology stack for insights and trends."""

    # Technology maturity mapping
    TECHNOLOGY_MATURITY = {
        # Emerging
        "webassembly": TechnologyMaturity.EMERGING,
        "deno": TechnologyMaturity.EMERGING,
        "svelte": TechnologyMaturity.EMERGING,
        "rust": TechnologyMaturity.EMERGING,
        "edge computing": TechnologyMaturity.EMERGING,
        # Growing
        "kubernetes": TechnologyMaturity.GROWING,
        "docker": TechnologyMaturity.GROWING,
        "graphql": TechnologyMaturity.GROWING,
        "typescript": TechnologyMaturity.GROWING,
        "vue.js": TechnologyMaturity.GROWING,
        # Mature
        "react": TechnologyMaturity.MATURE,
        "node.js": TechnologyMaturity.MATURE,
        "python": TechnologyMaturity.MATURE,
        "aws": TechnologyMaturity.MATURE,
        "postgresql": TechnologyMaturity.MATURE,
        # Declining
        "angular.js": TechnologyMaturity.DECLINING,
        "backbone.js": TechnologyMaturity.DECLINING,
        "coffeescript": TechnologyMaturity.DECLINING,
        # Legacy
        "jquery": TechnologyMaturity.LEGACY,
        "flash": TechnologyMaturity.LEGACY,
        "silverlight": TechnologyMaturity.LEGACY,
        "internet explorer": TechnologyMaturity.LEGACY,
    }

    # Technology risk levels
    TECHNOLOGY_RISKS = {
        "flash": 1.0,
        "silverlight": 1.0,
        "internet explorer": 0.9,
        "jquery": 0.3,
        "php": 0.2,
        "mysql": 0.1,
    }

    # Technology competitive advantages
    COMPETITIVE_ADVANTAGES = {
        "machine learning": 0.9,
        "artificial intelligence": 0.9,
        "kubernetes": 0.8,
        "microservices": 0.8,
        "serverless": 0.7,
        "graphql": 0.7,
        "typescript": 0.6,
        "react": 0.6,
    }

    @classmethod
    def analyze_technology_stack(
        cls, company_data: Dict[str, Any]
    ) -> List[TechnologyInsight]:
        """Analyze technology stack for insights."""
        insights: List[TechnologyInsight] = []

        technologies = company_data.get("technologies", [])
        if not technologies:
            return insights

        for tech in technologies:
            tech_lower = tech.lower().strip()

            # Get technology maturity
            maturity = cls._get_technology_maturity(tech_lower)

            # Determine adoption trend
            trend = cls._get_adoption_trend(tech_lower)

            # Calculate market penetration (simplified)
            penetration = cls._estimate_market_penetration(tech_lower)

            # Calculate competitive advantage
            advantage = cls._get_competitive_advantage(tech_lower)

            # Calculate risk level
            risk = cls._get_risk_level(tech_lower)

            # Get alternatives
            alternatives = cls._get_alternatives(tech_lower)

            # Estimate integration complexity
            complexity = cls._estimate_integration_complexity(tech_lower)

            insights.append(
                TechnologyInsight(
                    technology=tech,
                    category=cls._get_technology_category(tech_lower),
                    maturity=maturity,
                    adoption_trend=trend,
                    market_penetration=penetration,
                    competitive_advantage=advantage,
                    risk_level=risk,
                    alternatives=alternatives,
                    integration_complexity=complexity,
                )
            )

        return insights

    @classmethod
    def _get_technology_maturity(cls, tech: str) -> TechnologyMaturity:
        """Get technology maturity level."""
        return cls.TECHNOLOGY_MATURITY.get(tech, TechnologyMaturity.MATURE)

    @classmethod
    def _get_adoption_trend(cls, tech: str) -> str:
        """Get technology adoption trend."""
        # Simplified trend analysis
        emerging_tech = ["rust", "deno", "svelte", "webassembly"]
        declining_tech = ["jquery", "angular.js", "backbone.js", "flash"]

        if any(t in tech for t in emerging_tech):
            return "increasing"
        elif any(t in tech for t in declining_tech):
            return "decreasing"
        else:
            return "stable"

    @classmethod
    def _estimate_market_penetration(cls, tech: str) -> float:
        """Estimate market penetration (simplified)."""
        # High penetration technologies
        high_penetration = ["javascript", "html", "css", "react", "node.js"]
        medium_penetration = ["python", "java", "aws", "docker"]

        if any(t in tech for t in high_penetration):
            return 0.8
        elif any(t in tech for t in medium_penetration):
            return 0.5
        else:
            return 0.2

    @classmethod
    def _get_competitive_advantage(cls, tech: str) -> float:
        """Get competitive advantage score."""
        return cls.COMPETITIVE_ADVANTAGES.get(tech, 0.3)

    @classmethod
    def _get_risk_level(cls, tech: str) -> float:
        """Get technology risk level."""
        return cls.TECHNOLOGY_RISKS.get(tech, 0.1)

    @classmethod
    def _get_alternatives(cls, tech: str) -> List[str]:
        """Get technology alternatives."""
        alternatives_map = {
            "react": ["vue.js", "angular", "svelte"],
            "angular": ["react", "vue.js"],
            "vue.js": ["react", "angular"],
            "mysql": ["postgresql", "mongodb"],
            "postgresql": ["mysql", "mongodb"],
            "aws": ["azure", "gcp"],
            "azure": ["aws", "gcp"],
            "gcp": ["aws", "azure"],
        }

        return alternatives_map.get(tech, [])

    @classmethod
    def _estimate_integration_complexity(cls, tech: str) -> float:
        """Estimate integration complexity."""
        # High complexity technologies
        high_complexity = ["kubernetes", "microservices", "machine learning"]
        low_complexity = ["react", "vue.js", "express"]

        if any(t in tech for t in high_complexity):
            return 0.8
        elif any(t in tech for t in low_complexity):
            return 0.3
        else:
            return 0.5

    @classmethod
    def _get_technology_category(cls, tech: str) -> str:
        """Get technology category."""
        categories = {
            "frontend": ["react", "vue", "angular", "javascript", "html", "css"],
            "backend": ["node.js", "python", "java", "go", "rust"],
            "database": ["mysql", "postgresql", "mongodb", "redis"],
            "cloud": ["aws", "azure", "gcp", "kubernetes", "docker"],
            "analytics": ["google analytics", "mixpanel", "amplitude"],
            "marketing": ["hubspot", "salesforce", "mailchimp"],
        }

        for category, techs in categories.items():
            if any(t in tech for t in techs):
                return category

        return "other"


class BusinessIntelligenceEngine:
    """Main business intelligence analysis engine."""

    def __init__(self):
        self.growth_detector = GrowthSignalDetector()
        self.pain_point_detector = PainPointDetector()
        self.competitive_analyzer = CompetitiveLandscapeAnalyzer()
        self.technology_analyzer = TechnologyStackAnalyzer()

    def analyze_company(
        self, company_data: Dict[str, Any]
    ) -> BusinessIntelligenceResult:
        """Perform comprehensive business intelligence analysis."""
        try:
            company_id = company_data.get("id", "unknown")

            # Detect growth signals
            growth_signals = self.growth_detector.detect_growth_signals(company_data)

            # Detect pain points
            pain_points = self.pain_point_detector.detect_pain_points(company_data)

            # Analyze competitive landscape
            competitors = self.competitive_analyzer.analyze_competitive_landscape(
                company_data
            )

            # Analyze technology stack
            technology_insights = self.technology_analyzer.analyze_technology_stack(
                company_data
            )

            # Calculate overall scores
            growth_score = self._calculate_growth_score(growth_signals)
            opportunity_score = self._calculate_opportunity_score(
                growth_signals, pain_points
            )
            risk_score = self._calculate_risk_score(pain_points, technology_insights)
            confidence = self._calculate_confidence(
                growth_signals, pain_points, competitors
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                growth_signals, pain_points, competitors, technology_insights
            )

            return BusinessIntelligenceResult(
                company_id=company_id,
                growth_signals=growth_signals,
                pain_points=pain_points,
                competitors=competitors,
                technology_insights=technology_insights,
                overall_growth_score=growth_score,
                opportunity_score=opportunity_score,
                risk_score=risk_score,
                confidence=confidence,
                recommendations=recommendations,
                metadata={
                    "analysis_version": "1.0",
                    "signals_detected": len(growth_signals),
                    "pain_points_identified": len(pain_points),
                    "competitors_found": len(competitors),
                    "technologies_analyzed": len(technology_insights),
                },
            )

        except Exception as e:
            logger.error(f"Error in business intelligence analysis: {str(e)}")
            return BusinessIntelligenceResult(
                company_id=company_data.get("id", "unknown"),
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _calculate_growth_score(self, growth_signals: List[GrowthSignal]) -> float:
        """Calculate overall growth score."""
        if not growth_signals:
            return 0.0

        total_score = sum(
            signal.impact_score * signal.confidence for signal in growth_signals
        )
        max_possible = len(growth_signals)

        return min(total_score / max_possible, 1.0) if max_possible > 0 else 0.0

    def _calculate_opportunity_score(
        self, growth_signals: List[GrowthSignal], pain_points: List[PainPoint]
    ) -> float:
        """Calculate business opportunity score."""
        growth_score = self._calculate_growth_score(growth_signals)

        # Pain points can indicate opportunities
        pain_opportunity = sum(pp.severity * pp.confidence for pp in pain_points)
        pain_opportunity = (
            min(pain_opportunity / len(pain_points), 1.0) if pain_points else 0.0
        )

        return (growth_score * 0.7) + (pain_opportunity * 0.3)

    def _calculate_risk_score(
        self, pain_points: List[PainPoint], technology_insights: List[TechnologyInsight]
    ) -> float:
        """Calculate business risk score."""
        # Risk from pain points
        pain_risk = sum(pp.severity * pp.urgency * pp.confidence for pp in pain_points)
        pain_risk = min(pain_risk / len(pain_points), 1.0) if pain_points else 0.0

        # Risk from technology
        tech_risk = sum(ti.risk_level for ti in technology_insights)
        tech_risk = (
            min(tech_risk / len(technology_insights), 1.0)
            if technology_insights
            else 0.0
        )

        return (pain_risk * 0.6) + (tech_risk * 0.4)

    def _calculate_confidence(
        self,
        growth_signals: List[GrowthSignal],
        pain_points: List[PainPoint],
        competitors: List[CompetitorInfo],
    ) -> float:
        """Calculate overall confidence in the analysis."""
        signal_confidence = sum(gs.confidence for gs in growth_signals)
        signal_confidence = (
            signal_confidence / len(growth_signals) if growth_signals else 0.0
        )

        pain_confidence = sum(pp.confidence for pp in pain_points)
        pain_confidence = pain_confidence / len(pain_points) if pain_points else 0.0

        competitor_confidence = sum(c.confidence for c in competitors)
        competitor_confidence = (
            competitor_confidence / len(competitors) if competitors else 0.0
        )

        # Weight by data availability
        weights = []
        confidences = []

        if growth_signals:
            weights.append(0.4)
            confidences.append(signal_confidence)

        if pain_points:
            weights.append(0.3)
            confidences.append(pain_confidence)

        if competitors:
            weights.append(0.3)
            confidences.append(competitor_confidence)

        if not weights:
            return 0.0

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        return sum(w * c for w, c in zip(weights, confidences))

    def _generate_recommendations(
        self,
        growth_signals: List[GrowthSignal],
        pain_points: List[PainPoint],
        competitors: List[CompetitorInfo],
        technology_insights: List[TechnologyInsight],
    ) -> List[str]:
        """Generate business recommendations."""
        recommendations = []

        # Growth-based recommendations
        if growth_signals:
            signal_types = [gs.signal_type for gs in growth_signals]
            if GrowthSignalType.HIRING in signal_types:
                recommendations.append(
                    "Consider talent acquisition solutions and HR technology"
                )
            if GrowthSignalType.FUNDING in signal_types:
                recommendations.append(
                    "Explore growth acceleration and scaling solutions"
                )
            if GrowthSignalType.EXPANSION in signal_types:
                recommendations.append(
                    "Focus on infrastructure and operational scaling"
                )

        # Pain point-based recommendations
        pain_categories = [pp.category for pp in pain_points]
        if PainPointCategory.TECHNOLOGY in pain_categories:
            recommendations.append("Prioritize technology modernization initiatives")
        if PainPointCategory.SCALING in pain_categories:
            recommendations.append("Implement scalable infrastructure and processes")
        if PainPointCategory.SECURITY in pain_categories:
            recommendations.append(
                "Address security vulnerabilities and compliance gaps"
            )

        # Technology-based recommendations
        high_risk_tech = [ti for ti in technology_insights if ti.risk_level > 0.7]
        if high_risk_tech:
            recommendations.append(
                "Consider migrating from high-risk legacy technologies"
            )

        emerging_tech = [
            ti
            for ti in technology_insights
            if ti.maturity == TechnologyMaturity.EMERGING
        ]
        if emerging_tech:
            recommendations.append(
                "Monitor emerging technology adoption for competitive advantage"
            )

        # Competitive recommendations
        if competitors:
            leaders = [c for c in competitors if c.market_position == "leader"]
            if leaders:
                recommendations.append(
                    "Analyze market leaders for competitive positioning opportunities"
                )

        return recommendations[:5]  # Limit to top 5 recommendations


# Convenience functions
def analyze_company_intelligence(
    company_data: Dict[str, Any],
) -> BusinessIntelligenceResult:
    """Convenience function to analyze company business intelligence."""
    engine = BusinessIntelligenceEngine()
    return engine.analyze_company(company_data)


def batch_analyze_companies(
    companies_data: List[Dict[str, Any]],
) -> List[BusinessIntelligenceResult]:
    """Batch analyze multiple companies."""
    engine = BusinessIntelligenceEngine()
    results = []

    for company_data in companies_data:
        try:
            result = engine.analyze_company(company_data)
            results.append(result)
        except Exception as e:
            logger.error(
                f"Error analyzing company {company_data.get('id', 'unknown')}: {str(e)}"
            )
            results.append(
                BusinessIntelligenceResult(
                    company_id=company_data.get("id", "unknown"),
                    confidence=0.0,
                    metadata={"error": str(e)},
                )
            )

    return results
