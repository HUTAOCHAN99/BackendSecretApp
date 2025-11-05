# python_backend/app/api/messages.py
from fastapi import APIRouter, HTTPException
from app.services.encryption_service import EncryptionService

router = APIRouter()
encryption_service = EncryptionService()

@router.post("/encrypt")
async def encrypt_message(data: dict):
    """
    Encrypt a message
    """
    try:
        message = data.get("message")
        encryption_key = data.get("encryption_key")
        
        if not message or not encryption_key:
            raise HTTPException(status_code=400, detail="Message and encryption_key are required")
        
        encrypted_message, iv = encryption_service.encrypt_message(message, encryption_key)
        
        return {
            "encrypted_message": encrypted_message,
            "iv": iv,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

@router.post("/decrypt")
async def decrypt_message(data: dict):
    """
    Decrypt a message
    """
    try:
        encrypted_message = data.get("encrypted_message")
        iv = data.get("iv")
        encryption_key = data.get("encryption_key")
        
        if not encrypted_message or not iv or not encryption_key:
            raise HTTPException(status_code=400, detail="encrypted_message, iv, and encryption_key are required")
        
        decrypted_message = encryption_service.decrypt_message(encrypted_message, iv, encryption_key)
        
        return {
            "decrypted_message": decrypted_message,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")

@router.get("/health")
async def messages_health_check():
    return {"status": "healthy", "service": "encryption-service"}