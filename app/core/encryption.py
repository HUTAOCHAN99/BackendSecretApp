import base64
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

def generate_encryption_key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

def encrypt_message(message: str, key: str) -> tuple:
    try:
        key_bytes = base64.b64decode(key)
        iv = secrets.token_bytes(16)
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode('utf-8')) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(encrypted).decode('utf-8'), base64.b64encode(iv).decode('utf-8')
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")

def decrypt_message(encrypted_message: str, iv: str, key: str) -> str:
    try:
        key_bytes = base64.b64decode(key)
        encrypted_bytes = base64.b64decode(encrypted_message)
        iv_bytes = base64.b64decode(iv)
        
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
        
        return decrypted.decode('utf-8')
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")

def generate_chat_key(user_pin1: str, user_pin2: str) -> str:
    combined = f"{user_pin1}{user_pin2}"
    return base64.b64encode(hashlib.sha256(combined.encode()).digest()).decode('utf-8')