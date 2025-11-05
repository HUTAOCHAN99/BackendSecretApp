# python_backend/app/database/database.py
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Try asyncpg first, fallback to sqlite3
try:
    import asyncpg
    from contextlib import asynccontextmanager
    HAS_ASYNC_PG = True
    print("✅ Using PostgreSQL with asyncpg")
    
    class Database:
        def __init__(self):
            self.db_url = self._get_database_url()
            self._pool = None
        
        def _get_database_url(self):
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                return database_url
            return "postgresql://postgres:password@localhost:5432/secret_chat"
        
        async def get_pool(self):
            if self._pool is None:
                self._pool = await asyncpg.create_pool(self.db_url)
            return self._pool
        
        @asynccontextmanager
        async def get_connection(self):
            pool = await self.get_pool()
            async with pool.acquire() as connection:
                yield connection
        
        async def init_db(self):
            try:
                async with self.get_connection() as conn:
                    # Your existing table creation code...
                    await conn.execute('''
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
                    # ... other tables
                    
                logger.info("✅ PostgreSQL database initialized successfully")
            except Exception as e:
                logger.error(f"❌ PostgreSQL initialization failed: {e}")
                raise
        
        async def close(self):
            if self._pool:
                await self._pool.close()

except ImportError:
    HAS_ASYNC_PG = False
    print("⚠️ asyncpg not available, using SQLite fallback")
    import sqlite3
    import uuid
    from contextlib import contextmanager
    
    class Database:
        def __init__(self):
            self.db_path = "secret_chat.db"
            self._init_sqlite()
        
        def _init_sqlite(self):
            with self.get_connection() as conn:
                # Users table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        display_name TEXT NOT NULL,
                        user_pin TEXT UNIQUE NOT NULL,
                        is_verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Verification codes table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS verification_codes (
                        id TEXT PRIMARY KEY,
                        user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                        code TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Chats table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS chats (
                        id TEXT PRIMARY KEY,
                        user1_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                        user2_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user1_id, user2_id)
                    )
                ''')
                
                # Messages table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        chat_id TEXT REFERENCES chats(id) ON DELETE CASCADE,
                        sender_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                        encrypted_message TEXT NOT NULL,
                        iv TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_users_pin ON users(user_pin)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)')
        
        @contextmanager
        def get_connection(self):
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        
        async def init_db(self):
            logger.info("✅ SQLite database initialized")
        
        async def close(self):
            pass

db = Database()