-- Lead Generation SaaS - Complete Database Schema Setup
-- Execute this SQL in your Supabase SQL Editor

-- 1. Create schema_migrations table for tracking migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64)
);

-- 2. Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),
    size_range VARCHAR(50),
    location VARCHAR(255),
    description TEXT,
    website_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    phone VARCHAR(50),
    email VARCHAR(255),
    founded_year INTEGER,
    revenue_range VARCHAR(50),
    employee_count INTEGER,
    technologies JSONB DEFAULT '[]'::jsonb,
    social_media JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    job_title VARCHAR(255),
    department VARCHAR(100),
    seniority_level VARCHAR(50),
    linkedin_url VARCHAR(500),
    twitter_url VARCHAR(500),
    bio TEXT,
    location VARCHAR(255),
    years_at_company INTEGER,
    previous_companies JSONB DEFAULT '[]'::jsonb,
    skills JSONB DEFAULT '[]'::jsonb,
    interests JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create scraping_jobs table
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_url VARCHAR(1000) NOT NULL,
    scraping_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create scraped_data table
CREATE TABLE IF NOT EXISTS scraped_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('company', 'contact', 'mixed')),
    raw_data JSONB NOT NULL,
    processed_data JSONB,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    validation_status VARCHAR(50) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'valid', 'invalid', 'needs_review')),
    validation_errors JSONB DEFAULT '[]'::jsonb,
    source_url VARCHAR(1000),
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Create data_exports table
CREATE TABLE IF NOT EXISTS data_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    export_type VARCHAR(50) NOT NULL CHECK (export_type IN ('csv', 'xlsx', 'json', 'pdf')),
    filters JSONB DEFAULT '{}'::jsonb,
    columns JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    file_path VARCHAR(1000),
    file_size INTEGER,
    download_url VARCHAR(1000),
    expires_at TIMESTAMP WITH TIME ZONE,
    download_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_created_by ON companies(created_by);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at);

CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_created_by ON contacts(created_by);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(first_name, last_name);

CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_by ON scraping_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_at ON scraping_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_scraped_data_job_id ON scraped_data(job_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_company_id ON scraped_data(company_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_contact_id ON scraped_data(contact_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_type ON scraped_data(data_type);
CREATE INDEX IF NOT EXISTS idx_scraped_data_validation_status ON scraped_data(validation_status);

CREATE INDEX IF NOT EXISTS idx_data_exports_status ON data_exports(status);
CREATE INDEX IF NOT EXISTS idx_data_exports_created_by ON data_exports(created_by);
CREATE INDEX IF NOT EXISTS idx_data_exports_created_at ON data_exports(created_at);

-- 8. Create function to automatically update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 9. Create triggers for updated_at columns
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

-- 10. Enable Row Level Security (RLS)
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_exports ENABLE ROW LEVEL SECURITY;

-- 11. Create RLS Policies

-- Companies policies
CREATE POLICY "Users can view their own companies" ON companies
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert their own companies" ON companies
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own companies" ON companies
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete their own companies" ON companies
    FOR DELETE USING (auth.uid() = created_by);

-- Contacts policies
CREATE POLICY "Users can view their own contacts" ON contacts
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert their own contacts" ON contacts
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own contacts" ON contacts
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete their own contacts" ON contacts
    FOR DELETE USING (auth.uid() = created_by);

-- Scraping jobs policies
CREATE POLICY "Users can view their own scraping jobs" ON scraping_jobs
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert their own scraping jobs" ON scraping_jobs
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own scraping jobs" ON scraping_jobs
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete their own scraping jobs" ON scraping_jobs
    FOR DELETE USING (auth.uid() = created_by);

-- Scraped data policies
CREATE POLICY "Users can view their own scraped data" ON scraped_data
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert their own scraped data" ON scraped_data
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own scraped data" ON scraped_data
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete their own scraped data" ON scraped_data
    FOR DELETE USING (auth.uid() = created_by);

-- Data exports policies
CREATE POLICY "Users can view their own data exports" ON data_exports
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert their own data exports" ON data_exports
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own data exports" ON data_exports
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete their own data exports" ON data_exports
    FOR DELETE USING (auth.uid() = created_by);

-- 12. Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- 13. Insert sample data for testing

-- Note: The following sample data uses placeholder UUIDs
-- In a real scenario, these would be actual user IDs from auth.users

-- Sample companies (replace user_id with actual auth.users.id)
/*
INSERT INTO companies (name, domain, industry, size_range, location, description, website_url, created_by) VALUES
('TechCorp Solutions', 'techcorp.com', 'Technology', '51-200', 'San Francisco, CA', 'Leading software development company', 'https://techcorp.com', 'your-user-id-here'),
('DataFlow Analytics', 'dataflow.io', 'Data Analytics', '11-50', 'New York, NY', 'Advanced data analytics platform', 'https://dataflow.io', 'your-user-id-here'),
('CloudScale Systems', 'cloudscale.net', 'Cloud Computing', '201-500', 'Seattle, WA', 'Enterprise cloud solutions provider', 'https://cloudscale.net', 'your-user-id-here');
*/

-- Record this migration as executed
INSERT INTO schema_migrations (migration_name, checksum) VALUES 
('complete_schema_setup.sql', 'manual_setup_' || extract(epoch from now())::text)
ON CONFLICT (migration_name) DO NOTHING;

-- Success message
SELECT 'Database schema setup completed successfully!' as status;