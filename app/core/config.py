import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS Origins - allow all for mobile apps
    ALLOWED_ORIGINS: list = ["*"]
    
    # Database Configuration - SQLite untuk offline
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./secret_chat.db")

settings = Settings()