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
        """Register new user"""
        logger.info(f"🔐 Attempting registration for: {user_data.email}")
        
        try:
            async with db.get_connection() as conn:
                # Check if user already exists
                existing_user = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1", 
                    user_data.email
                )
                
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already registered")
                
                # Generate unique user data
                user_pin = self.generate_user_pin()
                hashed_password = self.hash_password(user_data.password)
                verification_code = self.generate_verification_code()
                
                # Create user
                user_id = await conn.fetchval('''
                    INSERT INTO users (email, password, display_name, user_pin, is_verified)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                ''', user_data.email, hashed_password, user_data.display_name, user_pin, False)
                
                # Create verification code
                expires_at = datetime.utcnow() + timedelta(hours=24)
                await conn.execute('''
                    INSERT INTO verification_codes (user_id, code, expires_at, used)
                    VALUES ($1, $2, $3, $4)
                ''', user_id, verification_code, expires_at, False)
                
            logger.info(f"✅ User registered successfully: {user_data.email}")
            logger.info(f"📌 Generated PIN: {user_pin}")
            logger.info(f"📧 Verification code: {verification_code} (for development)")
            
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
        """Verify user email with code"""
        try:
            async with db.get_connection() as conn:
                # Find user and verification code
                result = await conn.fetchrow('''
                    SELECT u.id, u.email, u.display_name, u.user_pin, vc.code, vc.expires_at, vc.used
                    FROM users u
                    JOIN verification_codes vc ON u.id = vc.user_id
                    WHERE u.email = $1 AND vc.code = $2 AND vc.used = FALSE
                    ORDER BY vc.created_at DESC
                    LIMIT 1
                ''', verify_data.email, verify_data.code)
                
                if not result:
                    raise HTTPException(status_code=400, detail="Invalid verification code")
                
                # Check if code expired
                if datetime.utcnow() > result['expires_at']:
                    raise HTTPException(status_code=400, detail="Verification code expired")
                
                # Mark code as used and verify user
                await conn.execute(
                    "UPDATE verification_codes SET used = TRUE WHERE code = $1 AND user_id = $2",
                    verify_data.code, result['id']
                )
                await conn.execute(
                    "UPDATE users SET is_verified = TRUE, updated_at = NOW() WHERE id = $1",
                    result['id']
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
        """Login user with email and password"""
        try:
            async with db.get_connection() as conn:
                # Find user by email
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1", 
                    login_data.email
                )
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Verify password
                hashed_input_password = self.hash_password(login_data.password)
                if user['password'] != hashed_input_password:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                # Check if user is verified
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
    
    async def get_user_profile(self, user_id: str) -> dict:
        """Get user profile by ID"""
        try:
            async with db.get_connection() as conn:
                user = await conn.fetchrow(
                    "SELECT id, email, display_name, user_pin, is_verified, created_at FROM users WHERE id = $1",
                    uuid.UUID(user_id)
                )
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {
                    "id": str(user['id']),
                    "email": user['email'],
                    "display_name": user['display_name'],
                    "user_pin": user['user_pin'],
                    "is_verified": user['is_verified'],
                    "created_at": user['created_at']
                }
                
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")
    
    async def search_user_by_pin(self, pin: str) -> dict:
        """Search user by PIN (for starting chats)"""
        try:
            async with db.get_connection() as conn:
                user = await conn.fetchrow(
                    "SELECT id, display_name, user_pin FROM users WHERE user_pin = $1",
                    pin
                )
                
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
    
    async def update_user_profile(self, user_id: str, display_name: str) -> dict:
        """Update user profile"""
        try:
            async with db.get_connection() as conn:
                await conn.execute(
                    "UPDATE users SET display_name = $1, updated_at = NOW() WHERE id = $2",
                    display_name, uuid.UUID(user_id)
                )
                
                # Get updated user
                user = await conn.fetchrow(
                    "SELECT id, email, display_name, user_pin, is_verified FROM users WHERE id = $1",
                    uuid.UUID(user_id)
                )
                
                return {
                    "id": str(user['id']),
                    "email": user['email'],
                    "display_name": user['display_name'],
                    "user_pin": user['user_pin'],
                    "is_verified": user['is_verified']
                }
                
        except Exception as e:
            logger.error(f"Failed to update user profile: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> dict:
        """Change user password"""
        try:
            async with db.get_connection() as conn:
                # Get current user data
                user = await conn.fetchrow(
                    "SELECT password FROM users WHERE id = $1",
                    uuid.UUID(user_id)
                )
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Verify current password
                hashed_current_password = self.hash_password(current_password)
                if user['password'] != hashed_current_password:
                    raise HTTPException(status_code=401, detail="Current password is incorrect")
                
                # Update password
                hashed_new_password = self.hash_password(new_password)
                await conn.execute(
                    "UPDATE users SET password = $1, updated_at = NOW() WHERE id = $2",
                    hashed_new_password, uuid.UUID(user_id)
                )
                
                logger.info(f"✅ Password changed successfully for user: {user_id}")
                
                return {"message": "Password changed successfully"}
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to change password: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")
    
    async def reset_password_request(self, email: str) -> dict:
        """Request password reset (send reset code)"""
        try:
            async with db.get_connection() as conn:
                user = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1",
                    email
                )
                
                if not user:
                    # Don't reveal if email exists or not
                    return {"message": "If the email exists, a reset code has been sent"}
                
                # Generate reset code
                reset_code = self.generate_verification_code()
                expires_at = datetime.utcnow() + timedelta(hours=1)
                
                # Store reset code (you might want a separate reset_codes table)
                await conn.execute('''
                    INSERT INTO verification_codes (user_id, code, expires_at, used)
                    VALUES ($1, $2, $3, $4)
                ''', user['id'], reset_code, expires_at, False)
                
                logger.info(f"📧 Password reset code for {email}: {reset_code}")
                
                return {
                    "message": "If the email exists, a reset code has been sent",
                    "reset_code": reset_code  # For development only
                }
                
        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Password reset request failed: {str(e)}")
    
    async def reset_password_confirm(self, email: str, reset_code: str, new_password: str) -> dict:
        """Confirm password reset with code"""
        try:
            async with db.get_connection() as conn:
                # Find valid reset code
                result = await conn.fetchrow('''
                    SELECT u.id, vc.code, vc.expires_at, vc.used
                    FROM users u
                    JOIN verification_codes vc ON u.id = vc.user_id
                    WHERE u.email = $1 AND vc.code = $2 AND vc.used = FALSE
                    ORDER BY vc.created_at DESC
                    LIMIT 1
                ''', email, reset_code)
                
                if not result:
                    raise HTTPException(status_code=400, detail="Invalid reset code")
                
                if datetime.utcnow() > result['expires_at']:
                    raise HTTPException(status_code=400, detail="Reset code expired")
                
                # Mark code as used and update password
                hashed_new_password = self.hash_password(new_password)
                await conn.execute(
                    "UPDATE verification_codes SET used = TRUE WHERE code = $1",
                    reset_code
                )
                await conn.execute(
                    "UPDATE users SET password = $1, updated_at = NOW() WHERE id = $2",
                    hashed_new_password, result['id']
                )
                
                logger.info(f"✅ Password reset successfully for: {email}")
                
                return {"message": "Password reset successfully"}
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset confirmation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Password reset confirmation failed: {str(e)}")

# Global instance
auth_service = AuthService()