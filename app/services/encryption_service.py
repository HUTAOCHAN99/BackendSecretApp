# python_backend/app/services/encryption_service.py
from app.core.encryption import encrypt_message, decrypt_message

class EncryptionService:
    
    def encrypt_message(self, message: str, key: str):
        """Encrypt message using AES-256-CBC"""
        try:
            encrypted_message, iv = encrypt_message(message, key)
            return encrypted_message, iv
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt_message(self, encrypted_message: str, iv: str, key: str):
        """Decrypt message using AES-256-CBC"""
        try:
            decrypted_content = decrypt_message(encrypted_message, iv, key)
            return decrypted_content
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")