# python_backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Secret Chat Encryption API",
    description="Backend API khusus untuk enkripsi pesan",
    version="1.0.0"
)

# CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include hanya messages router
from app.api.messages import router as messages_router
app.include_router(messages_router, prefix="/api/messages", tags=["Messages"])

@app.get("/")
async def root():
    return {
        "message": "Secret Chat Encryption API is running!", 
        "version": "1.0.0",
        "service": "encryption-only"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "encryption-api"}

@app.get("/info")
async def info():
    return {
        "name": "Secret Chat Encryption API",
        "version": "1.0.0", 
        "service": "message-encryption",
        "encryption": "AES-256-CBC"
    }