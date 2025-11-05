import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_url = self._get_database_url()
        logger.info(f"Database URL: {self.db_url}")  # Debug logging
    
    def _get_database_url(self):
        # Railway akan set DATABASE_URL environment variable
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Convert postgres:// to postgresql:// untuk psycopg2
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        
        # Fallback untuk development
        return "postgresql://postgres:password@localhost:5432/secret_chat"
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(
                self.db_url,
                cursor_factory=RealDictCursor
            )
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager 
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def init_db(self):
        """Initialize database tables"""
        try:
            with self.get_cursor() as cursor:
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        display_name VARCHAR(100) NOT NULL,
                        user_pin VARCHAR(6) UNIQUE NOT NULL,
                        is_verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # Verification codes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS verification_codes (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                        code VARCHAR(6) NOT NULL,
                        expires_at TIMESTAMPTZ NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # Chats table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chats (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
                        user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        UNIQUE(user1_id, user2_id)
                    )
                ''')
                
                # Messages table - dengan encryption fields
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
                        sender_id UUID REFERENCES users(id) ON DELETE CASCADE,
                        encrypted_message TEXT NOT NULL,
                        iv TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # Create indexes untuk performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_pin ON users(user_pin)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id)')
                
                logger.info("✅ Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

# Global database instance
db = Database()