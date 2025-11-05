from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserLogin(BaseModel):
    email: EmailStr  
    password: str

class VerifyCode(BaseModel):
    email: EmailStr
    code: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    user_pin: str
    is_verified: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    display_name: str
    user_pin: str

class RegisterResponse(BaseModel):
    message: str
    user_pin: str
    email: str
    verification_code: Optional[str] = None  