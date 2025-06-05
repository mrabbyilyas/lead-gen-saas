"""Database utilities and helper functions."""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime, timedelta
from supabase import Client

from app.core.database import get_supabase_client
from app.services.supabase_service import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Utility class for common database operations."""
    
    def __init__(self):
        self.client: Client = get_supabase_client()
    
    def execute_rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a stored procedure/function."""
        try:
            response = self.client.rpc(function_name, params or {})
            return response.execute()
        except Exception as e:
            logger.error(f"Error executing RPC {function_name}: {str(e)}")
            raise DatabaseError(f"RPC execution failed: {str(e)}")
    
    def bulk_insert(self, table_name: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple records in a single operation."""
        try:
            # Add timestamps to all records
            now = datetime.utcnow().isoformat()
            for record in records:
                if "created_at" not in record:
                    record["created_at"] = now
                if "updated_at" not in record:
                    record["updated_at"] = now
            
            response = self.client.table(table_name).insert(records).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error in bulk insert for table {table_name}: {str(e)}")
            raise DatabaseError(f"Bulk insert failed: {str(e)}")
    
    def bulk_update(self, table_name: str, updates: List[Dict[str, Any]], id_field: str = "id") -> List[Dict[str, Any]]:
        """Update multiple records in batch."""
        try:
            results = []
            now = datetime.utcnow().isoformat()
            
            for update_data in updates:
                if id_field not in update_data:
                    continue
                
                record_id = update_data.pop(id_field)
                update_data["updated_at"] = now
                
                response = self.client.table(table_name).update(update_data).eq(id_field, record_id).execute()
                if response.data:
                    results.extend(response.data)
            
            return results
        except Exception as e:
            logger.error(f"Error in bulk update for table {table_name}: {str(e)}")
            raise DatabaseError(f"Bulk update failed: {str(e)}")
    
    def bulk_delete(self, table_name: str, ids: List[Union[str, UUID]], id_field: str = "id") -> int:
        """Delete multiple records by IDs."""
        try:
            str_ids = [str(id_val) for id_val in ids]
            response = self.client.table(table_name).delete().in_(id_field, str_ids).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Error in bulk delete for table {table_name}: {str(e)}")
            raise DatabaseError(f"Bulk delete failed: {str(e)}")
    
    def get_table_stats(self, table_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a table."""
        try:
            query = self.client.table(table_name).select("*", count="exact")
            
            if user_id:
                query = query.eq("created_by", user_id)
            
            response = query.execute()
            total_count = response.count or 0
            
            # Get recent records count (last 7 days)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            recent_query = self.client.table(table_name).select("*", count="exact").gte("created_at", week_ago)
            
            if user_id:
                recent_query = recent_query.eq("created_by", user_id)
            
            recent_response = recent_query.execute()
            recent_count = recent_response.count or 0
            
            return {
                "table_name": table_name,
                "total_records": total_count,
                "recent_records": recent_count,
                "growth_rate": (recent_count / total_count * 100) if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting stats for table {table_name}: {str(e)}")
            raise DatabaseError(f"Failed to get table stats: {str(e)}")
    
    def cleanup_old_records(self, table_name: str, days_old: int = 30, date_field: str = "created_at") -> int:
        """Clean up old records from a table."""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
            response = self.client.table(table_name).delete().lt(date_field, cutoff_date).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Error cleaning up old records from {table_name}: {str(e)}")
            raise DatabaseError(f"Cleanup failed: {str(e)}")
    
    def get_duplicate_records(
        self,
        table_name: str,
        duplicate_fields: List[str],
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find duplicate records based on specified fields."""
        try:
            # This is a simplified approach - in production, you might want to use SQL functions
            query = self.client.table(table_name).select("*")
            
            if user_id:
                query = query.eq("created_by", user_id)
            
            response = query.execute()
            records = response.data or []
            
            # Group records by duplicate fields
            groups = {}
            for record in records:
                key = tuple(str(record.get(field, "")) for field in duplicate_fields)
                if key not in groups:
                    groups[key] = []
                groups[key].append(record)
            
            # Return groups with more than one record
            duplicates = []
            for group in groups.values():
                if len(group) > 1:
                    duplicates.extend(group[1:])  # Keep first, mark others as duplicates
            
            return duplicates
        except Exception as e:
            logger.error(f"Error finding duplicates in {table_name}: {str(e)}")
            raise DatabaseError(f"Duplicate detection failed: {str(e)}")
    
    def archive_records(
        self,
        table_name: str,
        archive_table_name: str,
        record_ids: List[Union[str, UUID]]
    ) -> Dict[str, int]:
        """Archive records by moving them to an archive table."""
        try:
            # Get records to archive
            str_ids = [str(id_val) for id_val in record_ids]
            response = self.client.table(table_name).select("*").in_("id", str_ids).execute()
            records = response.data or []
            
            if not records:
                return {"archived": 0, "deleted": 0}
            
            # Add archive timestamp
            now = datetime.utcnow().isoformat()
            for record in records:
                record["archived_at"] = now
            
            # Insert into archive table
            archive_response = self.client.table(archive_table_name).insert(records).execute()
            archived_count = len(archive_response.data) if archive_response.data else 0
            
            # Delete from original table
            delete_response = self.client.table(table_name).delete().in_("id", str_ids).execute()
            deleted_count = len(delete_response.data) if delete_response.data else 0
            
            return {"archived": archived_count, "deleted": deleted_count}
        except Exception as e:
            logger.error(f"Error archiving records from {table_name}: {str(e)}")
            raise DatabaseError(f"Archive operation failed: {str(e)}")
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get database health information."""
        try:
            # Test basic connectivity
            start_time = datetime.utcnow()
            test_response = self.client.table("companies").select("id").limit(1).execute()
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000  # milliseconds
            
            # Get table counts
            tables = ["companies", "contacts", "scraping_jobs", "scraped_data", "data_exports"]
            table_stats = {}
            
            for table in tables:
                try:
                    count_response = self.client.table(table).select("*", count="exact").execute()
                    table_stats[table] = count_response.count or 0
                except Exception:
                    table_stats[table] = -1  # Error getting count
            
            return {
                "status": "healthy" if response_time < 1000 else "slow",
                "response_time_ms": response_time,
                "table_counts": table_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking database health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def optimize_table_performance(self, table_name: str) -> Dict[str, Any]:
        """Get performance optimization suggestions for a table."""
        try:
            # Get table statistics
            stats = self.get_table_stats(table_name)
            
            suggestions = []
            
            # Check for large tables that might need indexing
            if stats["total_records"] > 10000:
                suggestions.append("Consider adding indexes for frequently queried columns")
            
            # Check growth rate
            if stats["growth_rate"] > 50:
                suggestions.append("High growth rate detected - consider data archiving strategy")
            
            # Check for old records
            old_records_query = self.client.table(table_name).select("*", count="exact")
            month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            old_records_query = old_records_query.lt("created_at", month_ago)
            old_response = old_records_query.execute()
            old_count = old_response.count or 0
            
            if old_count > 1000:
                suggestions.append(f"Consider archiving {old_count} old records")
            
            return {
                "table_name": table_name,
                "statistics": stats,
                "suggestions": suggestions,
                "old_records_count": old_count
            }
        except Exception as e:
            logger.error(f"Error analyzing table performance for {table_name}: {str(e)}")
            raise DatabaseError(f"Performance analysis failed: {str(e)}")


# Global database utils instance
_db_utils = None


def get_database_utils() -> DatabaseUtils:
    """Get the global database utils instance."""
    global _db_utils
    if _db_utils is None:
        _db_utils = DatabaseUtils()
    return _db_utils