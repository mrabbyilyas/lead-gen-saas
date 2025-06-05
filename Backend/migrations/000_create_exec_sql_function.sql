-- Create a function to execute SQL statements from the migration runner
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  EXECUTE sql;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated;

-- Add comment for documentation
COMMENT ON FUNCTION exec_sql(text) IS 'Execute SQL statements for migrations';