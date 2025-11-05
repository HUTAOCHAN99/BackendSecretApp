import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging

from app.database.supabase_client import supabase
from app.core.security import create_jwt_token
from app.models.user_models import UserRegister, UserLogin, VerifyCode, TokenResponse, RegisterResponse

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate 6-digit verification code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    def generate_user_pin() -> str:
        """Generate 6-character alphanumeric PIN"""
        import string
        import random
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(6))
    
    async def register_user(self, user_data: UserRegister) -> RegisterResponse:
        logger.info(f"🔐 Attempting registration for: {user_data.email}")
        
        try:
            # Check if user already exists
            response = supabase.table("users")\
                .select("id, email")\
                .eq("email", user_data.email)\
                .execute()
            
            if response.data and len(response.data) > 0:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Generate unique user data
            user_id = str(uuid.uuid4())
            user_pin = self.generate_user_pin()
            hashed_password = self.hash_password(user_data.password)
            verification_code = self.generate_verification_code()
            
            # Create user record
            user_record = {
                'id': user_id,
                'email': user_data.email,
                'password': hashed_password,
                'display_name': user_data.display_name,
                'user_pin': user_pin,
                'is_verified': False
            }
            
            # Insert user into database
            result = supabase.table("users").insert(user_record).execute()
            
            if hasattr(result, 'error') and result.error:
                raise HTTPException(status_code=500, detail=f"Database error: {result.error}")
            
            # Create verification code record
            code_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            verification_record = {
                'id': code_id,
                'user_id': user_id,
                'code': verification_code,
                'expires_at': expires_at.isoformat(),
                'used': False
            }
            
            # For now, we'll skip storing verification codes in database
            # In production, you'd store this in a verification_codes table
            
            logger.info(f"✅ User registered successfully: {user_data.email}")
            logger.info(f"📌 Generated PIN: {user_pin}")
            logger.info(f"📧 Verification code: {verification_code} (for development)")
            
            return RegisterResponse(
                message="Registration successful. Please verify your email.",
                user_pin=user_pin,
                email=user_data.email,
                verification_code=verification_code  # Include for development
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def verify_user(self, verify_data: VerifyCode) -> TokenResponse:
        """Verify user email with code"""
        try:
            # Find user by email
            response = supabase.table("users")\
                .select("id, email, display_name, user_pin, is_verified")\
                .eq("email", verify_data.email)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            user = response.data[0]
            
            # In production, you would verify against stored verification code
            # For now, we'll auto-verify any 6-digit code for development
            if len(verify_data.code) != 6 or not verify_data.code.isdigit():
                raise HTTPException(status_code=400, detail="Invalid verification code format")
            
            # Mark user as verified
            update_response = supabase.table("users")\
                .update({"is_verified": True})\
                .eq("id", user['id'])\
                .execute()
            
            if hasattr(update_response, 'error') and update_response.error:
                raise HTTPException(status_code=500, detail=f"Verification update failed: {update_response.error}")
            
            # Create JWT token
            token = create_jwt_token(user['id'])
            
            logger.info(f"✅ User verified successfully: {verify_data.email}")
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user_id=user['id'],
                email=user['email'],
                display_name=user['display_name'],
                user_pin=user['user_pin']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        """Login user with email and password"""
        try:
            # Find user by email
            response = supabase.table("users")\
                .select("id, email, password, display_name, user_pin, is_verified")\
                .eq("email", login_data.email)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            user = response.data[0]
            
            # Verify password
            hashed_input_password = self.hash_password(login_data.password)
            if user['password'] != hashed_input_password:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if user is verified
            if not user.get('is_verified', False):
                raise HTTPException(status_code=400, detail="Please verify your email first")
            
            # Create JWT token
            token = create_jwt_token(user['id'])
            
            logger.info(f"✅ User logged in successfully: {login_data.email}")
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user_id=user['id'],
                email=user['email'],
                display_name=user['display_name'],
                user_pin=user['user_pin']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    async def get_user_profile(self, user_id: str) -> dict:
        """Get user profile by ID"""
        try:
            response = supabase.table("users")\
                .select("id, email, display_name, user_pin, is_verified, created_at")\
                .eq("id", user_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")
    
    async def search_user_by_pin(self, pin: str) -> dict:
        """Search user by PIN (for starting chats)"""
        try:
            response = supabase.table("users")\
                .select("id, display_name, user_pin, email")\
                .eq("user_pin", pin)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            user = response.data[0]
            return {
                "id": user['id'],
                "display_name": user['display_name'],
                "user_pin": user['user_pin']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"User search failed: {str(e)}")