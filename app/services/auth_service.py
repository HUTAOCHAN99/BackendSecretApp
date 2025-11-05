import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging

from app.database.database import db
from app.core.security import create_jwt_token
from app.models.user_models import UserRegister, UserLogin, VerifyCode, TokenResponse, RegisterResponse

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_verification_code() -> str:
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    def generate_user_pin() -> str:
        import string
        import random
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(6))
    
    async def register_user(self, user_data: UserRegister) -> RegisterResponse:
        logger.info(f"🔐 Attempting registration for: {user_data.email}")
        
        try:
            with db.get_cursor() as cursor:
                # Check if user already exists
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s", 
                    (user_data.email,)
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Email already registered")
                
                # Generate unique user data
                user_pin = self.generate_user_pin()
                hashed_password = self.hash_password(user_data.password)
                verification_code = self.generate_verification_code()
                
                # Create user
                cursor.execute('''
                    INSERT INTO users (email, password, display_name, user_pin, is_verified)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                ''', (user_data.email, hashed_password, user_data.display_name, user_pin, False))
                
                user_result = cursor.fetchone()
                user_id = user_result['id']
                
                # Create verification code
                expires_at = datetime.utcnow() + timedelta(hours=24)
                cursor.execute('''
                    INSERT INTO verification_codes (user_id, code, expires_at, used)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, verification_code, expires_at, False))
                
            logger.info(f"✅ User registered successfully: {user_data.email}")
            logger.info(f"📌 Generated PIN: {user_pin}")
            logger.info(f"📧 Verification code: {verification_code}")
            
            return RegisterResponse(
                message="Registration successful. Please verify your email.",
                user_pin=user_pin,
                email=user_data.email,
                verification_code=verification_code  # For development
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def verify_user(self, verify_data: VerifyCode) -> TokenResponse:
        try:
            with db.get_cursor() as cursor:
                # Find user and verification code
                cursor.execute('''
                    SELECT u.id, u.email, u.display_name, u.user_pin, vc.code, vc.expires_at, vc.used
                    FROM users u
                    JOIN verification_codes vc ON u.id = vc.user_id
                    WHERE u.email = %s AND vc.code = %s AND vc.used = FALSE
                    ORDER BY vc.created_at DESC
                    LIMIT 1
                ''', (verify_data.email, verify_data.code))
                
                result = cursor.fetchone()
                
                if not result:
                    raise HTTPException(status_code=400, detail="Invalid verification code")
                
                if datetime.utcnow() > result['expires_at']:
                    raise HTTPException(status_code=400, detail="Verification code expired")
                
                # Mark code as used and verify user
                cursor.execute(
                    "UPDATE verification_codes SET used = TRUE WHERE code = %s AND user_id = %s",
                    (verify_data.code, result['id'])
                )
                cursor.execute(
                    "UPDATE users SET is_verified = TRUE, updated_at = NOW() WHERE id = %s",
                    (result['id'],)
                )
                
                # Create JWT token
                token = create_jwt_token(str(result['id']))
                
                logger.info(f"✅ User verified successfully: {verify_data.email}")
                
                return TokenResponse(
                    access_token=token,
                    token_type="bearer",
                    user_id=str(result['id']),
                    email=result['email'],
                    display_name=result['display_name'],
                    user_pin=result['user_pin']
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE email = %s", 
                    (login_data.email,)
                )
                user = cursor.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Verify password
                hashed_input_password = self.hash_password(login_data.password)
                if user['password'] != hashed_input_password:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                if not user['is_verified']:
                    raise HTTPException(status_code=400, detail="Please verify your email first")
                
                # Create JWT token
                token = create_jwt_token(str(user['id']))
                
                logger.info(f"✅ User logged in successfully: {login_data.email}")
                
                return TokenResponse(
                    access_token=token,
                    token_type="bearer",
                    user_id=str(user['id']),
                    email=user['email'],
                    display_name=user['display_name'],
                    user_pin=user['user_pin']
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    async def search_user_by_pin(self, pin: str) -> dict:
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, display_name, user_pin FROM users WHERE user_pin = %s",
                    (pin,)
                )
                user = cursor.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {
                    "id": str(user['id']),
                    "display_name": user['display_name'],
                    "user_pin": user['user_pin']
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"User search failed: {str(e)}")