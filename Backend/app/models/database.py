from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    DECIMAL,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import uuid
from typing import Any


class Base(DeclarativeBase):
    pass


class Company(Base):
    """Company model for storing company information."""

    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    website = Column(String(500))
    industry = Column(String(100))
    company_size = Column(
        String(50)
    )  # e.g., '1-10', '11-50', '51-200', '201-500', '500+'
    location = Column(
        JSONB
    )  # {"city": "San Francisco", "state": "CA", "country": "USA"}
    description = Column(Text)
    founded_year = Column(Integer)
    revenue_range = Column(String(50))  # e.g., '$1M-$10M', '$10M-$50M'
    technology_stack = Column(JSONB)  # Array of technologies used
    social_media = Column(
        JSONB
    )  # {"linkedin": "url", "twitter": "url", "facebook": "url"}
    employee_count = Column(Integer)
    growth_signals = Column(
        JSONB
    )  # {"hiring": true, "funding": true, "expansion": false}
    pain_points = Column(JSONB)  # Array of identified pain points
    competitive_landscape = Column(JSONB)  # Array of competitors
    data_quality_score: Any = Column(DECIMAL(3, 2), default=0.00)  # 0.00 to 1.00
    lead_score: Any = Column(DECIMAL(5, 2), default=0.00)  # Calculated lead score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)

    # Relationships
    contacts = relationship(
        "Contact", back_populates="company", cascade="all, delete-orphan"
    )
    scraped_data = relationship("ScrapedData", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', domain='{self.domain}')>"


class Contact(Base):
    """Contact model for storing individual contact information."""

    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    job_title = Column(String(200))
    department = Column(String(100))
    seniority_level = Column(
        String(50)
    )  # e.g., 'Entry', 'Mid', 'Senior', 'Executive', 'C-Level'
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))
    bio = Column(Text)
    location = Column(
        JSONB
    )  # {"city": "San Francisco", "state": "CA", "country": "USA"}
    skills = Column(JSONB)  # Array of skills
    experience_years = Column(Integer)
    education = Column(JSONB)  # Array of education entries
    contact_quality_score: Any = Column(DECIMAL(3, 2), default=0.00)  # 0.00 to 1.00
    engagement_potential: Any = Column(DECIMAL(3, 2), default=0.00)  # 0.00 to 1.00
    last_activity_date = Column(DateTime(timezone=True))
    is_decision_maker = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="contacts")
    scraped_data = relationship("ScrapedData", back_populates="contact")

    def __repr__(self):
        return f"<Contact(id={self.id}, full_name='{self.full_name}', email='{self.email}')>"


class ScrapingJob(Base):
    """Scraping job model for tracking scraping operations."""

    __tablename__ = "scraping_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(String(255), nullable=False)
    job_type = Column(
        String(50), nullable=False
    )  # e.g., 'google_my_business', 'linkedin', 'website', 'directory'
    status = Column(
        String(50), default="pending"
    )  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    search_parameters = Column(JSONB, nullable=False)  # Search criteria and filters
    progress_percentage: Any = Column(DECIMAL(5, 2), default=0.00)
    total_targets = Column(Integer, default=0)
    processed_targets = Column(Integer, default=0)
    successful_extractions = Column(Integer, default=0)
    failed_extractions = Column(Integer, default=0)
    companies_found = Column(Integer, default=0)
    contacts_found = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    estimated_completion = Column(DateTime(timezone=True))
    error_message = Column(Text)
    error_details = Column(JSONB)
    performance_metrics = Column(
        JSONB
    )  # {"avg_response_time": 1.5, "rate_limit_hits": 3}
    source_urls = Column(JSONB)  # Array of URLs being scraped
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)

    # Relationships
    scraped_data = relationship(
        "ScrapedData", back_populates="scraping_job", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ScrapingJob(id={self.id}, job_name='{self.job_name}', status='{self.status}')>"


class ScrapedData(Base):
    """Scraped data model for storing raw and processed scraping results."""

    __tablename__ = "scraped_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="CASCADE")
    )
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL")
    )
    contact_id = Column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    source_type = Column(
        String(50), nullable=False
    )  # 'google_my_business', 'linkedin', 'website', 'directory'
    source_url = Column(String(1000))
    raw_data = Column(JSONB, nullable=False)  # Complete raw scraped data
    processed_data = Column(JSONB)  # Cleaned and structured data
    extraction_confidence: Any = Column(DECIMAL(3, 2), default=0.00)  # 0.00 to 1.00
    data_completeness: Any = Column(DECIMAL(3, 2), default=0.00)  # 0.00 to 1.00
    validation_status = Column(
        String(50), default="pending"
    )  # 'pending', 'valid', 'invalid', 'needs_review'
    validation_errors = Column(JSONB)  # Array of validation error messages
    duplicate_of = Column(
        UUID(as_uuid=True), ForeignKey("scraped_data.id")
    )  # Reference to original if duplicate
    is_processed = Column(Boolean, default=False)
    processing_notes = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scraping_job = relationship("ScrapingJob", back_populates="scraped_data")
    company = relationship("Company", back_populates="scraped_data")
    contact = relationship("Contact", back_populates="scraped_data")

    def __repr__(self):
        return f"<ScrapedData(id={self.id}, source_type='{self.source_type}', validation_status='{self.validation_status}')>"


class DataExport(Base):
    """Data export model for tracking export operations."""

    __tablename__ = "data_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    export_name = Column(String(255), nullable=False)
    export_type = Column(String(50), nullable=False)  # 'csv', 'excel', 'json'
    status = Column(
        String(50), default="pending"
    )  # 'pending', 'processing', 'completed', 'failed'
    filters = Column(JSONB)  # Export filters applied
    total_records = Column(Integer, default=0)
    file_path = Column(String(1000))
    file_size_bytes = Column(Integer)
    download_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)

    def __repr__(self):
        return f"<DataExport(id={self.id}, export_name='{self.export_name}', status='{self.status}')>"


# Additional utility models for future features


class UserActivity(Base):
    """User activity model for tracking user actions and analytics."""

    __tablename__ = "user_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    activity_type = Column(
        String(50), nullable=False
    )  # 'login', 'scrape', 'export', 'view', 'update'
    resource_type = Column(String(50))  # 'company', 'contact', 'scraping_job', 'export'
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)  # Additional activity details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, activity_type='{self.activity_type}')>"


class SystemMetrics(Base):
    """System metrics model for storing application performance data."""

    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value: Any = Column(DECIMAL(10, 4), nullable=False)
    metric_unit = Column(String(20))  # 'seconds', 'count', 'percentage', 'bytes'
    tags = Column(JSONB)  # Additional metric tags for filtering
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, metric_name='{self.metric_name}', metric_value={self.metric_value})>"


class APIKey(Base):
    """API key model for managing external API access."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)  # Hashed API key
    permissions = Column(JSONB)  # Array of permissions
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<APIKey(id={self.id}, key_name='{self.key_name}', is_active={self.is_active})>"
