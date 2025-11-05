import os

def create_missing_files():
    base_dir = os.path.dirname(__file__)
    
    # Files to create if missing
    files_to_create = {
        'app/database/__init__.py': '# Database package\n',
        'app/database/supabase_client.py': '''from supabase import create_client, Client
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
''',
    }
    
    for file_path, content in files_to_create.items():
        full_path = os.path.join(base_dir, file_path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        if not os.path.exists(full_path):
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created: {file_path}")
        else:
            print(f"✅ Already exists: {file_path}")

if __name__ == "__main__":
    create_missing_files()
    print("\n🎉 Missing files created! Now run: python run_server.py")