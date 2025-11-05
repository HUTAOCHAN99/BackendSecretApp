import secrets
import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging

from app.database.supabase_client import supabase
from app.core.security import create_jwt_token
from app.models.user_models import UserRegister, UserLogin, VerifyCode, TokenResponse, RegisterResponse
from app.services.email_service import email_service

# Setup logging
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
        """Generate 6-character alphanumeric PIN"""
        import string
        import random
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(6))
    
    async def register_user(self, user_data: UserRegister) -> RegisterResponse:
        logger.info(f"🔐 Attempting registration for: {user_data.email}")
        
        try:
            # Check if user already exists
            logger.info("Checking if user already exists...")
            existing_user = supabase.table("users").select("email").eq("email", user_data.email).execute()
            
            if existing_user.data:
                logger.warning(f"Email already registered: {user_data.email}")
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Generate unique PIN
            user_pin = self.generate_user_pin()
            logger.info(f"Generated user PIN: {user_pin}")
            
            # Hash password
            hashed_password = self.hash_password(user_data.password)
            
            # Create user
            user = {
                "email": user_data.email,
                "password": hashed_password,
                "user_pin": user_pin,
                "display_name": user_data.display_name,
                "is_verified": False
            }
            
            logger.info("Inserting user into database...")
            result = supabase.table("users").insert(user).execute()
            
            if not result.data:
                logger.error("Failed to create user - no data returned")
                raise HTTPException(status_code=500, detail="Failed to create user")
            
            user_id = result.data[0]["id"]
            logger.info(f"User created successfully with ID: {user_id}")
            
            # Generate verification code
            verification_code = self.generate_verification_code()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            logger.info("Creating verification code...")
            # Insert verification code
            code_result = supabase.table("verification_codes").insert({
                "user_id": user_id,
                "code": verification_code,
                "expires_at": expires_at.isoformat(),
                "used": False
            }).execute()
            
            if not code_result.data:
                logger.error("Failed to create verification code")
                # Clean up user if verification code creation fails
                supabase.table("users").delete().eq("id", user_id).execute()
                raise HTTPException(status_code=500, detail="Failed to create verification code")
            
            logger.info("Verification code created successfully")
            
            # Send verification email
            logger.info("Sending verification email...")
            email_sent = await email_service.send_verification_email(
                recipient_email=user_data.email,
                verification_code=verification_code,
                user_pin=user_pin
            )
            
            if not email_sent:
                logger.warning("Email sending failed, but registration completed")
            
            logger.info("🎉 Registration completed successfully")
            
            return RegisterResponse(
                message="Registration successful. Please check your email for verification code.",
                user_pin=user_pin,
                email=user_data.email,
                verification_code=verification_code  # For development only
            )
            
        except HTTPException:
            logger.error("HTTPException during registration")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def verify_user(self, verify_data: VerifyCode) -> TokenResponse:
        logger.info(f"🔍 Verifying user: {verify_data.email}")
        
        try:
            # Find user
            user_result = supabase.table("users").select("*").eq("email", verify_data.email).execute()
            if not user_result.data:
                logger.warning(f"User not found: {verify_data.email}")
                raise HTTPException(status_code=404, detail="User not found")
            
            user = user_result.data[0]
            user_id = user["id"]
            logger.info(f"User found: {user_id}")
            
            # Check verification code
            code_result = supabase.table("verification_codes").select("*").eq("user_id", user_id).eq("code", verify_data.code).eq("used", False).execute()
            
            if not code_result.data:
                logger.warning(f"Invalid verification code for user: {user_id}")
                raise HTTPException(status_code=400, detail="Invalid verification code")
            
            code_data = code_result.data[0]
            expires_at = datetime.fromisoformat(code_data["expires_at"].replace('Z', '+00:00'))
            
            if datetime.utcnow() > expires_at:
                logger.warning(f"Verification code expired for user: {user_id}")
                raise HTTPException(status_code=400, detail="Verification code expired")
            
            # Mark code as used and verify user
            logger.info("Marking verification code as used...")
            supabase.table("verification_codes").update({"used": True}).eq("id", code_data["id"]).execute()
            
            logger.info("Updating user verification status...")
            supabase.table("users").update({"is_verified": True}).eq("id", user_id).execute()
            
            # Create JWT token
            token = create_jwt_token(user_id)
            logger.info("JWT token created successfully")
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user_id=user_id,
                email=user["email"],
                display_name=user["display_name"],
                user_pin=user["user_pin"]
            )
            
        except HTTPException:
            logger.error("HTTPException during verification")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during verification: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        logger.info(f"🔑 Attempting login for: {login_data.email}")
        
        try:
            user_result = supabase.table("users").select("*").eq("email", login_data.email).execute()
            
            if not user_result.data:
                logger.warning(f"User not found: {login_data.email}")
                raise HTTPException(status_code=404, detail="User not found")
            
            user = user_result.data[0]
            logger.info(f"User found: {user['id']}")
            
            # Verify password
            hashed_input_password = self.hash_password(login_data.password)
            if user["password"] != hashed_input_password:
                logger.warning(f"Invalid password for user: {user['id']}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if verified
            if not user["is_verified"]:
                logger.warning(f"User not verified: {user['id']}")
                raise HTTPException(status_code=400, detail="Please verify your email first")
            
            # Create JWT token
            token = create_jwt_token(user["id"])
            logger.info("Login successful, JWT token created")
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user_id=user["id"],
                email=user["email"],
                display_name=user["display_name"],
                user_pin=user["user_pin"]
            )
            
        except HTTPException:
            logger.error("HTTPException during login")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")