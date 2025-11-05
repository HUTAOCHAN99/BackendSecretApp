#!/usr/bin/env python3
"""
Production entry point for Railway
"""
import os
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Secret Chat Backend...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        # Test database connection (SQLite)
        from app.database.supabase_client import db
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    port = int(os.environ.get("PORT", 8000))
    
    # For Railway deployment
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )