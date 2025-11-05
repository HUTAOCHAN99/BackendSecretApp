# python_backend/app/database/database.py
import os
import asyncpg
import logging
from contextlib import asynccontextmanager
from app.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_url = self._get_database_url()
        self._pool = None
        logger.info(f"🔗 Database instance created with URL: {self._get_safe_url()}")
    
    def _get_database_url(self):
        """Get database URL from environment with proper formatting"""
        # Priority: 1. DATABASE_URL from env, 2. DATABASE_URL from settings, 3. Fallback
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            logger.warning("⚠️ DATABASE_URL not found in environment variables, using settings")
            database_url = settings.DATABASE_URL
        
        # Debug: Log what we found
        logger.info(f"🔍 Raw database URL: {self._get_safe_url_for_debug(database_url)}")
        
        # Convert postgres:// to postgresql:// untuk asyncpg
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("🔄 Converted postgres:// to postgresql://")
        
        if not database_url:
            logger.error("❌ No database URL found! Check your environment variables")
            raise ValueError("DATABASE_URL is required")
            
        logger.info(f"✅ Final database URL: {self._get_safe_url_for_debug(database_url)}")
        return database_url
    
    def _get_safe_url(self):
        """Return current database URL with password hidden"""
        return self._get_safe_url_for_debug(self.db_url)
    
    def _get_safe_url_for_debug(self, url):
        """Return database URL with password hidden for logging"""
        if not url:
            return "None"
        if "@" in url:
            parts = url.split("@")
            if "://" in parts[0]:
                auth_part = parts[0].split("://")[1]
                if ":" in auth_part:
                    user_pass = auth_part.split(":")
                    if len(user_pass) == 2:
                        # Hide password
                        return url.replace(f":{user_pass[1]}", ":***")
        return url
    
    async def get_pool(self):
        """Get database connection pool with retry logic"""
        if self._pool is None:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Creating database connection pool (attempt {attempt + 1}/{max_retries})...")
                    
                    self._pool = await asyncpg.create_pool(
                        self.db_url,
                        min_size=1,
                        max_size=10,
                        command_timeout=60,
                        server_settings={
                            'application_name': 'secret_chat_app',
                            'search_path': 'public'
                        }
                    )
                    
                    # Test the connection
                    async with self._pool.acquire() as conn:
                        version = await conn.fetchval("SELECT version()")
                        db_name = await conn.fetchval("SELECT current_database()")
                        logger.info(f"✅ Database connected successfully!")
                        logger.info(f"📊 Database: {db_name}")
                        logger.info(f"🐘 PostgreSQL: {version.split(',')[0]}")
                    
                    return self._pool
                    
                except Exception as e:
                    logger.error(f"❌ Connection attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error("💥 All connection attempts failed")
                        raise
                    
                    # Wait before retry
                    import asyncio
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
        
        return self._pool
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        pool = await self.get_pool()
        async with pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"❌ Database connection error: {e}")
                raise
    
    async def init_db(self):
        """Initialize database tables with comprehensive error handling"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Database initialization attempt {attempt + 1}/{max_retries}")
                
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
                    logger.info("✅ Users table created/verified")
                    
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
                    logger.info("✅ Verification codes table created/verified")
                    
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
                    logger.info("✅ Chats table created/verified")
                    
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
                    logger.info("✅ Messages table created/verified")
                    
                    # Create indexes
                    await conn.execute('''
                        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                        CREATE INDEX IF NOT EXISTS idx_users_pin ON users(user_pin);
                        CREATE INDEX IF NOT EXISTS idx_verification_codes_user_id ON verification_codes(user_id);
                        CREATE INDEX IF NOT EXISTS idx_chats_user1_id ON chats(user1_id);
                        CREATE INDEX IF NOT EXISTS idx_chats_user2_id ON chats(user2_id);
                        CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
                        CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
                        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
                    ''')
                    logger.info("✅ Database indexes created/verified")
                    
                logger.info("🎉 Database initialization completed successfully!")
                return
                
            except asyncpg.PostgresConnectionError as e:
                logger.error(f"❌ PostgreSQL connection error: {e}")
                if attempt == max_retries - 1:
                    logger.error("💥 Database initialization failed after all retries")
                    raise
                
            except asyncpg.UndefinedTableError as e:
                logger.error(f"❌ Table error: {e}")
                raise
                
            except Exception as e:
                logger.error(f"❌ Unexpected error during initialization: {e}")
                if attempt == max_retries - 1:
                    logger.error("💥 Database initialization failed")
                    # Don't raise, let the application continue
                    logger.info("🔄 Continuing without database initialization...")
                    return
                
            # Wait before retry
            import asyncio
            wait_time = (attempt + 1) * 3  # 3, 6, 9 seconds
            logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)
    
    async def health_check(self):
        """Check if database is responsive"""
        try:
            async with self.get_connection() as conn:
                # Simple query to check database health
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connection pool"""
        if self._pool:
            try:
                await self._pool.close()
                logger.info("✅ Database connection pool closed")
            except Exception as e:
                logger.error(f"❌ Error closing database pool: {e}")
            finally:
                self._pool = None

# Global database instance
db = Database()

# SQLite fallback (for development without PostgreSQL)
class SQLiteDatabase:
    """SQLite fallback implementation"""
    def __init__(self):
        import sqlite3
        self.db_path = "secret_chat.db"
        self.conn = None
        logger.info("🔧 Using SQLite fallback database")
    
    def get_connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def init_db(self):
        """Initialize SQLite database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
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
            cursor.execute('''
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    user1_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    user2_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user1_id, user2_id)
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT REFERENCES chats(id) ON DELETE CASCADE,
                    sender_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    encrypted_message TEXT NOT NULL,
                    iv TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ SQLite database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ SQLite initialization failed: {e}")
            raise
    
    async def close(self):
        """Close SQLite connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

# Factory function to get appropriate database instance
def get_database():
    """Get database instance based on available dependencies"""
    try:
        # Try to create PostgreSQL database first
        db_instance = Database()
        # Test if we can actually connect
        import asyncio
        try:
            asyncio.run(db_instance.health_check())
            logger.info("✅ Using PostgreSQL database")
            return db_instance
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL not available: {e}, falling back to SQLite")
            return SQLiteDatabase()
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL initialization failed: {e}, using SQLite fallback")
        return SQLiteDatabase()

# Global instance - auto-select based on availability
db = get_database()