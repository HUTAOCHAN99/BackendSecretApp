from fastapi import APIRouter

from app.services.auth_service import AuthService
from app.models.user_models import UserRegister, UserLogin, VerifyCode, TokenResponse, RegisterResponse

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=RegisterResponse)
async def register(user_data: UserRegister):
    return await auth_service.register_user(user_data)

@router.post("/verify", response_model=TokenResponse)
async def verify(verify_data: VerifyCode):
    return await auth_service.verify_user(verify_data)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    return await auth_service.login_user(login_data)