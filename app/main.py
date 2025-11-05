from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Secret Chat API",
    description="Backend API untuk aplikasi chat rahasia",
    version=settings.APP_VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {
        "message": "Secret Chat API is running!", 
        "version": settings.APP_VERSION,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "secret-chat-api"}

@app.get("/info")
async def info():
    return {
        "name": "Secret Chat API",
        "version": settings.APP_VERSION,
        "database": "Supabase"
    }