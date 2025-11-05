from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ChatCreate(BaseModel):
    user1_id: str
    user2_id: str

class ChatResponse(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class SearchUserRequest(BaseModel):
    pin: str

class UserSearchResponse(BaseModel):
    id: str
    display_name: str
    user_pin: str

    class Config:
        from_attributes = True

class UserChatResponse(BaseModel):
    chat_id: str
    other_user_id: str
    other_user_name: str
    other_user_pin: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatStartResponse(BaseModel):
    chat_id: str
    is_new: bool
    message: str

    class Config:
        from_attributes = True

class ChatListResponse(BaseModel):
    chats: List[UserChatResponse]

    class Config:
        from_attributes = True