from pydantic import BaseModel
from datetime import datetime

class MessageSend(BaseModel):
    chat_id: str
    sender_id: str
    message: str
    encryption_key: str

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    message: str
    created_at: datetime