import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-fallback-secret-for-development")
    
    # CORS Origins
    ALLOWED_ORIGINS: list = ["*"]  # Will update for production
    
    # App Configuration
    APP_VERSION: str = "1.0.0"

settings = Settings()