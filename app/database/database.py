# python_backend/app/database/database.py
import os
import logging
from contextlib import asynccontextmanager
from app.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_url = self._get_database_url()
        self._pool = None
        self.db_type = self._detect_database_type()
        logger.info(f"🔗 Database type: {self.db_type}")
    
    def _get_database_url(self):
        """Get database URL from environment"""
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            logger.info("✅ DATABASE_URL found in environment")
            # Convert postgres:// to postgresql://
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        else:
            logger.warning("⚠️ DATABASE_URL not found in environment variables")
            # Use SQLite as default
            return "sqlite:///secret_chat.db"
    
    def _detect_database_type(self):
        """Detect database type from URL"""
        if self.db_url and 'postgres' in self.db_url:
            return 'postgresql'
        else:
            return 'sqlite'
    
    async def get_pool(self):
        """Get database connection pool"""
        if self._pool is None:
            if self.db_type == 'postgresql':
                await self._init_postgresql_pool()
            else:
                self._init_sqlite_pool()
        return self._pool
    
    async def _init_postgresql_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            import asyncpg
            logger.info("🔄 Creating PostgreSQL connection pool...")
            self._pool = await asyncpg.create_pool(self.db_url)
            logger.info("✅ PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            # Fallback to SQLite
            logger.info("🔄 Falling back to SQLite...")
            self.db_type = 'sqlite'
            self._init_sqlite_pool()
    
    def _init_sqlite_pool(self):
        """Initialize SQLite connection pool"""
        logger.info("🔧 Using SQLite database")
        self._pool = SQLiteConnectionPool()
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection"""
        pool = await self.get_pool()
        
        if self.db_type == 'postgresql':
            # PostgreSQL connection
            async with pool.acquire() as connection:
                yield connection
        else:
            # SQLite connection
            connection = pool.get_connection()
            try:
                yield connection
            finally:
                pool.return_connection(connection)
    
    async def init_db(self):
        """Initialize database tables"""
        try:
            if self.db_type == 'postgresql':
                await self._init_postgresql_tables()
            else:
                self._init_sqlite_tables()
            logger.info("✅ Database initialization completed successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    async def _init_postgresql_tables(self):
        """Initialize PostgreSQL tables"""
        async with self.get_connection() as conn:
            # Users table
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
            
            # Verification codes table
            await conn.execute('''
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
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(user1_id, user2_id)
                )
            ''')
            
            # Messages table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
                    sender_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    encrypted_message TEXT NOT NULL,
                    iv TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_pin ON users(user_pin)",
                "CREATE INDEX IF NOT EXISTS idx_verification_codes_user_id ON verification_codes(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_chats_user1_id ON chats(user1_id)",
                "CREATE INDEX IF NOT EXISTS idx_chats_user2_id ON chats(user2_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id)"
            ]
            
            for index in indexes:
                await conn.execute(index)
            
            logger.info("✅ PostgreSQL tables initialized")
    
    def _init_sqlite_tables(self):
        """Initialize SQLite tables"""
        conn = self._pool.get_connection()
        try:
            # Users table - SQLite compatible syntax
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    user_pin TEXT UNIQUE NOT NULL,
                    is_verified BOOLEAN DEFAULT 0,
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
                    used BOOLEAN DEFAULT 0,
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
            
            # Create indexes - SQLite compatible syntax
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_pin ON users(user_pin)",
                "CREATE INDEX IF NOT EXISTS idx_verification_codes_user_id ON verification_codes(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_chats_user1_id ON chats(user1_id)",
                "CREATE INDEX IF NOT EXISTS idx_chats_user2_id ON chats(user2_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id)"
            ]
            
            for index in indexes:
                conn.execute(index)
            
            conn.commit()
            logger.info("✅ SQLite tables initialized")
        finally:
            self._pool.return_connection(conn)
    
    async def health_check(self):
        """Check if database is responsive"""
        try:
            async with self.get_connection() as conn:
                if self.db_type == 'postgresql':
                    result = await conn.fetchval("SELECT 1")
                    return result == 1
                else:
                    cursor = conn.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connection pool"""
        if self._pool:
            try:
                if self.db_type == 'postgresql':
                    await self._pool.close()
                else:
                    self._pool.close()
                logger.info("✅ Database connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing database: {e}")


class SQLiteConnectionPool:
    """Simple SQLite connection pool"""
    def __init__(self):
        import sqlite3
        self.db_path = "secret_chat.db"
        logger.info(f"🔧 SQLite database: {self.db_path}")
    
    def get_connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def return_connection(self, conn):
        conn.close()
    
    def close(self):
        pass


# Global database instance
db = Database()