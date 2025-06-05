"""Lead Scoring Algorithm Module.

This module implements a comprehensive lead scoring system that evaluates
companies and contacts based on multiple weighted criteria including:
- Contact completeness
- Business indicators
- Data quality
- Engagement potential
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class ScoreCategory(Enum):
    """Score categories for lead scoring."""
    CONTACT_COMPLETENESS = "contact_completeness"
    BUSINESS_INDICATORS = "business_indicators"
    DATA_QUALITY = "data_quality"
    ENGAGEMENT_POTENTIAL = "engagement_potential"
    COMPANY_PROFILE = "company_profile"
    TECHNOLOGY_STACK = "technology_stack"


class SeniorityLevel(Enum):
    """Seniority levels for contact scoring."""
    C_LEVEL = "c_level"
    VP_LEVEL = "vp_level"
    DIRECTOR = "director"
    MANAGER = "manager"
    SENIOR = "senior"
    JUNIOR = "junior"
    INTERN = "intern"
    UNKNOWN = "unknown"


class CompanySize(Enum):
    """Company size categories."""
    STARTUP = "startup"  # 1-10
    SMALL = "small"  # 11-50
    MEDIUM = "medium"  # 51-200
    LARGE = "large"  # 201-1000
    ENTERPRISE = "enterprise"  # 1000+
    UNKNOWN = "unknown"


@dataclass
class ScoreWeight:
    """Weight configuration for scoring categories."""
    contact_completeness: float = 0.25
    business_indicators: float = 0.30
    data_quality: float = 0.20
    engagement_potential: float = 0.15
    company_profile: float = 0.10
    
    def __post_init__(self) -> None:
        """Validate that weights sum to 1.0."""
        total = (
            self.contact_completeness +
            self.business_indicators +
            self.data_quality +
            self.engagement_potential +
            self.company_profile
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of lead score components."""
    contact_completeness: float
    business_indicators: float
    data_quality: float
    engagement_potential: float
    company_profile: float
    total_score: float
    max_possible_score: float
    score_percentage: float
    category_scores: Dict[str, Dict[str, float]]
    

@dataclass
class LeadScore:
    """Complete lead scoring result."""
    company_id: Optional[str]
    contact_id: Optional[str]
    total_score: float
    score_percentage: float
    grade: str
    breakdown: ScoreBreakdown
    calculated_at: datetime
    factors: Dict[str, Any]


class SeniorityDetector:
    """Detects seniority level from job titles."""
    
    C_LEVEL_PATTERNS = [
        r'\b(ceo|cto|cfo|coo|cmo|cpo|chief)\b',
        r'\bpresident\b',
        r'\bfounder\b',
        r'\bowner\b'
    ]
    
    VP_PATTERNS = [
        r'\b(vp|vice president)\b',
        r'\bevp\b',
        r'\bsvp\b'
    ]
    
    DIRECTOR_PATTERNS = [
        r'\bdirector\b',
        r'\bhead of\b',
        r'\blead\b'
    ]
    
    MANAGER_PATTERNS = [
        r'\bmanager\b',
        r'\bsupervisor\b',
        r'\bteam lead\b'
    ]
    
    SENIOR_PATTERNS = [
        r'\bsenior\b',
        r'\bsr\.\b',
        r'\bprincipal\b'
    ]
    
    JUNIOR_PATTERNS = [
        r'\bjunior\b',
        r'\bjr\.\b',
        r'\bassociate\b',
        r'\bassistant\b'
    ]
    
    INTERN_PATTERNS = [
        r'\bintern\b',
        r'\btrainee\b'
    ]
    
    @classmethod
    def detect_seniority(cls, job_title: Optional[str]) -> SeniorityLevel:
        """Detect seniority level from job title."""
        if not job_title:
            return SeniorityLevel.UNKNOWN
            
        title_lower = job_title.lower()
        
        # Check patterns in order of seniority
        for pattern in cls.C_LEVEL_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.C_LEVEL
                
        for pattern in cls.VP_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.VP_LEVEL
                
        for pattern in cls.DIRECTOR_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.DIRECTOR
                
        for pattern in cls.MANAGER_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.MANAGER
                
        for pattern in cls.SENIOR_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.SENIOR
                
        for pattern in cls.JUNIOR_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.JUNIOR
                
        for pattern in cls.INTERN_PATTERNS:
            if re.search(pattern, title_lower):
                return SeniorityLevel.INTERN
                
        return SeniorityLevel.UNKNOWN


class CompanySizeDetector:
    """Detects company size category."""
    
    @classmethod
    def detect_size(cls, employee_count: Optional[int], 
                   company_size: Optional[str]) -> CompanySize:
        """Detect company size from employee count or size string."""
        if employee_count is not None:
            if employee_count <= 10:
                return CompanySize.STARTUP
            elif employee_count <= 50:
                return CompanySize.SMALL
            elif employee_count <= 200:
                return CompanySize.MEDIUM
            elif employee_count <= 1000:
                return CompanySize.LARGE
            else:
                return CompanySize.ENTERPRISE
                
        if company_size:
            size_lower = company_size.lower()
            if any(term in size_lower for term in ['startup', '1-10', 'micro']):
                return CompanySize.STARTUP
            elif any(term in size_lower for term in ['small', '11-50', '10-50']):
                return CompanySize.SMALL
            elif any(term in size_lower for term in ['medium', '51-200', '50-200']):
                return CompanySize.MEDIUM
            elif any(term in size_lower for term in ['large', '201-1000', '200-1000']):
                return CompanySize.LARGE
            elif any(term in size_lower for term in ['enterprise', '1000+', 'fortune']):
                return CompanySize.ENTERPRISE
                
        return CompanySize.UNKNOWN


class ContactCompletenessScorer:
    """Scores contact data completeness."""
    
    FIELD_WEIGHTS = {
        'email': 0.25,
        'phone': 0.20,
        'full_name': 0.15,
        'job_title': 0.15,
        'linkedin_url': 0.10,
        'department': 0.05,
        'location': 0.05,
        'bio': 0.05
    }
    
    @classmethod
    def score_contact(cls, contact_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Score contact completeness."""
        scores = {}
        total_score = 0.0
        
        for field, weight in cls.FIELD_WEIGHTS.items():
            value = contact_data.get(field)
            field_score = cls._score_field(field, value)
            scores[field] = field_score
            total_score += field_score * weight
            
        return total_score, scores
    
    @classmethod
    def _score_field(cls, field: str, value: Any) -> float:
        """Score individual field completeness."""
        if value is None:
            return 0.0
            
        if isinstance(value, str):
            if not value.strip():
                return 0.0
            # Score based on length and quality
            if field == 'email':
                return 1.0 if '@' in value and '.' in value else 0.5
            elif field == 'phone':
                # Remove non-digits and check length
                digits = re.sub(r'\D', '', value)
                return 1.0 if len(digits) >= 10 else 0.7
            elif field == 'linkedin_url':
                return 1.0 if 'linkedin.com' in value.lower() else 0.5
            elif field in ['full_name', 'job_title']:
                return min(1.0, len(value.strip()) / 20)  # Full score at 20+ chars
            else:
                return min(1.0, len(value.strip()) / 10)  # Full score at 10+ chars
                
        elif isinstance(value, dict) and field == 'location':
            # Score location completeness
            location_fields = ['city', 'state', 'country']
            filled_fields = sum(1 for f in location_fields if value.get(f))
            return filled_fields / len(location_fields)
            
        return 1.0 if value else 0.0


class BusinessIndicatorsScorer:
    """Scores business indicators and company attractiveness."""
    
    SENIORITY_SCORES = {
        SeniorityLevel.C_LEVEL: 1.0,
        SeniorityLevel.VP_LEVEL: 0.9,
        SeniorityLevel.DIRECTOR: 0.8,
        SeniorityLevel.MANAGER: 0.6,
        SeniorityLevel.SENIOR: 0.4,
        SeniorityLevel.JUNIOR: 0.2,
        SeniorityLevel.INTERN: 0.1,
        SeniorityLevel.UNKNOWN: 0.3
    }
    
    COMPANY_SIZE_SCORES = {
        CompanySize.ENTERPRISE: 1.0,
        CompanySize.LARGE: 0.8,
        CompanySize.MEDIUM: 0.6,
        CompanySize.SMALL: 0.4,
        CompanySize.STARTUP: 0.3,
        CompanySize.UNKNOWN: 0.2
    }
    
    HIGH_VALUE_INDUSTRIES = {
        'technology', 'software', 'fintech', 'healthcare', 'biotechnology',
        'artificial intelligence', 'machine learning', 'cybersecurity',
        'cloud computing', 'saas', 'e-commerce', 'digital marketing'
    }
    
    @classmethod
    def score_business_indicators(cls, contact_data: Dict[str, Any], 
                                company_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Score business indicators."""
        scores = {}
        
        # Seniority score
        job_title = contact_data.get('job_title')
        seniority = SeniorityDetector.detect_seniority(job_title)
        scores['seniority'] = cls.SENIORITY_SCORES[seniority]
        
        # Company size score
        employee_count = company_data.get('employee_count')
        company_size_str = company_data.get('company_size')
        company_size = CompanySizeDetector.detect_size(employee_count, company_size_str)
        scores['company_size'] = cls.COMPANY_SIZE_SCORES[company_size]
        
        # Industry score
        industry = company_data.get('industry', '').lower()
        scores['industry'] = 1.0 if any(hvi in industry for hvi in cls.HIGH_VALUE_INDUSTRIES) else 0.5
        
        # Decision maker score
        is_decision_maker = contact_data.get('is_decision_maker', False)
        scores['decision_maker'] = 1.0 if is_decision_maker else 0.3
        
        # Revenue/funding score
        revenue_range = company_data.get('revenue_range', '')
        scores['revenue'] = cls._score_revenue(revenue_range)
        
        # Growth signals score
        growth_signals = company_data.get('growth_signals', {})
        scores['growth_signals'] = cls._score_growth_signals(growth_signals)
        
        # Calculate weighted total
        weights = {
            'seniority': 0.30,
            'company_size': 0.25,
            'industry': 0.15,
            'decision_maker': 0.15,
            'revenue': 0.10,
            'growth_signals': 0.05
        }
        
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score, scores
    
    @classmethod
    def _score_revenue(cls, revenue_range: str) -> float:
        """Score revenue range."""
        if not revenue_range:
            return 0.2
            
        revenue_lower = revenue_range.lower()
        if any(term in revenue_lower for term in ['billion', '$1b+', '>1b']):
            return 1.0
        elif any(term in revenue_lower for term in ['million', '$100m+', '>100m']):
            return 0.8
        elif any(term in revenue_lower for term in ['$10m+', '>10m']):
            return 0.6
        elif any(term in revenue_lower for term in ['$1m+', '>1m']):
            return 0.4
        else:
            return 0.2
    
    @classmethod
    def _score_growth_signals(cls, growth_signals: Dict[str, Any]) -> float:
        """Score growth signals."""
        if not growth_signals:
            return 0.2
            
        positive_signals = [
            'hiring', 'expansion', 'funding', 'new_product', 'partnership',
            'acquisition', 'ipo', 'revenue_growth', 'market_expansion'
        ]
        
        signal_count = sum(1 for signal in positive_signals 
                          if growth_signals.get(signal, False))
        
        return min(1.0, signal_count / len(positive_signals) * 2)  # Scale up


class DataQualityScorer:
    """Scores data quality and reliability."""
    
    @classmethod
    def score_data_quality(cls, contact_data: Dict[str, Any], 
                          company_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Score overall data quality."""
        scores = {}
        
        # Contact verification score
        is_verified = contact_data.get('is_verified', False)
        scores['verification'] = 1.0 if is_verified else 0.3
        
        # Data freshness score
        last_activity = contact_data.get('last_activity_date')
        scores['freshness'] = cls._score_freshness(last_activity)
        
        # Source reliability score
        source = contact_data.get('source', '')
        scores['source_reliability'] = cls._score_source(source)
        
        # Data consistency score
        scores['consistency'] = cls._score_consistency(contact_data, company_data)
        
        # Existing quality scores
        contact_quality = contact_data.get('contact_quality_score')
        if contact_quality is not None:
            scores['contact_quality'] = float(contact_quality)
        else:
            scores['contact_quality'] = 0.5
            
        company_quality = company_data.get('data_quality_score')
        if company_quality is not None:
            scores['company_quality'] = float(company_quality)
        else:
            scores['company_quality'] = 0.5
        
        # Calculate weighted total
        weights = {
            'verification': 0.25,
            'freshness': 0.20,
            'source_reliability': 0.15,
            'consistency': 0.15,
            'contact_quality': 0.15,
            'company_quality': 0.10
        }
        
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score, scores
    
    @classmethod
    def _score_freshness(cls, last_activity: Optional[datetime]) -> float:
        """Score data freshness based on last activity."""
        if not last_activity:
            return 0.3
            
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            except ValueError:
                return 0.3
                
        now = datetime.now(last_activity.tzinfo) if last_activity.tzinfo else datetime.now()
        days_old = (now - last_activity).days
        
        if days_old <= 30:
            return 1.0
        elif days_old <= 90:
            return 0.8
        elif days_old <= 180:
            return 0.6
        elif days_old <= 365:
            return 0.4
        else:
            return 0.2
    
    @classmethod
    def _score_source(cls, source: str) -> float:
        """Score source reliability."""
        reliable_sources = {
            'linkedin': 0.9,
            'company_website': 0.8,
            'google_my_business': 0.7,
            'crunchbase': 0.8,
            'apollo': 0.7,
            'zoominfo': 0.7
        }
        
        source_lower = source.lower()
        for reliable_source, score in reliable_sources.items():
            if reliable_source in source_lower:
                return score
                
        return 0.5  # Default for unknown sources
    
    @classmethod
    def _score_consistency(cls, contact_data: Dict[str, Any], 
                          company_data: Dict[str, Any]) -> float:
        """Score data consistency between contact and company."""
        consistency_score = 1.0
        
        # Check if contact location matches company location
        contact_location = contact_data.get('location', {})
        company_location = company_data.get('location', {})
        
        if contact_location and company_location:
            contact_city = contact_location.get('city', '').lower()
            company_city = company_location.get('city', '').lower()
            if contact_city and company_city and contact_city != company_city:
                consistency_score -= 0.2
        
        # Check if email domain matches company domain
        email = contact_data.get('email', '')
        company_domain = company_data.get('domain', '')
        
        if email and company_domain:
            email_domain = email.split('@')[-1].lower()
            if company_domain.lower() not in email_domain:
                consistency_score -= 0.3
        
        return max(0.0, consistency_score)


class EngagementPotentialScorer:
    """Scores engagement potential and likelihood of response."""
    
    @classmethod
    def score_engagement_potential(cls, contact_data: Dict[str, Any], 
                                 company_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Score engagement potential."""
        scores = {}
        
        # Social media presence score
        scores['social_presence'] = cls._score_social_presence(contact_data)
        
        # Professional activity score
        scores['professional_activity'] = cls._score_professional_activity(contact_data)
        
        # Company engagement score
        scores['company_engagement'] = cls._score_company_engagement(company_data)
        
        # Contact accessibility score
        scores['accessibility'] = cls._score_accessibility(contact_data)
        
        # Existing engagement score
        engagement_potential = contact_data.get('engagement_potential')
        if engagement_potential is not None:
            scores['existing_engagement'] = float(engagement_potential)
        else:
            scores['existing_engagement'] = 0.5
        
        # Calculate weighted total
        weights = {
            'social_presence': 0.25,
            'professional_activity': 0.25,
            'company_engagement': 0.20,
            'accessibility': 0.15,
            'existing_engagement': 0.15
        }
        
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score, scores
    
    @classmethod
    def _score_social_presence(cls, contact_data: Dict[str, Any]) -> float:
        """Score social media presence."""
        score = 0.0
        
        if contact_data.get('linkedin_url'):
            score += 0.6
        if contact_data.get('twitter_handle'):
            score += 0.3
        if contact_data.get('bio'):
            score += 0.1
            
        return min(1.0, score)
    
    @classmethod
    def _score_professional_activity(cls, contact_data: Dict[str, Any]) -> float:
        """Score professional activity indicators."""
        score = 0.5  # Base score
        
        # Recent activity
        last_activity = contact_data.get('last_activity_date')
        if last_activity:
            if isinstance(last_activity, str):
                try:
                    last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                except ValueError:
                    last_activity = None
                    
            if last_activity:
                now = datetime.now(last_activity.tzinfo) if last_activity.tzinfo else datetime.now()
                days_old = (now - last_activity).days
                if days_old <= 7:
                    score += 0.3
                elif days_old <= 30:
                    score += 0.2
                elif days_old <= 90:
                    score += 0.1
        
        # Skills and experience
        skills = contact_data.get('skills', [])
        if skills and len(skills) > 3:
            score += 0.1
            
        experience_years = contact_data.get('experience_years')
        if experience_years and experience_years > 5:
            score += 0.1
            
        return min(1.0, score)
    
    @classmethod
    def _score_company_engagement(cls, company_data: Dict[str, Any]) -> float:
        """Score company engagement indicators."""
        score = 0.5  # Base score
        
        # Social media presence
        social_media = company_data.get('social_media', {})
        if social_media:
            score += min(0.3, len(social_media) * 0.1)
        
        # Website presence
        if company_data.get('website'):
            score += 0.1
            
        # Technology stack (indicates active development)
        tech_stack = company_data.get('technology_stack', [])
        if tech_stack:
            score += min(0.1, len(tech_stack) * 0.02)
            
        return min(1.0, score)
    
    @classmethod
    def _score_accessibility(cls, contact_data: Dict[str, Any]) -> float:
        """Score contact accessibility."""
        score = 0.0
        
        # Email availability
        if contact_data.get('email'):
            score += 0.5
            
        # Phone availability
        if contact_data.get('phone'):
            score += 0.3
            
        # LinkedIn availability
        if contact_data.get('linkedin_url'):
            score += 0.2
            
        return min(1.0, score)


class CompanyProfileScorer:
    """Scores company profile attractiveness."""
    
    @classmethod
    def score_company_profile(cls, company_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Score company profile."""
        scores = {}
        
        # Company maturity score
        scores['maturity'] = cls._score_maturity(company_data)
        
        # Technology adoption score
        scores['technology'] = cls._score_technology(company_data)
        
        # Market position score
        scores['market_position'] = cls._score_market_position(company_data)
        
        # Innovation score
        scores['innovation'] = cls._score_innovation(company_data)
        
        # Calculate weighted total
        weights = {
            'maturity': 0.30,
            'technology': 0.25,
            'market_position': 0.25,
            'innovation': 0.20
        }
        
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score, scores
    
    @classmethod
    def _score_maturity(cls, company_data: Dict[str, Any]) -> float:
        """Score company maturity."""
        founded_year = company_data.get('founded_year')
        if not founded_year:
            return 0.5
            
        current_year = datetime.now().year
        age = current_year - founded_year
        
        if age >= 20:
            return 1.0
        elif age >= 10:
            return 0.8
        elif age >= 5:
            return 0.6
        elif age >= 2:
            return 0.4
        else:
            return 0.2
    
    @classmethod
    def _score_technology(cls, company_data: Dict[str, Any]) -> float:
        """Score technology adoption."""
        tech_stack = company_data.get('technology_stack', [])
        if not tech_stack:
            return 0.3
            
        modern_technologies = {
            'react', 'vue', 'angular', 'node.js', 'python', 'aws', 'azure',
            'kubernetes', 'docker', 'microservices', 'api', 'cloud',
            'machine learning', 'ai', 'blockchain', 'saas'
        }
        
        tech_lower = [tech.lower() for tech in tech_stack]
        modern_count = sum(1 for tech in modern_technologies 
                          if any(modern_tech in tech for modern_tech in tech_lower))
        
        return min(1.0, modern_count / 5)  # Full score at 5+ modern technologies
    
    @classmethod
    def _score_market_position(cls, company_data: Dict[str, Any]) -> float:
        """Score market position."""
        score = 0.5  # Base score
        
        # Revenue range
        revenue_range = company_data.get('revenue_range', '')
        if 'billion' in revenue_range.lower():
            score += 0.3
        elif 'million' in revenue_range.lower():
            score += 0.2
        
        # Employee count
        employee_count = company_data.get('employee_count')
        if employee_count:
            if employee_count > 1000:
                score += 0.2
            elif employee_count > 100:
                score += 0.1
        
        return min(1.0, score)
    
    @classmethod
    def _score_innovation(cls, company_data: Dict[str, Any]) -> float:
        """Score innovation indicators."""
        score = 0.3  # Base score
        
        # Growth signals
        growth_signals = company_data.get('growth_signals', {})
        if growth_signals:
            innovation_signals = ['new_product', 'partnership', 'funding', 'expansion']
            signal_count = sum(1 for signal in innovation_signals 
                             if growth_signals.get(signal, False))
            score += signal_count * 0.15
        
        # Technology stack diversity
        tech_stack = company_data.get('technology_stack', [])
        if len(tech_stack) > 10:
            score += 0.2
        elif len(tech_stack) > 5:
            score += 0.1
        
        return min(1.0, score)


class LeadScoringEngine:
    """Main lead scoring engine that orchestrates all scoring components."""
    
    def __init__(self, weights: Optional[ScoreWeight] = None):
        """Initialize the lead scoring engine."""
        self.weights = weights or ScoreWeight()
        self.contact_scorer = ContactCompletenessScorer()
        self.business_scorer = BusinessIndicatorsScorer()
        self.quality_scorer = DataQualityScorer()
        self.engagement_scorer = EngagementPotentialScorer()
        self.company_scorer = CompanyProfileScorer()
    
    def score_lead(self, contact_data: Dict[str, Any], 
                   company_data: Dict[str, Any]) -> LeadScore:
        """Calculate comprehensive lead score."""
        try:
            # Calculate individual category scores
            contact_score, contact_breakdown = self.contact_scorer.score_contact(contact_data)
            business_score, business_breakdown = self.business_scorer.score_business_indicators(
                contact_data, company_data
            )
            quality_score, quality_breakdown = self.quality_scorer.score_data_quality(
                contact_data, company_data
            )
            engagement_score, engagement_breakdown = self.engagement_scorer.score_engagement_potential(
                contact_data, company_data
            )
            company_score, company_breakdown = self.company_scorer.score_company_profile(
                company_data
            )
            
            # Calculate weighted total score
            total_score = (
                contact_score * self.weights.contact_completeness +
                business_score * self.weights.business_indicators +
                quality_score * self.weights.data_quality +
                engagement_score * self.weights.engagement_potential +
                company_score * self.weights.company_profile
            )
            
            # Calculate maximum possible score (all categories at 1.0)
            max_possible_score = (
                1.0 * self.weights.contact_completeness +
                1.0 * self.weights.business_indicators +
                1.0 * self.weights.data_quality +
                1.0 * self.weights.engagement_potential +
                1.0 * self.weights.company_profile
            )
            
            score_percentage = (total_score / max_possible_score) * 100
            
            # Create detailed breakdown
            breakdown = ScoreBreakdown(
                contact_completeness=contact_score,
                business_indicators=business_score,
                data_quality=quality_score,
                engagement_potential=engagement_score,
                company_profile=company_score,
                total_score=total_score,
                max_possible_score=max_possible_score,
                score_percentage=score_percentage,
                category_scores={
                    'contact_breakdown': contact_breakdown,
                    'business_breakdown': business_breakdown,
                    'quality_breakdown': quality_breakdown,
                    'engagement_breakdown': engagement_breakdown,
                    'company_breakdown': company_breakdown
                }
            )
            
            # Determine grade
            grade = self._calculate_grade(score_percentage)
            
            # Collect factors
            factors = {
                'seniority': SeniorityDetector.detect_seniority(
                    contact_data.get('job_title')
                ).value,
                'company_size': CompanySizeDetector.detect_size(
                    company_data.get('employee_count'),
                    company_data.get('company_size')
                ).value,
                'industry': company_data.get('industry'),
                'is_decision_maker': contact_data.get('is_decision_maker', False),
                'is_verified': contact_data.get('is_verified', False),
                'has_email': bool(contact_data.get('email')),
                'has_phone': bool(contact_data.get('phone')),
                'has_linkedin': bool(contact_data.get('linkedin_url'))
            }
            
            return LeadScore(
                company_id=company_data.get('id'),
                contact_id=contact_data.get('id'),
                total_score=total_score,
                score_percentage=score_percentage,
                grade=grade,
                breakdown=breakdown,
                calculated_at=datetime.now(),
                factors=factors
            )
            
        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            # Return minimal score on error
            return LeadScore(
                company_id=company_data.get('id'),
                contact_id=contact_data.get('id'),
                total_score=0.0,
                score_percentage=0.0,
                grade='F',
                breakdown=ScoreBreakdown(
                    contact_completeness=0.0,
                    business_indicators=0.0,
                    data_quality=0.0,
                    engagement_potential=0.0,
                    company_profile=0.0,
                    total_score=0.0,
                    max_possible_score=1.0,
                    score_percentage=0.0,
                    category_scores={}
                ),
                calculated_at=datetime.now(),
                factors={'error': str(e)}
            )
    
    def _calculate_grade(self, score_percentage: float) -> str:
        """Calculate letter grade from score percentage."""
        if score_percentage >= 90:
            return 'A+'
        elif score_percentage >= 85:
            return 'A'
        elif score_percentage >= 80:
            return 'A-'
        elif score_percentage >= 75:
            return 'B+'
        elif score_percentage >= 70:
            return 'B'
        elif score_percentage >= 65:
            return 'B-'
        elif score_percentage >= 60:
            return 'C+'
        elif score_percentage >= 55:
            return 'C'
        elif score_percentage >= 50:
            return 'C-'
        elif score_percentage >= 40:
            return 'D'
        else:
            return 'F'
    
    def batch_score_leads(self, leads_data: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[LeadScore]:
        """Score multiple leads in batch."""
        results = []
        for contact_data, company_data in leads_data:
            score = self.score_lead(contact_data, company_data)
            results.append(score)
        return results
    
    def update_weights(self, new_weights: ScoreWeight) -> None:
        """Update scoring weights."""
        self.weights = new_weights
    
    def get_scoring_summary(self, scores: List[LeadScore]) -> Dict[str, Any]:
        """Generate summary statistics for a batch of scores."""
        if not scores:
            return {}
            
        total_scores = [score.total_score for score in scores]
        percentages = [score.score_percentage for score in scores]
        grades = [score.grade for score in scores]
        
        grade_distribution: Dict[str, int] = {}
        for grade in grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            'total_leads': len(scores),
            'average_score': sum(total_scores) / len(total_scores),
            'average_percentage': sum(percentages) / len(percentages),
            'min_score': min(total_scores),
            'max_score': max(total_scores),
            'grade_distribution': grade_distribution,
            'high_quality_leads': len([s for s in scores if s.score_percentage >= 70]),
            'medium_quality_leads': len([s for s in scores if 40 <= s.score_percentage < 70]),
            'low_quality_leads': len([s for s in scores if s.score_percentage < 40])
        }


# Factory function for easy instantiation
def create_lead_scoring_engine(weights: Optional[ScoreWeight] = None) -> LeadScoringEngine:
    """Create a lead scoring engine with optional custom weights."""
    return LeadScoringEngine(weights)


# Utility functions
def calculate_lead_score(contact_data: Dict[str, Any], 
                        company_data: Dict[str, Any],
                        weights: Optional[ScoreWeight] = None) -> LeadScore:
    """Convenience function to calculate a single lead score."""
    engine = create_lead_scoring_engine(weights)
    return engine.score_lead(contact_data, company_data)


def batch_calculate_lead_scores(leads_data: List[Tuple[Dict[str, Any], Dict[str, Any]]],
                               weights: Optional[ScoreWeight] = None) -> List[LeadScore]:
    """Convenience function to calculate multiple lead scores."""
    engine = create_lead_scoring_engine(weights)
    return engine.batch_score_leads(leads_data)