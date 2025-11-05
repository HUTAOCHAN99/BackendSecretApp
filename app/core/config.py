import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database Configuration - Railway akan provide DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/secret_chat")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS Origins
    ALLOWED_ORIGINS: list = ["*"]
    
    # App Configuration
    APP_VERSION: str = "1.0.0"

settings = Settings()