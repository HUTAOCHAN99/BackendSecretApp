import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database Configuration - Default to SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///secret_chat.db")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS Origins
    ALLOWED_ORIGINS: list = ["*"]
    
    # App Configuration
    APP_VERSION: str = "1.0.0"

settings = Settings()