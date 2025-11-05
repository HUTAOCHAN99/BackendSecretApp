# python_backend/app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Railway Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    RAILWAY_ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT", "development")
    RAILWAY_SERVICE_NAME: str = os.getenv("RAILWAY_SERVICE_NAME", "secret-chat-backend")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///secret_chat.db")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production-for-railway")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS Origins - Allow all for mobile apps and web
    ALLOWED_ORIGINS: list = [
        "*",  # Allow all origins for mobile apps
        "http://localhost:3000",
        "http://localhost:8080",
        "https://your-app-name.up.railway.app",
    ]
    
    # App Configuration
    APP_VERSION: str = "1.0.0"
    APP_NAME: str = "Secret Chat Backend"
    
    # Security Configuration
    SECURE_COOKIES: bool = os.getenv("RAILWAY_ENVIRONMENT") == "production"
    DEBUG: bool = os.getenv("RAILWAY_ENVIRONMENT") != "production"
    
    # Email Configuration (Optional)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Encryption Configuration
    ENCRYPTION_KEY_LENGTH: int = 32  # AES-256
    
    @property
    def is_production(self):
        return self.RAILWAY_ENVIRONMENT == "production"
    
    @property
    def is_development(self):
        return self.RAILWAY_ENVIRONMENT == "development"
    
    @property
    def database_type(self):
        if 'postgres' in self.DATABASE_URL:
            return 'postgresql'
        else:
            return 'sqlite'

settings = Settings()

# Configuration for different environments
class DevelopmentConfig(Settings):
    DEBUG: bool = True
    ALLOWED_ORIGINS: list = ["*"]
    
class ProductionConfig(Settings):
    DEBUG: bool = False
    SECURE_COOKIES: bool = True
    
def get_settings():
    environment = os.getenv("RAILWAY_ENVIRONMENT", "development")
    if environment == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()

# Global settings instance
current_settings = get_settings()