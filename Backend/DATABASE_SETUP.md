# Database Setup Guide for Lead Generation SaaS

This guide explains how to set up the database schema in Supabase for the Lead Generation SaaS application.

## Prerequisites

1. A Supabase project created at [supabase.com](https://supabase.com)
2. Access to the Supabase SQL Editor in your project dashboard
3. Your Supabase URL and API key configured in the `.env` file

## Setup Instructions

### Step 1: Execute the Schema Setup SQL

1. Open your Supabase project dashboard
2. Navigate to the **SQL Editor** in the left sidebar
3. Create a new query
4. Copy the entire contents of `supabase_schema_setup.sql` and paste it into the SQL Editor
5. Click **Run** to execute the SQL

### Step 2: Verify the Setup

After running the SQL, you should see:
- A success message: "Database schema setup completed successfully!"
- The following tables created in your database:
  - `schema_migrations`
  - `companies`
  - `contacts`
  - `scraping_jobs`
  - `scraped_data`
  - `data_exports`

### Step 3: Test the Connection

Run the following command to test the database connection:

```bash
python -c "from app.core.database import test_database_connection; test_database_connection()"
```

## Database Schema Overview

### Core Tables

#### 1. Companies Table
Stores information about companies that are being tracked or scraped.
- **Primary Key**: `id` (UUID)
- **Key Fields**: `name`, `domain`, `industry`, `size_range`, `location`
- **Relationships**: Referenced by `contacts` and `scraped_data`
- **Security**: Row Level Security enabled, users can only access their own data

#### 2. Contacts Table
Stores individual contact information within companies.
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `company_id` → `companies.id`
- **Key Fields**: `first_name`, `last_name`, `email`, `job_title`
- **Security**: Row Level Security enabled, users can only access their own data

#### 3. Scraping Jobs Table
Tracks web scraping jobs and their status.
- **Primary Key**: `id` (UUID)
- **Key Fields**: `name`, `target_url`, `status`, `progress`
- **Status Values**: `pending`, `running`, `completed`, `failed`, `cancelled`
- **Security**: Row Level Security enabled, users can only access their own data

#### 4. Scraped Data Table
Stores raw and processed data from scraping operations.
- **Primary Key**: `id` (UUID)
- **Foreign Keys**: `job_id`, `company_id`, `contact_id`
- **Key Fields**: `data_type`, `raw_data`, `processed_data`, `confidence_score`
- **Security**: Row Level Security enabled, users can only access their own data

#### 5. Data Exports Table
Tracks data export requests and their status.
- **Primary Key**: `id` (UUID)
- **Key Fields**: `name`, `export_type`, `status`, `file_path`
- **Export Types**: `csv`, `xlsx`, `json`, `pdf`
- **Security**: Row Level Security enabled, users can only access their own data

### Security Features

#### Row Level Security (RLS)
All tables have RLS enabled with policies that ensure:
- Users can only view, insert, update, and delete their own data
- Data isolation between different users
- Automatic filtering based on the authenticated user's ID

#### Authentication Integration
The schema integrates with Supabase Auth:
- All tables have a `created_by` field that references `auth.users.id`
- RLS policies use `auth.uid()` to identify the current user
- Automatic user-based data filtering

### Performance Optimizations

#### Indexes
The schema includes indexes on frequently queried columns:
- Foreign key columns for join performance
- Status columns for filtering
- Created date columns for sorting
- Email and domain columns for searching

#### Triggers
Automatic `updated_at` timestamp updates using database triggers:
- Ensures data consistency
- Tracks when records were last modified
- No application-level code required

## Migration Management

The application includes a migration system for future schema changes:

### Running Migrations
```bash
python -m app.core.migrations migrate
```

### Checking Migration Status
```bash
python -m app.core.migrations status
```

### Rolling Back Migrations
```bash
python -m app.core.migrations rollback <migration_name>
```

## Adding Sample Data

To add sample data for testing:

1. First, get your user ID from Supabase Auth
2. Replace `'your-user-id-here'` in the commented sample data section of `supabase_schema_setup.sql`
3. Uncomment and run the INSERT statements

Alternatively, you can use the API endpoints to create test data once the application is running.

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Ensure RLS policies are correctly configured
   - Verify that the user is authenticated
   - Check that `created_by` fields are properly set

2. **Connection Errors**
   - Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
   - Check that the Supabase project is active
   - Ensure network connectivity

3. **Migration Errors**
   - Check that the `schema_migrations` table exists
   - Verify SQL syntax in migration files
   - Ensure proper file permissions

### Useful SQL Queries

#### Check Table Existence
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';
```

#### Check RLS Status
```sql
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

#### View RLS Policies
```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';
```

## Next Steps

After setting up the database:

1. Test the API endpoints to ensure they can interact with the database
2. Set up authentication in your frontend application
3. Configure any additional Supabase features (Storage, Edge Functions, etc.)
4. Set up monitoring and backup strategies
5. Configure production environment variables

## Support

For issues related to:
- **Supabase**: Check the [Supabase Documentation](https://supabase.com/docs)
- **PostgreSQL**: Refer to the [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- **Application**: Review the API documentation and error logs