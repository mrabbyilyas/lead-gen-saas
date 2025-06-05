-- Lead Generation SaaS Row Level Security Policies
-- Migration 002: Enable RLS and create security policies

-- Enable Row Level Security on all tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_exports ENABLE ROW LEVEL SECURITY;

-- Companies table policies
-- Users can only see companies they created or have access to
CREATE POLICY "Users can view their own companies" ON companies
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert companies" ON companies
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own companies" ON companies
    FOR UPDATE USING (auth.uid() = created_by)
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can delete their own companies" ON companies
    FOR DELETE USING (auth.uid() = created_by);

-- Contacts table policies
-- Users can only see contacts from companies they have access to
CREATE POLICY "Users can view contacts from their companies" ON contacts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM companies 
            WHERE companies.id = contacts.company_id 
            AND companies.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can insert contacts for their companies" ON contacts
    FOR INSERT WITH CHECK (
        auth.uid() = created_by AND
        EXISTS (
            SELECT 1 FROM companies 
            WHERE companies.id = contacts.company_id 
            AND companies.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can update contacts from their companies" ON contacts
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM companies 
            WHERE companies.id = contacts.company_id 
            AND companies.created_by = auth.uid()
        )
    )
    WITH CHECK (
        auth.uid() = created_by AND
        EXISTS (
            SELECT 1 FROM companies 
            WHERE companies.id = contacts.company_id 
            AND companies.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can delete contacts from their companies" ON contacts
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM companies 
            WHERE companies.id = contacts.company_id 
            AND companies.created_by = auth.uid()
        )
    );

-- Scraping jobs table policies
-- Users can only see their own scraping jobs
CREATE POLICY "Users can view their own scraping jobs" ON scraping_jobs
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert scraping jobs" ON scraping_jobs
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own scraping jobs" ON scraping_jobs
    FOR UPDATE USING (auth.uid() = created_by)
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can delete their own scraping jobs" ON scraping_jobs
    FOR DELETE USING (auth.uid() = created_by);

-- Scraped data table policies
-- Users can only see scraped data from their own jobs
CREATE POLICY "Users can view scraped data from their jobs" ON scraped_data
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scraping_jobs 
            WHERE scraping_jobs.id = scraped_data.job_id 
            AND scraping_jobs.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can insert scraped data for their jobs" ON scraped_data
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM scraping_jobs 
            WHERE scraping_jobs.id = scraped_data.job_id 
            AND scraping_jobs.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can update scraped data from their jobs" ON scraped_data
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM scraping_jobs 
            WHERE scraping_jobs.id = scraped_data.job_id 
            AND scraping_jobs.created_by = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM scraping_jobs 
            WHERE scraping_jobs.id = scraped_data.job_id 
            AND scraping_jobs.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can delete scraped data from their jobs" ON scraped_data
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM scraping_jobs 
            WHERE scraping_jobs.id = scraped_data.job_id 
            AND scraping_jobs.created_by = auth.uid()
        )
    );

-- Data exports table policies
-- Users can only see their own exports
CREATE POLICY "Users can view their own exports" ON data_exports
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert exports" ON data_exports
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own exports" ON data_exports
    FOR UPDATE USING (auth.uid() = created_by)
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can delete their own exports" ON data_exports
    FOR DELETE USING (auth.uid() = created_by);

-- Create a function to check if user is admin (for future use)
CREATE OR REPLACE FUNCTION is_admin(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- This can be extended to check admin status from a user_roles table
    -- For now, we'll use a simple metadata check
    RETURN (
        SELECT COALESCE(
            (auth.jwt() ->> 'user_metadata' ->> 'is_admin')::boolean,
            false
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to get current user's organization (for future multi-tenant support)
CREATE OR REPLACE FUNCTION get_user_organization()
RETURNS UUID AS $$
BEGIN
    -- This can be extended to support multi-tenant organizations
    -- For now, we'll use the user's ID as their organization
    RETURN auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Grant permissions for the trigger function
GRANT EXECUTE ON FUNCTION update_updated_at_column() TO authenticated;
GRANT EXECUTE ON FUNCTION is_admin(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_organization() TO authenticated;