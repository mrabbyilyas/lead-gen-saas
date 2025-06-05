-- Lead Generation SaaS Seed Data
-- Migration 003: Insert sample data for development and testing

-- Note: This seed data is for development/testing purposes only
-- In production, you may want to skip this migration or use different data

-- Insert sample companies
INSERT INTO companies (
    id,
    name,
    domain,
    website,
    industry,
    company_size,
    location,
    description,
    founded_year,
    revenue_range,
    technology_stack,
    social_media,
    employee_count,
    growth_signals,
    pain_points,
    competitive_landscape,
    data_quality_score,
    lead_score
) VALUES 
(
    '550e8400-e29b-41d4-a716-446655440001',
    'TechStart Solutions',
    'techstart.com',
    'https://www.techstart.com',
    'Software Development',
    '11-50',
    '{"city": "San Francisco", "state": "CA", "country": "USA"}',
    'A innovative software development company specializing in AI and machine learning solutions for enterprise clients.',
    2018,
    '$1M-$10M',
    '["Python", "React", "AWS", "Docker", "Kubernetes"]',
    '{"linkedin": "https://linkedin.com/company/techstart", "twitter": "@techstart"}',
    35,
    '{"hiring": true, "funding": true, "expansion": false}',
    '["Scalability", "Data Integration", "Customer Acquisition"]',
    '["Competitor A", "Competitor B"]',
    0.85,
    78.50
),
(
    '550e8400-e29b-41d4-a716-446655440002',
    'Digital Marketing Pro',
    'digitalmarketingpro.com',
    'https://www.digitalmarketingpro.com',
    'Marketing & Advertising',
    '51-200',
    '{"city": "New York", "state": "NY", "country": "USA"}',
    'Full-service digital marketing agency helping businesses grow their online presence.',
    2015,
    '$10M-$50M',
    '["Google Ads", "Facebook Ads", "HubSpot", "Salesforce", "Analytics"]',
    '{"linkedin": "https://linkedin.com/company/digitalmarketingpro", "facebook": "https://facebook.com/digitalmarketingpro"}',
    125,
    '{"hiring": true, "funding": false, "expansion": true}',
    '["Lead Quality", "Attribution Tracking", "Client Retention"]',
    '["Agency X", "Marketing Corp"]',
    0.92,
    85.75
),
(
    '550e8400-e29b-41d4-a716-446655440003',
    'HealthTech Innovations',
    'healthtech-innovations.com',
    'https://www.healthtech-innovations.com',
    'Healthcare Technology',
    '201-500',
    '{"city": "Boston", "state": "MA", "country": "USA"}',
    'Developing cutting-edge healthcare technology solutions to improve patient outcomes.',
    2012,
    '$50M-$100M',
    '["React Native", "Node.js", "MongoDB", "HIPAA Compliance", "ML/AI"]',
    '{"linkedin": "https://linkedin.com/company/healthtech-innovations"}',
    280,
    '{"hiring": true, "funding": true, "expansion": true}',
    '["Regulatory Compliance", "Data Security", "Integration Challenges"]',
    '["MedTech Leader", "Health Solutions Inc"]',
    0.88,
    92.25
);

-- Insert sample contacts
INSERT INTO contacts (
    id,
    company_id,
    first_name,
    last_name,
    full_name,
    email,
    phone,
    job_title,
    department,
    seniority_level,
    linkedin_url,
    twitter_handle,
    bio,
    location,
    skills,
    experience_years,
    education,
    contact_quality_score,
    engagement_potential,
    is_decision_maker,
    is_verified
) VALUES 
(
    '660e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440001',
    'John',
    'Smith',
    'John Smith',
    'john.smith@techstart.com',
    '+1-555-0101',
    'Chief Technology Officer',
    'Engineering',
    'C-Level',
    'https://linkedin.com/in/johnsmith-cto',
    '@johnsmith_tech',
    'Experienced CTO with 15+ years in software development and team leadership.',
    '{"city": "San Francisco", "state": "CA", "country": "USA"}',
    '["Python", "Machine Learning", "Team Leadership", "Architecture Design"]',
    15,
    '[{"degree": "MS Computer Science", "school": "Stanford University", "year": 2008}]',
    0.95,
    0.88,
    true,
    true
),
(
    '660e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440001',
    'Sarah',
    'Johnson',
    'Sarah Johnson',
    'sarah.johnson@techstart.com',
    '+1-555-0102',
    'VP of Sales',
    'Sales',
    'Executive',
    'https://linkedin.com/in/sarahjohnson-sales',
    '@sarah_sales',
    'Results-driven sales executive with a track record of exceeding targets.',
    '{"city": "San Francisco", "state": "CA", "country": "USA"}',
    '["B2B Sales", "Relationship Building", "Negotiation", "CRM"]',
    12,
    '[{"degree": "MBA", "school": "UC Berkeley", "year": 2012}]',
    0.90,
    0.92,
    true,
    true
),
(
    '660e8400-e29b-41d4-a716-446655440003',
    '550e8400-e29b-41d4-a716-446655440002',
    'Michael',
    'Brown',
    'Michael Brown',
    'michael.brown@digitalmarketingpro.com',
    '+1-555-0201',
    'CEO & Founder',
    'Executive',
    'C-Level',
    'https://linkedin.com/in/michaelbrown-ceo',
    '@mike_marketing',
    'Serial entrepreneur and marketing expert with 20+ years of experience.',
    '{"city": "New York", "state": "NY", "country": "USA"}',
    '["Digital Marketing", "Strategy", "Leadership", "Growth Hacking"]',
    20,
    '[{"degree": "BA Marketing", "school": "NYU", "year": 2003}]',
    0.98,
    0.95,
    true,
    true
),
(
    '660e8400-e29b-41d4-a716-446655440004',
    '550e8400-e29b-41d4-a716-446655440003',
    'Dr. Emily',
    'Davis',
    'Dr. Emily Davis',
    'emily.davis@healthtech-innovations.com',
    '+1-555-0301',
    'Chief Medical Officer',
    'Medical',
    'C-Level',
    'https://linkedin.com/in/dr-emilydavis',
    '@dr_emily_health',
    'Board-certified physician and healthcare technology innovator.',
    '{"city": "Boston", "state": "MA", "country": "USA"}',
    '["Healthcare", "Medical Technology", "Regulatory Affairs", "Clinical Research"]',
    18,
    '[{"degree": "MD", "school": "Harvard Medical School", "year": 2005}, {"degree": "MBA", "school": "MIT Sloan", "year": 2010}]',
    0.96,
    0.90,
    true,
    true
);

-- Insert sample scraping jobs
INSERT INTO scraping_jobs (
    id,
    job_name,
    job_type,
    status,
    search_parameters,
    progress_percentage,
    total_targets,
    processed_targets,
    successful_extractions,
    failed_extractions,
    companies_found,
    contacts_found,
    start_time,
    end_time,
    performance_metrics,
    source_urls
) VALUES 
(
    '770e8400-e29b-41d4-a716-446655440001',
    'Tech Companies in SF',
    'google_my_business',
    'completed',
    '{"location": "San Francisco, CA", "industry": "Technology", "keywords": ["software", "tech", "startup"]}',
    100.00,
    50,
    50,
    45,
    5,
    25,
    35,
    '2024-01-15 10:00:00+00',
    '2024-01-15 12:30:00+00',
    '{"avg_response_time": 1.2, "rate_limit_hits": 2, "success_rate": 0.90}',
    '["https://maps.google.com/search/tech+companies+san+francisco"]'
),
(
    '770e8400-e29b-41d4-a716-446655440002',
    'Marketing Agencies NYC',
    'linkedin',
    'completed',
    '{"location": "New York, NY", "industry": "Marketing", "company_size": "51-200"}',
    100.00,
    30,
    30,
    28,
    2,
    15,
    42,
    '2024-01-16 14:00:00+00',
    '2024-01-16 16:45:00+00',
    '{"avg_response_time": 2.1, "rate_limit_hits": 5, "success_rate": 0.93}',
    '["https://linkedin.com/search/results/companies/"]'
),
(
    '770e8400-e29b-41d4-a716-446655440003',
    'Healthcare Tech Boston',
    'website',
    'running',
    '{"location": "Boston, MA", "industry": "Healthcare Technology", "keywords": ["healthtech", "medical", "digital health"]}',
    65.00,
    40,
    26,
    24,
    2,
    12,
    18,
    '2024-01-17 09:00:00+00',
    NULL,
    '{"avg_response_time": 1.8, "rate_limit_hits": 1, "success_rate": 0.92}',
    '["https://example-directory.com/healthcare-companies"]'
);

-- Insert sample scraped data
INSERT INTO scraped_data (
    id,
    job_id,
    company_id,
    contact_id,
    source_type,
    source_url,
    raw_data,
    processed_data,
    extraction_confidence,
    data_completeness,
    validation_status,
    is_processed,
    scraped_at,
    processed_at
) VALUES 
(
    '880e8400-e29b-41d4-a716-446655440001',
    '770e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440001',
    '660e8400-e29b-41d4-a716-446655440001',
    'google_my_business',
    'https://maps.google.com/place/techstart-solutions',
    '{"name": "TechStart Solutions", "address": "123 Tech St, San Francisco, CA", "phone": "+1-555-0100", "website": "techstart.com", "rating": 4.5, "reviews": 25}',
    '{"company_name": "TechStart Solutions", "domain": "techstart.com", "location": {"city": "San Francisco", "state": "CA"}, "phone": "+1-555-0100"}',
    0.95,
    0.88,
    'valid',
    true,
    '2024-01-15 10:15:00+00',
    '2024-01-15 10:20:00+00'
),
(
    '880e8400-e29b-41d4-a716-446655440002',
    '770e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440002',
    '660e8400-e29b-41d4-a716-446655440003',
    'linkedin',
    'https://linkedin.com/company/digitalmarketingpro',
    '{"company_name": "Digital Marketing Pro", "industry": "Marketing Services", "size": "51-200 employees", "location": "New York, NY", "description": "Full-service digital marketing agency"}',
    '{"company_name": "Digital Marketing Pro", "industry": "Marketing & Advertising", "employee_count": 125, "location": {"city": "New York", "state": "NY"}}',
    0.92,
    0.85,
    'valid',
    true,
    '2024-01-16 14:30:00+00',
    '2024-01-16 14:35:00+00'
);

-- Insert sample data exports
INSERT INTO data_exports (
    id,
    export_name,
    export_type,
    status,
    filters,
    total_records,
    file_path,
    file_size_bytes,
    download_count,
    expires_at
) VALUES 
(
    '990e8400-e29b-41d4-a716-446655440001',
    'Tech Companies Export - Jan 2024',
    'csv',
    'completed',
    '{"industry": "Technology", "location": "San Francisco, CA", "date_range": {"start": "2024-01-01", "end": "2024-01-31"}}',
    25,
    '/exports/tech_companies_jan_2024.csv',
    156789,
    3,
    '2024-02-15 23:59:59+00'
),
(
    '990e8400-e29b-41d4-a716-446655440002',
    'All Contacts Export',
    'excel',
    'completed',
    '{"include_contacts": true, "verified_only": true}',
    42,
    '/exports/all_contacts_verified.xlsx',
    234567,
    1,
    '2024-02-20 23:59:59+00'
);

-- Update sequences to avoid conflicts with seed data
-- Note: In PostgreSQL with UUID primary keys, this is not typically necessary
-- but included for completeness in case integer IDs are used elsewhere

-- Add some comments for documentation
COMMENT ON TABLE companies IS 'Stores company information extracted from various sources';
COMMENT ON TABLE contacts IS 'Stores individual contact information linked to companies';
COMMENT ON TABLE scraping_jobs IS 'Tracks scraping operations and their progress';
COMMENT ON TABLE scraped_data IS 'Stores raw and processed data from scraping operations';
COMMENT ON TABLE data_exports IS 'Tracks data export operations and file downloads';

COMMENT ON COLUMN companies.lead_score IS 'Calculated lead score based on various factors (0-100)';
COMMENT ON COLUMN companies.data_quality_score IS 'Quality score of the company data (0.00-1.00)';
COMMENT ON COLUMN contacts.contact_quality_score IS 'Quality score of the contact data (0.00-1.00)';
COMMENT ON COLUMN contacts.engagement_potential IS 'Potential for successful engagement (0.00-1.00)';
COMMENT ON COLUMN scraped_data.extraction_confidence IS 'Confidence level of data extraction (0.00-1.00)';
COMMENT ON COLUMN scraped_data.data_completeness IS 'Completeness of extracted data (0.00-1.00)';