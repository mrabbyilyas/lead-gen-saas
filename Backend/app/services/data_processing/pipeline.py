"""Main data processing pipeline orchestrator."""

import logging
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from datetime import datetime
import time

from .validators import (
    EmailValidator,
    PhoneValidator,
    URLValidator,
    DomainValidator,
    LinkedInURLValidator,
    CompanyNameValidator,
    ContactNameValidator,
    ValidationResult,
)
from .cleaning import DataCleaner
from .enrichment import CompanyEnricher, ContactEnricher
from .deduplication import DataDeduplicator, MergeStrategy
from .estimation import DataEstimator

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Data processing stages."""

    VALIDATION = "validation"
    CLEANING = "cleaning"
    ENRICHMENT = "enrichment"
    DEDUPLICATION = "deduplication"
    ESTIMATION = "estimation"
    FINALIZATION = "finalization"


class ProcessingMode(Enum):
    """Processing modes."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BATCH = "batch"


@dataclass
class ProcessingConfig:
    """Configuration for data processing pipeline."""

    # Processing modes
    mode: ProcessingMode = ProcessingMode.SEQUENTIAL
    batch_size: int = 100
    max_workers: int = 4

    # Stage enablement
    enable_validation: bool = True
    enable_cleaning: bool = True
    enable_enrichment: bool = True
    enable_deduplication: bool = True
    enable_estimation: bool = True

    # Validation settings
    strict_validation: bool = False
    skip_invalid_records: bool = False

    # Cleaning settings
    aggressive_cleaning: bool = False
    preserve_original: bool = True

    # Enrichment settings
    enrichment_timeout: int = 30
    max_enrichment_requests: int = 10

    # Deduplication settings
    merge_strategy: MergeStrategy = MergeStrategy.KEEP_MOST_COMPLETE
    dedup_threshold: float = 0.8

    # Estimation settings
    enable_size_estimation: bool = True
    enable_revenue_estimation: bool = True
    enable_contact_scoring: bool = True

    # Error handling
    continue_on_error: bool = True
    max_errors: int = 100

    # Performance settings
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour


@dataclass
class StageResult:
    """Result of a processing stage."""

    stage: ProcessingStage
    success: bool
    processed_count: int
    error_count: int
    duration: float
    data: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of the entire processing pipeline."""

    success: bool
    total_duration: float
    input_count: int
    output_count: int
    processed_companies: List[Dict[str, Any]] = field(default_factory=list)
    processed_contacts: List[Dict[str, Any]] = field(default_factory=list)
    stage_results: List[StageResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataProcessingPipeline:
    """Main data processing pipeline orchestrator."""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()

        # Initialize processors
        self.validators: Dict[str, Union[EmailValidator, PhoneValidator, URLValidator, DomainValidator, LinkedInURLValidator, CompanyNameValidator, ContactNameValidator]] = {
            "email": EmailValidator(),
            "phone": PhoneValidator(),
            "url": URLValidator(),
            "domain": DomainValidator(),
            "linkedin_url": LinkedInURLValidator(),
            "company_name": CompanyNameValidator(),
            "contact_name": ContactNameValidator(),
        }

        self.cleaner = DataCleaner()
        self.company_enricher = CompanyEnricher()
        self.contact_enricher = ContactEnricher()
        self.deduplicator = DataDeduplicator()
        self.estimator = DataEstimator()

        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "companies_processed": 0,
            "contacts_processed": 0,
            "errors_encountered": 0,
            "processing_time": 0.0,
        }

    async def process_data(
        self,
        companies: Optional[List[Dict[str, Any]]] = None,
        contacts: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> PipelineResult:
        """Process companies and contacts through the full pipeline."""
        start_time = time.time()
        stage_results = []
        errors = []

        try:
            # Initialize data
            companies = companies or []
            contacts = contacts or []
            input_count = len(companies) + len(contacts)

            logger.info(
                f"Starting data processing pipeline with {len(companies)} companies and {len(contacts)} contacts"
            )

            # Stage 1: Validation
            if self.config.enable_validation:
                validation_result = await self._run_validation_stage(
                    companies, contacts, progress_callback
                )
                stage_results.append(validation_result)

                if validation_result.success:
                    companies, contacts = self._extract_data_from_stage_result(
                        validation_result, companies, contacts
                    )
                else:
                    errors.extend(validation_result.errors)
                    if not self.config.continue_on_error:
                        raise Exception("Validation stage failed")

            # Stage 2: Cleaning
            if self.config.enable_cleaning:
                cleaning_result = await self._run_cleaning_stage(
                    companies, contacts, progress_callback
                )
                stage_results.append(cleaning_result)

                if cleaning_result.success:
                    companies, contacts = self._extract_data_from_stage_result(
                        cleaning_result, companies, contacts
                    )
                else:
                    errors.extend(cleaning_result.errors)
                    if not self.config.continue_on_error:
                        raise Exception("Cleaning stage failed")

            # Stage 3: Enrichment
            if self.config.enable_enrichment:
                enrichment_result = await self._run_enrichment_stage(
                    companies, contacts, progress_callback
                )
                stage_results.append(enrichment_result)

                if enrichment_result.success:
                    companies, contacts = self._extract_data_from_stage_result(
                        enrichment_result, companies, contacts
                    )
                else:
                    errors.extend(enrichment_result.errors)
                    if not self.config.continue_on_error:
                        raise Exception("Enrichment stage failed")

            # Stage 4: Deduplication
            if self.config.enable_deduplication:
                deduplication_result = await self._run_deduplication_stage(
                    companies, contacts, progress_callback
                )
                stage_results.append(deduplication_result)

                if deduplication_result.success:
                    companies, contacts = self._extract_data_from_stage_result(
                        deduplication_result, companies, contacts
                    )
                else:
                    errors.extend(deduplication_result.errors)
                    if not self.config.continue_on_error:
                        raise Exception("Deduplication stage failed")

            # Stage 5: Estimation
            if self.config.enable_estimation:
                estimation_result = await self._run_estimation_stage(
                    companies, contacts, progress_callback
                )
                stage_results.append(estimation_result)

                if estimation_result.success:
                    companies, contacts = self._extract_data_from_stage_result(
                        estimation_result, companies, contacts
                    )
                else:
                    errors.extend(estimation_result.errors)
                    if not self.config.continue_on_error:
                        raise Exception("Estimation stage failed")

            # Stage 6: Finalization
            finalization_result = await self._run_finalization_stage(
                companies, contacts, progress_callback
            )
            stage_results.append(finalization_result)

            if finalization_result.success:
                companies, contacts = self._extract_data_from_stage_result(
                    finalization_result, companies, contacts
                )
            else:
                errors.extend(finalization_result.errors)

            # Calculate final statistics
            total_duration = time.time() - start_time
            output_count = len(companies) + len(contacts)

            # Update internal statistics
            self.stats["total_processed"] += input_count
            self.stats["companies_processed"] += len(companies)
            self.stats["contacts_processed"] += len(contacts)
            self.stats["processing_time"] += total_duration

            success = all(result.success for result in stage_results)

            logger.info(
                f"Pipeline completed in {total_duration:.2f}s. Processed {output_count}/{input_count} records"
            )

            return PipelineResult(
                success=success,
                total_duration=total_duration,
                input_count=input_count,
                output_count=output_count,
                processed_companies=companies,
                processed_contacts=contacts,
                stage_results=stage_results,
                errors=errors,
                metadata={
                    "config": self.config.__dict__,
                    "statistics": self.stats.copy(),
                },
            )

        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"Pipeline failed after {total_duration:.2f}s: {e}")

            return PipelineResult(
                success=False,
                total_duration=total_duration,
                input_count=input_count if "input_count" in locals() else 0,
                output_count=0,
                processed_companies=[],
                processed_contacts=[],
                stage_results=stage_results,
                errors=errors + [f"Pipeline failed: {str(e)}"],
            )

    async def _run_validation_stage(
        self,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> StageResult:
        """Run validation stage."""
        start_time = time.time()
        errors = []
        processed_count = 0

        try:
            logger.info("Starting validation stage")

            # Validate companies
            validated_companies = []
            for i, company in enumerate(companies):
                try:
                    validated_company = await self._validate_company(company)
                    if validated_company or not self.config.skip_invalid_records:
                        validated_companies.append(validated_company or company)
                        processed_count += 1
                except Exception as e:
                    errors.append(f"Company validation error at index {i}: {str(e)}")
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "validation", i + 1, len(companies) + len(contacts)
                    )

            # Validate contacts
            validated_contacts = []
            for i, contact in enumerate(contacts):
                try:
                    validated_contact = await self._validate_contact(contact)
                    if validated_contact or not self.config.skip_invalid_records:
                        validated_contacts.append(validated_contact or contact)
                        processed_count += 1
                except Exception as e:
                    errors.append(f"Contact validation error at index {i}: {str(e)}")
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "validation",
                        len(companies) + i + 1,
                        len(companies) + len(contacts),
                    )

            duration = time.time() - start_time

            return StageResult(
                stage=ProcessingStage.VALIDATION,
                success=True,
                processed_count=processed_count,
                error_count=len(errors),
                duration=duration,
                data=validated_companies + validated_contacts,
                errors=errors,
                metadata={
                    "companies_validated": len(validated_companies),
                    "contacts_validated": len(validated_contacts),
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Validation stage failed: {e}")

            return StageResult(
                stage=ProcessingStage.VALIDATION,
                success=False,
                processed_count=processed_count,
                error_count=len(errors) + 1,
                duration=duration,
                errors=errors + [f"Validation stage failed: {str(e)}"],
            )

    async def _run_cleaning_stage(
        self,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> StageResult:
        """Run cleaning stage."""
        start_time = time.time()
        errors = []
        processed_count = 0

        try:
            logger.info("Starting cleaning stage")

            # Clean companies
            cleaned_companies = []
            for i, company in enumerate(companies):
                try:
                    cleaned_company = self.cleaner.clean_company_data(company)
                    cleaned_companies.append(cleaned_company)
                    processed_count += 1
                except Exception as e:
                    errors.append(f"Company cleaning error at index {i}: {str(e)}")
                    cleaned_companies.append(company)  # Keep original on error
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback("cleaning", i + 1, len(companies) + len(contacts))

            # Clean contacts
            cleaned_contacts = []
            for i, contact in enumerate(contacts):
                try:
                    cleaned_contact = self.cleaner.clean_contact_data(contact)
                    cleaned_contacts.append(cleaned_contact)
                    processed_count += 1
                except Exception as e:
                    errors.append(f"Contact cleaning error at index {i}: {str(e)}")
                    cleaned_contacts.append(contact)  # Keep original on error
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "cleaning",
                        len(companies) + i + 1,
                        len(companies) + len(contacts),
                    )

            duration = time.time() - start_time

            return StageResult(
                stage=ProcessingStage.CLEANING,
                success=True,
                processed_count=processed_count,
                error_count=len(errors),
                duration=duration,
                data=cleaned_companies + cleaned_contacts,
                errors=errors,
                metadata={
                    "companies_cleaned": len(cleaned_companies),
                    "contacts_cleaned": len(cleaned_contacts),
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Cleaning stage failed: {e}")

            return StageResult(
                stage=ProcessingStage.CLEANING,
                success=False,
                processed_count=processed_count,
                error_count=len(errors) + 1,
                duration=duration,
                errors=errors + [f"Cleaning stage failed: {str(e)}"],
            )

    async def _run_enrichment_stage(
        self,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> StageResult:
        """Run enrichment stage."""
        start_time = time.time()
        errors = []
        processed_count = 0

        try:
            logger.info("Starting enrichment stage")

            # Enrich companies
            enriched_companies = []
            for i, company in enumerate(companies):
                try:
                    enrichment_result = await self.company_enricher.enrich_company(
                        company
                    )
                    enriched_companies.append(enrichment_result.enriched_data)
                    processed_count += 1

                    if enrichment_result.errors:
                        errors.extend(enrichment_result.errors)

                except Exception as e:
                    errors.append(f"Company enrichment error at index {i}: {str(e)}")
                    enriched_companies.append(company)  # Keep original on error
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "enrichment", i + 1, len(companies) + len(contacts)
                    )

            # Enrich contacts
            enriched_contacts = []
            for i, contact in enumerate(contacts):
                try:
                    enrichment_result = self.contact_enricher.enrich_contact(contact)
                    enriched_contacts.append(enrichment_result.enriched_data)
                    processed_count += 1

                    if enrichment_result.errors:
                        errors.extend(enrichment_result.errors)

                except Exception as e:
                    errors.append(f"Contact enrichment error at index {i}: {str(e)}")
                    enriched_contacts.append(contact)  # Keep original on error
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "enrichment",
                        len(companies) + i + 1,
                        len(companies) + len(contacts),
                    )

            duration = time.time() - start_time

            return StageResult(
                stage=ProcessingStage.ENRICHMENT,
                success=True,
                processed_count=processed_count,
                error_count=len(errors),
                duration=duration,
                data=enriched_companies + enriched_contacts,
                errors=errors,
                metadata={
                    "companies_enriched": len(enriched_companies),
                    "contacts_enriched": len(enriched_contacts),
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Enrichment stage failed: {e}")

            return StageResult(
                stage=ProcessingStage.ENRICHMENT,
                success=False,
                processed_count=processed_count,
                error_count=len(errors) + 1,
                duration=duration,
                errors=errors + [f"Enrichment stage failed: {str(e)}"],
            )

    async def _run_deduplication_stage(
        self,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> StageResult:
        """Run deduplication stage."""
        start_time = time.time()
        errors = []

        try:
            logger.info("Starting deduplication stage")

            # Deduplicate companies
            company_dedup_result = self.deduplicator.deduplicate_companies(
                companies, self.config.merge_strategy
            )

            # Deduplicate contacts
            contact_dedup_result = self.deduplicator.deduplicate_contacts(
                contacts, self.config.merge_strategy
            )

            # Collect errors
            errors.extend(company_dedup_result.errors)
            errors.extend(contact_dedup_result.errors)

            duration = time.time() - start_time
            processed_count = (
                company_dedup_result.deduplicated_count
                + contact_dedup_result.deduplicated_count
            )

            if progress_callback:
                progress_callback(
                    "deduplication", processed_count, len(companies) + len(contacts)
                )

            return StageResult(
                stage=ProcessingStage.DEDUPLICATION,
                success=True,
                processed_count=processed_count,
                error_count=len(errors),
                duration=duration,
                data=company_dedup_result.merged_records + contact_dedup_result.merged_records,
                errors=errors,
                metadata={
                    "companies_before": company_dedup_result.original_count,
                    "companies_after": company_dedup_result.deduplicated_count,
                    "company_duplicates_removed": company_dedup_result.duplicates_found,
                    "contacts_before": contact_dedup_result.original_count,
                    "contacts_after": contact_dedup_result.deduplicated_count,
                    "contact_duplicates_removed": contact_dedup_result.duplicates_found,
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Deduplication stage failed: {e}")

            return StageResult(
                stage=ProcessingStage.DEDUPLICATION,
                success=False,
                processed_count=0,
                error_count=len(errors) + 1,
                duration=duration,
                errors=errors + [f"Deduplication stage failed: {str(e)}"],
            )

    async def _run_estimation_stage(
        self,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> StageResult:
        """Run estimation stage."""
        start_time = time.time()
        errors = []
        processed_count = 0

        try:
            logger.info("Starting estimation stage")

            # Estimate company metrics
            estimated_companies = []
            for i, company in enumerate(companies):
                try:
                    estimation_result = self.estimator.estimate_company_metrics(company)
                    estimated_companies.append(estimation_result.estimated_data)
                    processed_count += 1

                    if estimation_result.errors:
                        errors.extend(estimation_result.errors)

                except Exception as e:
                    errors.append(f"Company estimation error at index {i}: {str(e)}")
                    estimated_companies.append(company)  # Keep original on error
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "estimation", i + 1, len(companies) + len(contacts)
                    )

            # Estimate contact values
            estimated_contacts = []
            for i, contact in enumerate(contacts):
                try:
                    # Find associated company for context
                    company_context = None
                    contact_company = contact.get("company")
                    if contact_company:
                        for company in estimated_companies:
                            if (
                                company.get("name", "").lower()
                                == contact_company.lower()
                            ):
                                company_context = company
                                break

                    estimation_result = self.estimator.estimate_contact_value(
                        contact, company_context
                    )
                    estimated_contacts.append(estimation_result.estimated_data)
                    processed_count += 1

                    if estimation_result.errors:
                        errors.extend(estimation_result.errors)

                except Exception as e:
                    errors.append(f"Contact estimation error at index {i}: {str(e)}")
                    estimated_contacts.append(contact)  # Keep original on error
                    if not self.config.continue_on_error:
                        raise

                if progress_callback:
                    progress_callback(
                        "estimation",
                        len(companies) + i + 1,
                        len(companies) + len(contacts),
                    )

            duration = time.time() - start_time

            return StageResult(
                stage=ProcessingStage.ESTIMATION,
                success=True,
                processed_count=processed_count,
                error_count=len(errors),
                duration=duration,
                data=estimated_companies + estimated_contacts,
                errors=errors,
                metadata={
                    "companies_estimated": len(estimated_companies),
                    "contacts_estimated": len(estimated_contacts),
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Estimation stage failed: {e}")

            return StageResult(
                stage=ProcessingStage.ESTIMATION,
                success=False,
                processed_count=processed_count,
                error_count=len(errors) + 1,
                duration=duration,
                errors=errors + [f"Estimation stage failed: {str(e)}"],
            )

    async def _run_finalization_stage(
        self,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> StageResult:
        """Run finalization stage."""
        start_time = time.time()
        errors: List[str] = []

        try:
            logger.info("Starting finalization stage")

            # Add processing metadata
            for company in companies:
                company["_processing_metadata"] = {
                    "processed_at": time.time(),
                    "pipeline_version": "1.0",
                    "processing_config": self.config.__dict__,
                }

            for contact in contacts:
                contact["_processing_metadata"] = {
                    "processed_at": time.time(),
                    "pipeline_version": "1.0",
                    "processing_config": self.config.__dict__,
                }

            duration = time.time() - start_time
            processed_count = len(companies) + len(contacts)

            if progress_callback:
                progress_callback("finalization", processed_count, processed_count)

            return StageResult(
                stage=ProcessingStage.FINALIZATION,
                success=True,
                processed_count=processed_count,
                error_count=0,
                duration=duration,
                data=companies + contacts,
                errors=errors,
                metadata={
                    "final_companies": len(companies),
                    "final_contacts": len(contacts),
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Finalization stage failed: {e}")

            return StageResult(
                stage=ProcessingStage.FINALIZATION,
                success=False,
                processed_count=0,
                error_count=1,
                duration=duration,
                errors=[f"Finalization stage failed: {str(e)}"],
            )

    async def _validate_company(
        self, company: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Validate a single company record."""
        validated_company = company.copy()
        validation_results = {}

        # Validate company name
        if "name" in company:
            name_result = self.validators["company_name"].validate(company["name"])
            validation_results["name"] = name_result
            if not name_result.is_valid and self.config.strict_validation:
                return None

        # Validate email
        if "email" in company:
            email_result = self.validators["email"].validate(company["email"])
            validation_results["email"] = email_result
            if not email_result.is_valid and self.config.strict_validation:
                return None

        # Validate phone
        if "phone" in company:
            phone_result = self.validators["phone"].validate(company["phone"])
            validation_results["phone"] = phone_result
            if not phone_result.is_valid and self.config.strict_validation:
                return None

        # Validate website/domain
        if "website" in company:
            url_result = self.validators["url"].validate(company["website"])
            validation_results["website"] = url_result
            if not url_result.is_valid and self.config.strict_validation:
                return None

        if "domain" in company:
            domain_result = self.validators["domain"].validate(company["domain"])
            validation_results["domain"] = domain_result
            if not domain_result.is_valid and self.config.strict_validation:
                return None

        # Add validation metadata
        validated_company["_validation_results"] = validation_results

        return validated_company

    async def _validate_contact(
        self, contact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Validate a single contact record."""
        validated_contact = contact.copy()
        validation_results = {}

        # Validate contact name
        full_name = (
            contact.get("full_name")
            or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        )
        if full_name:
            name_result = self.validators["contact_name"].validate(full_name)
            validation_results["name"] = name_result
            if not name_result.is_valid and self.config.strict_validation:
                return None

        # Validate email
        if "email" in contact:
            email_result = self.validators["email"].validate(contact["email"])
            validation_results["email"] = email_result
            if not email_result.is_valid and self.config.strict_validation:
                return None

        # Validate phone
        if "phone" in contact:
            phone_result = self.validators["phone"].validate(contact["phone"])
            validation_results["phone"] = phone_result
            if not phone_result.is_valid and self.config.strict_validation:
                return None

        # Validate LinkedIn URL
        if "linkedin_url" in contact:
            linkedin_result = self.validators["linkedin_url"].validate(
                contact["linkedin_url"]
            )
            validation_results["linkedin_url"] = linkedin_result
            if not linkedin_result.is_valid and self.config.strict_validation:
                return None

        # Add validation metadata
        validated_contact["_validation_results"] = validation_results

        return validated_contact

    def _extract_data_from_stage_result(
        self,
        stage_result: StageResult,
        companies: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract processed data from stage result."""
        # Since we now concatenate data in stage results, we need to split it back
        if stage_result.data:
            # Assume first half are companies, second half are contacts
            total_items = len(stage_result.data)
            company_count = len(companies)
            contact_count = len(contacts)
            
            if total_items >= company_count + contact_count:
                new_companies = stage_result.data[:company_count]
                new_contacts = stage_result.data[company_count:company_count + contact_count]
                return new_companies, new_contacts
        
        return companies, contacts

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()

    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            "total_processed": 0,
            "companies_processed": 0,
            "contacts_processed": 0,
            "errors_encountered": 0,
            "processing_time": 0.0,
        }


# Convenience functions
def create_default_pipeline() -> DataProcessingPipeline:
    """Create a pipeline with default configuration."""
    return DataProcessingPipeline()


def create_fast_pipeline() -> DataProcessingPipeline:
    """Create a pipeline optimized for speed."""
    config = ProcessingConfig(
        mode=ProcessingMode.PARALLEL,
        enable_enrichment=False,  # Skip slow enrichment
        enable_estimation=False,  # Skip estimation
        continue_on_error=True,
        max_workers=8,
    )
    return DataProcessingPipeline(config)


def create_comprehensive_pipeline() -> DataProcessingPipeline:
    """Create a pipeline with all features enabled."""
    config = ProcessingConfig(
        mode=ProcessingMode.SEQUENTIAL,
        enable_validation=True,
        enable_cleaning=True,
        enable_enrichment=True,
        enable_deduplication=True,
        enable_estimation=True,
        strict_validation=False,
        aggressive_cleaning=True,
        continue_on_error=True,
    )
    return DataProcessingPipeline(config)
