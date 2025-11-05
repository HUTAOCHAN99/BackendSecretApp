# python_backend/app/database/database.py
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_url = self._get_database_url()
        self._pool = None
        logger.info(f"🔗 Database instance created")
        logger.info(f"📊 Database type: {'PostgreSQL' if 'postgres' in self.db_url else 'SQLite'}")
    
    def _get_database_url(self):
        """Get database URL from environment with proper formatting"""
        # Priority: 1. DATABASE_URL from env, 2. DATABASE_URL from settings
        database_url = os.environ.get('DATABASE_URL')
        
        # Log environment info for debugging
        env_info = {
            'DATABASE_URL_exists': bool(database_url),
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            'RAILWAY_SERVICE_NAME': os.environ.get('RAILWAY_SERVICE_NAME'),
            'NODE_ENV': os.environ.get('NODE_ENV')
        }
        logger.info(f"🔍 Environment info: {env_info}")
        
        if database_url:
            logger.info("✅ Using DATABASE_URL from environment variables")
        else:
            logger.warning("⚠️ DATABASE_URL not found in environment variables")
            database_url = settings.DATABASE_URL
            logger.info("🔧 Using DATABASE_URL from settings")
        
        # Convert postgres:// to postgresql:// untuk asyncpg
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("🔄 Converted postgres:// to postgresql://")
        
        logger.info(f"🏁 Final database URL: {self._get_safe_url(database_url)}")
        return database_url
    
    def _get_safe_url(self, url=None):
        """Return database URL with password hidden for logging"""
        if url is None:
            url = self.db_url
            
        if not url:
            return "None"
            
        if "@" in url:
            parts = url.split("@")
            if "://" in parts[0]:
                auth_part = parts[0].split("://")[1]
                if ":" in auth_part:
                    user_pass = auth_part.split(":")
                    if len(user_pass) == 2:
                        # Hide password but show user and host
                        safe_url = url.replace(f":{user_pass[1]}@", ":***@")
                        return safe_url
        return url
    
    async def get_pool(self):
        """Get database connection pool"""
        if self._pool is None:
            try:
                logger.info("🔄 Creating database connection pool...")
                
                # Check if we should use PostgreSQL or SQLite
                if self.db_url and 'postgres' in self.db_url:
                    import asyncpg
                    self._pool = await asyncpg.create_pool(
                        self.db_url,
                        min_size=1,
                        max_size=10,
                        command_timeout=60
                    )
                    logger.info("✅ PostgreSQL connection pool created")
                else:
                    # Use SQLite
                    self._pool = SQLiteConnectionPool()
                    logger.info("✅ SQLite connection pool created")
                    
            except Exception as e:
                logger.error(f"❌ Failed to create database connection pool: {e}")
                # Fallback to SQLite
                logger.info("🔄 Falling back to SQLite...")
                self._pool = SQLiteConnectionPool()
                
        return self._pool
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        pool = await self.get_pool()
        
        if hasattr(pool, 'acquire') and callable(getattr(pool, 'acquire')):
            # PostgreSQL connection
            async with pool.acquire() as connection:
                try:
                    yield connection
                except Exception as e:
                    logger.error(f"❌ PostgreSQL connection error: {e}")
                    raise
        else:
            # SQLite connection
            connection = pool.get_connection()
            try:
                yield connection
            except Exception as e:
                logger.error(f"❌ SQLite connection error: {e}")
                raise
            finally:
                pool.return_connection(connection)
    
    async def init_db(self):
        """Initialize database tables"""
        try:
            async with self.get_connection() as conn:
                if hasattr(conn, 'execute'):  # PostgreSQL
                    await self._init_postgresql(conn)
                else:  # SQLite
                    self._init_sqlite(conn)
                    
            logger.info("✅ Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.info("🔄 Continuing application startup...")
    
    async def _init_postgresql(self, conn):
        """Initialize PostgreSQL tables"""
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
        logger.info("✅ PostgreSQL users table created/verified")
        
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
        logger.info("✅ PostgreSQL verification_codes table created/verified")
        
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
        logger.info("✅ PostgreSQL chats table created/verified")
        
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
        logger.info("✅ PostgreSQL messages table created/verified")
        
        # Create indexes
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_pin ON users(user_pin);
            CREATE INDEX IF NOT EXISTS idx_verification_codes_user_id ON verification_codes(user_id);
            CREATE INDEX IF NOT EXISTS idx_chats_user1_id ON chats(user1_id);
            CREATE INDEX IF NOT EXISTS idx_chats_user2_id ON chats(user2_id);
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
            CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
        ''')
        logger.info("✅ PostgreSQL indexes created/verified")
    
    def _init_sqlite(self, conn):
        """Initialize SQLite tables"""
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
        conn.execute('CREATE INDEX IF NOT EXISTS idx_verification_codes_user_id ON verification_codes(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_user1_id ON chats(user1_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_user2_id ON chats(user2_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id)')
        
        conn.commit()
        logger.info("✅ SQLite tables and indexes created/verified")
    
    async def health_check(self):
        """Check if database is responsive"""
        try:
            async with self.get_connection() as conn:
                if hasattr(conn, 'fetchval'):  # PostgreSQL
                    result = await conn.fetchval("SELECT 1")
                    return result == 1
                else:  # SQLite
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
                if hasattr(self._pool, 'close'):
                    await self._pool.close()
                    logger.info("✅ Database connection pool closed")
                else:
                    self._pool.close()
                    logger.info("✅ SQLite connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing database pool: {e}")
            finally:
                self._pool = None


class SQLiteConnectionPool:
    """Simple SQLite connection pool"""
    def __init__(self):
        import sqlite3
        self.db_path = "secret_chat.db"
        self.connections = []
        logger.info("🔧 SQLite connection pool initialized")
    
    def get_connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def return_connection(self, conn):
        conn.close()
    
    def close(self):
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        self.connections.clear()


# Global database instance
db = Database()