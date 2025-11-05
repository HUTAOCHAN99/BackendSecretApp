# python_backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from app.core.config import settings

# Import database untuk initialization
from app.database.database import db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secret Chat API",
    description="Backend API untuk aplikasi chat rahasia",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("🚀 Starting application initialization...")
    
    try:
        await db.init_db()
        logger.info("✅ Database initialization completed")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization completed with warnings: {e}")
    
    # Test database connection
    try:
        is_healthy = await db.health_check()
        if is_healthy:
            logger.info("✅ Database health check passed")
        else:
            logger.warning("⚠️ Database health check failed")
    except Exception as e:
        logger.warning(f"⚠️ Database health check error: {e}")
    
    logger.info("🎉 Application startup completed")

# Close database on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        await db.close()
        logger.info("✅ Application shutdown completed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Include routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.chats import router as chats_router
from app.api.messages import router as messages_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(chats_router, prefix="/api/chats", tags=["Chats"])
app.include_router(messages_router, prefix="/api/messages", tags=["Messages"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Secret Chat API is running!", 
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
        "environment": "production" if os.environ.get('RAILWAY_ENVIRONMENT') else "development"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_health = False
    try:
        db_health = await db.health_check()
    except Exception as e:
        logger.error(f"Health check error: {e}")
    
    return {
        "status": "healthy", 
        "service": "secret-chat-api",
        "database": "connected" if db_health else "disconnected",
        "environment": "railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "local"
    }

@app.get("/debug/database")
async def debug_database():
    """Debug endpoint for database information"""
    try:
        db_health = await db.health_check()
        db_type = getattr(db, 'db_type', 'unknown')
        db_url = getattr(db, 'db_url', 'unknown')
        
        # Safe URL for logging
        safe_url = db_url
        if db_url and '@' in db_url:
            safe_url = db_url.split('@')[0] + '@***'
        
        return {
            "database_type": db_type,
            "database_url": safe_url,
            "status": "connected" if db_health else "disconnected",
            "environment": "railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "local",
            "has_database_url": bool(os.environ.get('DATABASE_URL'))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "environment": "railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "local"
        }

@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint for environment variables"""
    env_vars = {
        "RAILWAY_ENVIRONMENT": os.environ.get('RAILWAY_ENVIRONMENT'),
        "RAILWAY_SERVICE_NAME": os.environ.get('RAILWAY_SERVICE_NAME'),
        "DATABASE_URL_exists": bool(os.environ.get('DATABASE_URL')),
        "PORT": os.environ.get('PORT'),
        "PYTHON_VERSION": os.environ.get('PYTHON_VERSION')
    }
    return env_vars

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": request.url.path
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Internal Server Error",
        "message": "An internal server error occurred",
        "path": request.url.path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )