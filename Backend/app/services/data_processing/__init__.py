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
from .estimation import CompanySizeEstimator, RevenueEstimator
from .pipeline import DataProcessingPipeline, ProcessingConfig, PipelineResult

__all__ = [
    # Main processor
    "DataProcessingPipeline",
    # Validators
    "EmailValidator",
    "PhoneValidator",
    "DataValidator",
    # Enrichment
    "CompanyEnricher",
    "ContactEnricher",
    "TechnologyDetector",
    # Deduplication
    "DataDeduplicator",
    "CompanyDeduplicator",
    "ContactDeduplicator",
    # Cleaning
    "DataCleaner",
    "TextCleaner",
    "AddressCleaner",
    # Estimation
    "CompanySizeEstimator",
    "RevenueEstimator",
    # Pipeline
    "DataProcessingPipeline",
    "ProcessingConfig",
    "PipelineResult",
]

# Create default instances
data_processing_pipeline = DataProcessingPipeline()
processing_pipeline = DataProcessingPipeline()
