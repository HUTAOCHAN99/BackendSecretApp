import os
import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseManager:
    _client = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = cls._create_client()
        return cls._client
    
    @classmethod
    def _create_client(cls) -> Client:
        try:
            if not settings.SUPABASE_URL:
                raise ValueError("SUPABASE_URL is not set")
            if not settings.SUPABASE_KEY:
                raise ValueError("SUPABASE_KEY is not set")
            
            # Create client with minimal configuration
            client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # Test connection
            try:
                result = client.table('users').select('count', count='exact').limit(1).execute()
                logger.info("✅ Supabase client created and connected successfully")
            except Exception as test_error:
                logger.warning(f"⚠️ Supabase client created but connection test failed: {test_error}")
            
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to create Supabase client: {e}")
            raise

# Global access function
def get_supabase_client() -> Client:
    return SupabaseManager.get_client()

# Initialize client
try:
    supabase = get_supabase_client()
    print("✅ Supabase client initialized successfully")
except Exception as e:
    print(f"❌ Supabase client initialization failed: {e}")
    # Create a mock client for development
    class MockSupabaseClient:
        def __getattr__(self, name):
            def mock_method(*args, **kwargs):
                print(f"⚠️ Mock Supabase called: {name} with args: {args}")
                return type('MockResponse', (), {'data': [], 'error': None})()
            return mock_method
    
    supabase = MockSupabaseClient()
    print("⚠️ Using mock Supabase client - some features may not work")