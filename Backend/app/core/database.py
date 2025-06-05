from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """Supabase client wrapper"""

    def __init__(self) -> None:
        self._client: Optional[Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Supabase client"""
        try:
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL, supabase_key=settings.SUPABASE_KEY
            )
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            raise

    def get_client(self) -> Client:
        """Get Supabase client instance"""
        if self._client is None:
            self._initialize_client()
        if self._client is None:
            raise RuntimeError("Failed to initialize Supabase client")
        return self._client

    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try to access the client
            if self._client is None:
                return False
            self._client.table("test").select("*").limit(1).execute()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Create global Supabase client instance
supabase_db = SupabaseClient()


# Database helper functions
def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return supabase_db.get_client()


def test_database_connection() -> bool:
    """Test database connection"""
    return supabase_db.test_connection()
