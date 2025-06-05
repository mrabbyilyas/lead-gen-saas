-- Lead Generation SaaS Database Schema
-- Migration 001: Create core tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Companies table - stores company information
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    website VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50), -- e.g., '1-10', '11-50', '51-200', '201-500', '500+'
    location JSONB, -- {"city": "San Francisco", "state": "CA", "country": "USA"}
    description TEXT,
    founded_year INTEGER,
    revenue_range VARCHAR(50), -- e.g., '$1M-$10M', '$10M-$50M'
    technology_stack JSONB, -- Array of technologies used
    social_media JSONB, -- {"linkedin": "url", "twitter": "url", "facebook": "url"}
    employee_count INTEGER,
    growth_signals JSONB, -- {"hiring": true, "funding": true, "expansion": false}
    pain_points JSONB, -- Array of identified pain points
    competitive_landscape JSONB, -- Array of competitors
    data_quality_score DECIMAL(3,2) DEFAULT 0.00, -- 0.00 to 1.00
    lead_score DECIMAL(5,2) DEFAULT 0.00, -- Calculated lead score
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    -- Constraints
    CONSTRAINT companies_data_quality_score_check CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    CONSTRAINT companies_lead_score_check CHECK (lead_score >= 0),
    CONSTRAINT companies_founded_year_check CHECK (founded_year > 1800 AND founded_year <= EXTRACT(YEAR FROM NOW()))
);

-- Contacts table - stores individual contact information
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    job_title VARCHAR(200),
    department VARCHAR(100),
    seniority_level VARCHAR(50), -- e.g., 'Entry', 'Mid', 'Senior', 'Executive', 'C-Level'
    linkedin_url VARCHAR(500),
    twitter_handle VARCHAR(100),
    bio TEXT,
    location JSONB, -- {"city": "San Francisco", "state": "CA", "country": "USA"}
    skills JSONB, -- Array of skills
    experience_years INTEGER,
    education JSONB, -- Array of education entries
    contact_quality_score DECIMAL(3,2) DEFAULT 0.00, -- 0.00 to 1.00
    engagement_potential DECIMAL(3,2) DEFAULT 0.00, -- 0.00 to 1.00
    last_activity_date TIMESTAMP WITH TIME ZONE,
    is_decision_maker BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    -- Constraints
    CONSTRAINT contacts_quality_score_check CHECK (contact_quality_score >= 0 AND contact_quality_score <= 1),
    CONSTRAINT contacts_engagement_check CHECK (engagement_potential >= 0 AND engagement_potential <= 1),
    CONSTRAINT contacts_experience_check CHECK (experience_years >= 0 AND experience_years <= 70)
);

-- Scraping jobs table - tracks scraping operations
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- e.g., 'google_my_business', 'linkedin', 'website', 'directory'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    search_parameters JSONB NOT NULL, -- Search criteria and filters
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    total_targets INTEGER DEFAULT 0,
    processed_targets INTEGER DEFAULT 0,
    successful_extractions INTEGER DEFAULT 0,
    failed_extractions INTEGER DEFAULT 0,
    companies_found INTEGER DEFAULT 0,
    contacts_found INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    error_details JSONB,
    performance_metrics JSONB, -- {"avg_response_time": 1.5, "rate_limit_hits": 3}
    source_urls JSONB, -- Array of URLs being scraped
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    -- Constraints
    CONSTRAINT scraping_jobs_progress_check CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT scraping_jobs_status_check CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Scraped data table - raw data from scraping operations
CREATE TABLE IF NOT EXISTS scraped_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    source_type VARCHAR(50) NOT NULL, -- 'google_my_business', 'linkedin', 'website', 'directory'
    source_url VARCHAR(1000),
    raw_data JSONB NOT NULL, -- Complete raw scraped data
    processed_data JSONB, -- Cleaned and structured data
    extraction_confidence DECIMAL(3,2) DEFAULT 0.00, -- 0.00 to 1.00
    data_completeness DECIMAL(3,2) DEFAULT 0.00, -- 0.00 to 1.00
    validation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'valid', 'invalid', 'needs_review'
    validation_errors JSONB, -- Array of validation error messages
    duplicate_of UUID REFERENCES scraped_data(id), -- Reference to original if duplicate
    is_processed BOOLEAN DEFAULT FALSE,
    processing_notes TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT scraped_data_confidence_check CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
    CONSTRAINT scraped_data_completeness_check CHECK (data_completeness >= 0 AND data_completeness <= 1),
    CONSTRAINT scraped_data_validation_check CHECK (validation_status IN ('pending', 'valid', 'invalid', 'needs_review'))
);

-- Data exports table - track export operations
CREATE TABLE IF NOT EXISTS data_exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    export_name VARCHAR(255) NOT NULL,
    export_type VARCHAR(50) NOT NULL, -- 'csv', 'excel', 'json'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    filters JSONB, -- Export filters applied
    total_records INTEGER DEFAULT 0,
    file_path VARCHAR(1000),
    file_size_bytes BIGINT,
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    -- Constraints
    CONSTRAINT data_exports_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT data_exports_type_check CHECK (export_type IN ('csv', 'excel', 'json'))
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_company_size ON companies(company_size);
CREATE INDEX IF NOT EXISTS idx_companies_lead_score ON companies(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_companies_created_by ON companies(created_by);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at);
CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_job_title ON contacts(job_title);
CREATE INDEX IF NOT EXISTS idx_contacts_seniority_level ON contacts(seniority_level);
CREATE INDEX IF NOT EXISTS idx_contacts_is_decision_maker ON contacts(is_decision_maker);
CREATE INDEX IF NOT EXISTS idx_contacts_created_by ON contacts(created_by);
CREATE INDEX IF NOT EXISTS idx_contacts_full_name_trgm ON contacts USING gin(full_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_job_type ON scraping_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_by ON scraping_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_at ON scraping_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_scraped_data_job_id ON scraped_data(job_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_company_id ON scraped_data(company_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_contact_id ON scraped_data(contact_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_source_type ON scraped_data(source_type);
CREATE INDEX IF NOT EXISTS idx_scraped_data_validation_status ON scraped_data(validation_status);
CREATE INDEX IF NOT EXISTS idx_scraped_data_is_processed ON scraped_data(is_processed);

CREATE INDEX IF NOT EXISTS idx_data_exports_status ON data_exports(status);
CREATE INDEX IF NOT EXISTS idx_data_exports_export_type ON data_exports(export_type);
CREATE INDEX IF NOT EXISTS idx_data_exports_created_by ON data_exports(created_by);
CREATE INDEX IF NOT EXISTS idx_data_exports_created_at ON data_exports(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scraping_jobs_updated_at BEFORE UPDATE ON scraping_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scraped_data_updated_at BEFORE UPDATE ON scraped_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_exports_updated_at BEFORE UPDATE ON data_exports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();