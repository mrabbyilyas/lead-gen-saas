"""Data processing pipeline for lead generation system.

This module provides comprehensive data processing capabilities including:
- Data validation and cleaning
- Email and phone number validation
- Company data enrichment
- Deduplication algorithms
- Technology stack detection
- Company size estimation
"""

from .validators import EmailValidator, PhoneValidator, DataValidator
from .enrichment import CompanyEnricher, ContactEnricher, TechnologyDetector
from .deduplication import DataDeduplicator, CompanyDeduplicator, ContactDeduplicator
from .cleaning import DataCleaner, TextCleaner, AddressCleaner
from .estimation import (
    DataEstimator,
    CompanySizeEstimator,
    RevenueEstimator,
    EstimationResult,
    CompanySize as EstimationCompanySize,
    RevenueRange,
    Industry,
)
from .lead_scoring import (
    ScoreCategory,
    SeniorityLevel,
    CompanySize as ScoringCompanySize,
    ScoreWeight,
    ScoreBreakdown,
    LeadScore,
    SeniorityDetector,
    CompanySizeDetector,
    ContactCompletenessScorer,
    BusinessIndicatorsScorer,
    DataQualityScorer,
    EngagementPotentialScorer,
    CompanyProfileScorer,
    LeadScoringEngine,
    create_lead_scoring_engine,
    calculate_lead_score,
    batch_calculate_lead_scores,
)
from .pipeline import (
    DataProcessingPipeline,
    ProcessingConfig,
    ProcessingMode,
    ProcessingStage,
    PipelineResult,
    StageResult,
)

__all__ = [
    # Validators
    "EmailValidator",
    "PhoneValidator",
    "URLValidator",
    "DomainValidator",
    "LinkedInValidator",
    "CompanyNameValidator",
    "ContactNameValidator",
    "DataValidator",
    "ValidationConfig",
    "ValidationResult",
    "create_data_validator",
    # Enrichment
    "TechnologyDetector",
    "CompanyEnricher",
    "ContactEnricher",
    "DataEnricher",
    "EnrichmentConfig",
    "EnrichmentResult",
    "create_data_enricher",
    # Deduplication
    "DataDeduplicator",
    "CompanyDeduplicator",
    "ContactDeduplicator",
    # Cleaning
    "DataCleaner",
    "TextCleaner",
    "AddressCleaner",
    # Estimation
    "DataEstimator",
    "CompanySizeEstimator",
    "RevenueEstimator",
    "EstimationResult",
    "EstimationCompanySize",
    "RevenueRange",
    "Industry",
    # Lead Scoring
    "ScoreCategory",
    "SeniorityLevel",
    "ScoringCompanySize",
    "ScoreWeight",
    "ScoreBreakdown",
    "LeadScore",
    "SeniorityDetector",
    "CompanySizeDetector",
    "ContactCompletenessScorer",
    "BusinessIndicatorsScorer",
    "DataQualityScorer",
    "EngagementPotentialScorer",
    "CompanyProfileScorer",
    "LeadScoringEngine",
    "create_lead_scoring_engine",
    "calculate_lead_score",
    "batch_calculate_lead_scores",
    # Pipeline
    "DataProcessingPipeline",
    "ProcessingConfig",
    "ProcessingMode",
    "ProcessingStage",
    "PipelineResult",
    "StageResult",
]

# Create default instances
data_processing_pipeline = DataProcessingPipeline()
processing_pipeline = DataProcessingPipeline()
