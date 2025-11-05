#!/usr/bin/env python3
"""
Production entry point for Railway
"""
import os
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Secret Chat Backend...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Remove Supabase test - just start the server
    print("✅ Starting server...")
    
    port = int(os.environ.get("PORT", 8000))
    
    # For Railway deployment
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )