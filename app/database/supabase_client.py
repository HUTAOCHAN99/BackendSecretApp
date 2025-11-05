from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Create and return Supabase client
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase URL and Key must be set in environment variables")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Global supabase client instance
supabase: Client = get_supabase_client()
