from fastapi import HTTPException
from app.database.supabase_client import supabase
from app.core.encryption import generate_chat_key

class ChatService:
    
    async def search_user_by_pin(self, pin: str):
        """Search user by PIN"""
        result = supabase.table("users").select("id, display_name, user_pin, email").eq("user_pin", pin).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = result.data[0]
        return {
            "id": user["id"],
            "display_name": user["display_name"],
            "user_pin": user["user_pin"]
        }
    
    async def start_chat(self, user1_id: str, user2_id: str):
        """Start a new chat or return existing one"""
        if user1_id == user2_id:
            raise HTTPException(status_code=400, detail="Cannot start chat with yourself")
        
        # Check if chat already exists (in any direction)
        existing_chat = supabase.table("chats")\
            .select("*")\
            .or_(f"and(user1_id.eq.{user1_id},user2_id.eq.{user2_id}),and(user1_id.eq.{user2_id},user2_id.eq.{user1_id})")\
            .execute()
        
        if existing_chat.data:
            return {
                "chat_id": existing_chat.data[0]["id"], 
                "is_new": False,
                "message": "Chat already exists"
            }
        
        # Create new chat
        chat_data = {
            "user1_id": user1_id,
            "user2_id": user2_id
        }
        
        result = supabase.table("chats").insert(chat_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create chat")
        
        return {
            "chat_id": result.data[0]["id"], 
            "is_new": True,
            "message": "New chat created"
        }
    
    async def get_user_chats(self, user_id: str):
        """Get all chats for a user"""
        try:
            # Get chats where user is either user1 or user2
            chats_result = supabase.table("chats")\
                .select("*, user1:users!chats_user1_id_fkey(display_name, user_pin), user2:users!chats_user2_id_fkey(display_name, user_pin)")\
                .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
                .execute()
            
            if not chats_result.data:
                return []
            
            formatted_chats = []
            for chat in chats_result.data:
                try:
                    # Determine which user is the other participant
                    if chat["user1_id"] == user_id:
                        other_user = chat["user2"]
                        other_user_id = chat["user2_id"]
                    else:
                        other_user = chat["user1"]
                        other_user_id = chat["user1_id"]
                    
                    formatted_chats.append({
                        "chat_id": chat["id"],
                        "other_user_id": other_user_id,
                        "other_user_name": other_user["display_name"] if other_user else "Unknown User",
                        "other_user_pin": other_user["user_pin"] if other_user else "Unknown",
                        "created_at": chat["created_at"]
                    })
                except Exception as e:
                    print(f"Error formatting chat {chat['id']}: {e}")
                    continue
            
            return formatted_chats
            
        except Exception as e:
            print(f"Error getting user chats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get user chats: {str(e)}")
    
    def generate_chat_key(self, user_pin1: str, user_pin2: str) -> str:
        """Generate encryption key for chat"""
        return generate_chat_key(user_pin1, user_pin2)