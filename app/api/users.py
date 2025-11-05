from fastapi import APIRouter, Depends, HTTPException
# GUNAKAN ABSOLUTE IMPORTS
from app.services.chat_service import ChatService
from app.models.chat_models import SearchUserRequest, UserSearchResponse
from app.core.security import verify_jwt_token

router = APIRouter()
chat_service = ChatService()

def get_current_user(token: str = Depends(verify_jwt_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return token

@router.post("/search", response_model=UserSearchResponse)
async def search_user(search_data: SearchUserRequest, current_user: dict = Depends(get_current_user)):
    return await chat_service.search_user_by_pin(search_data.pin)