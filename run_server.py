import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting Secret Chat Backend...")
print(f"📁 Working directory: {os.getcwd()}")

try:
    # Import semua module secara manual
    print("📦 Importing modules...")
    
    # Import core
    from app.core.config import settings
    print("✅ Config imported")
    
    from app.core.security import create_jwt_token, verify_jwt_token
    print("✅ Security imported")
    
    from app.core.encryption import encrypt_message, decrypt_message, generate_chat_key
    print("✅ Encryption imported")
    
    # Import database
    from app.database.supabase_client import supabase
    print("✅ Database imported")
    
    # Test database connection
    print("🔗 Testing database connection...")
    test_result = supabase.table("users").select("count", count="exact").execute()
    print(f"✅ Database connected! Found {len(test_result.data)} users")
    
    # Import services
    from app.services.auth_service import AuthService
    from app.services.chat_service import ChatService  
    from app.services.encryption_service import EncryptionService
    print("✅ Services imported")
    
    # Import API routes
    from app.api.auth import router as auth_router
    from app.api.users import router as users_router
    from app.api.chats import router as chats_router
    from app.api.messages import router as messages_router
    print("✅ API routes imported")
    
    # Create FastAPI app
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="Secret Chat API",
        description="Backend API untuk aplikasi chat rahasia", 
        version="1.0.0"
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
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(chats_router, prefix="/api/chats", tags=["Chats"])
    app.include_router(messages_router, prefix="/api/messages", tags=["Messages"])
    
    @app.get("/")
    async def root():
        return {"message": "Secret Chat API is running!", "version": "1.0.0"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "secret-chat-api"}
    
    print("🎉 App created successfully!")
    print("🌐 Server will start at http://0.0.0.0:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n🔧 Debug info:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    print("\n🔥 Starting server...")
    
    # FIX: Nonaktifkan reload untuk sekarang
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)