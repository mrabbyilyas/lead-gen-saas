"""Data processing pipeline for lead generation system.

This module provides comprehensive data processing capabilities including:
- Data validation and cleaning
- Email and phone number validation
- Company data enrichment
- Deduplication algorithms
- Technology stack detection
- Company size estimation
"""

from .data_processor import DataProcessor
from .validators import EmailValidator, PhoneValidator, DataValidator
from .enrichment import CompanyEnricher, ContactEnricher, TechnologyDetector
from .deduplication import DeduplicationEngine, CompanyDeduplicator, ContactDeduplicator
from .cleaning import DataCleaner, TextCleaner, AddressCleaner
from .estimation import CompanySizeEstimator, RevenueEstimator
from .pipeline import ProcessingPipeline, PipelineConfig, ProcessingResult

__all__ = [
    # Main processor
    "DataProcessor",
    # Validators
    "EmailValidator",
    "PhoneValidator",
    "DataValidator",
    # Enrichment
    "CompanyEnricher",
    "ContactEnricher",
    "TechnologyDetector",
    # Deduplication
    "DeduplicationEngine",
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
    "ProcessingPipeline",
    "PipelineConfig",
    "ProcessingResult",
]

# Create default instances
data_processor = DataProcessor()
processing_pipeline = ProcessingPipeline()
