from fastapi import APIRouter, Depends, HTTPException
from app.services.chat_service import ChatService
from app.core.security import verify_jwt_token
from app.models.chat_models import SearchUserRequest, UserSearchResponse, ChatCreate

router = APIRouter()
chat_service = ChatService()

def get_current_user(token: str = Depends(verify_jwt_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return token

@router.post("/search", response_model=UserSearchResponse)
async def search_user(
    search_data: SearchUserRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Search for user by PIN
    """
    try:
        return await chat_service.search_user_by_pin(search_data.pin)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/start", response_model=dict)
async def start_chat(
    chat_data: ChatCreate, 
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new chat or return existing chat
    """
    try:
        # Verify current user is one of the participants
        if current_user["user_id"] not in [chat_data.user1_id, chat_data.user2_id]:
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to start this chat"
            )
        
        return await chat_service.start_chat(chat_data.user1_id, chat_data.user2_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")

@router.get("/my-chats", response_model=list)
async def get_my_chats(current_user: dict = Depends(get_current_user)):
    """
    Get all chats for the current user
    """
    try:
        return await chat_service.get_user_chats(current_user["user_id"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chats: {str(e)}")

@router.get("/health")
async def chat_health_check():
    """
    Health check for chats endpoint
    """
    return {"status": "healthy", "service": "chats"}