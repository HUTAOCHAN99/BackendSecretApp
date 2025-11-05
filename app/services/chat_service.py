# python_backend/app/services/chat_service.py
import uuid
from fastapi import HTTPException
import logging
from app.database.database import db
from app.core.encryption import generate_chat_key

logger = logging.getLogger(__name__)

class ChatService:
    
    async def search_user_by_pin(self, pin: str):
        """Search user by PIN"""
        try:
            async with db.get_connection() as conn:
                if hasattr(conn, 'fetchrow'):  # PostgreSQL
                    user = await conn.fetchrow(
                        "SELECT id, display_name, user_pin FROM users WHERE user_pin = $1",
                        pin
                    )
                else:  # SQLite
                    cursor = conn.execute(
                        "SELECT id, display_name, user_pin FROM users WHERE user_pin = ?",
                        (pin,)
                    )
                    user = cursor.fetchone()
                
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
    
    async def start_chat(self, user1_id: str, user2_id: str):
        """Start a new chat or return existing one"""
        if user1_id == user2_id:
            raise HTTPException(status_code=400, detail="Cannot start chat with yourself")
        
        try:
            async with db.get_connection() as conn:
                # Check if chat already exists
                if hasattr(conn, 'fetchrow'):  # PostgreSQL
                    existing_chat = await conn.fetchrow('''
                        SELECT id FROM chats 
                        WHERE (user1_id = $1 AND user2_id = $2) OR (user1_id = $3 AND user2_id = $4)
                    ''', user1_id, user2_id, user2_id, user1_id)
                else:  # SQLite
                    cursor = conn.execute('''
                        SELECT id FROM chats 
                        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
                    ''', (user1_id, user2_id, user2_id, user1_id))
                    existing_chat = cursor.fetchone()
                
                if existing_chat:
                    return {
                        "chat_id": str(existing_chat['id']),
                        "is_new": False,
                        "message": "Chat already exists"
                    }
                
                # Create new chat
                chat_id = str(uuid.uuid4())
                if hasattr(conn, 'execute'):  # PostgreSQL async
                    await conn.execute('''
                        INSERT INTO chats (id, user1_id, user2_id)
                        VALUES ($1, $2, $3)
                    ''', chat_id, user1_id, user2_id)
                else:  # SQLite sync
                    conn.execute('''
                        INSERT INTO chats (id, user1_id, user2_id)
                        VALUES (?, ?, ?)
                    ''', (chat_id, user1_id, user2_id))
                    conn.commit()
                
                return {
                    "chat_id": chat_id,
                    "is_new": True,
                    "message": "New chat created"
                }
                
        except Exception as e:
            logger.error(f"Failed to start chat: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")
    
    async def get_user_chats(self, user_id: str):
        """Get all chats for a user"""
        try:
            async with db.get_connection() as conn:
                if hasattr(conn, 'fetch'):  # PostgreSQL
                    chats = await conn.fetch('''
                        SELECT c.id as chat_id, c.created_at,
                               CASE 
                                   WHEN c.user1_id = $1 THEN u2.id
                                   ELSE u1.id
                               END as other_user_id,
                               CASE 
                                   WHEN c.user1_id = $1 THEN u2.display_name
                                   ELSE u1.display_name
                               END as other_user_name,
                               CASE 
                                   WHEN c.user1_id = $1 THEN u2.user_pin
                                   ELSE u1.user_pin
                               END as other_user_pin
                        FROM chats c
                        LEFT JOIN users u1 ON c.user1_id = u1.id
                        LEFT JOIN users u2 ON c.user2_id = u2.id
                        WHERE c.user1_id = $1 OR c.user2_id = $1
                        ORDER BY c.created_at DESC
                    ''', user_id)
                else:  # SQLite
                    cursor = conn.execute('''
                        SELECT c.id as chat_id, c.created_at,
                               CASE 
                                   WHEN c.user1_id = ? THEN u2.id
                                   ELSE u1.id
                               END as other_user_id,
                               CASE 
                                   WHEN c.user1_id = ? THEN u2.display_name
                                   ELSE u1.display_name
                               END as other_user_name,
                               CASE 
                                   WHEN c.user1_id = ? THEN u2.user_pin
                                   ELSE u1.user_pin
                               END as other_user_pin
                        FROM chats c
                        LEFT JOIN users u1 ON c.user1_id = u1.id
                        LEFT JOIN users u2 ON c.user2_id = u2.id
                        WHERE c.user1_id = ? OR c.user2_id = ?
                        ORDER BY c.created_at DESC
                    ''', (user_id, user_id, user_id, user_id, user_id))
                    chats = cursor.fetchall()
                
                return [{
                    "chat_id": str(chat['chat_id']),
                    "other_user_id": str(chat['other_user_id']),
                    "other_user_name": chat['other_user_name'],
                    "other_user_pin": chat['other_user_pin'],
                    "created_at": chat['created_at']
                } for chat in chats]
                
        except Exception as e:
            logger.error(f"Failed to get user chats: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get user chats: {str(e)}")