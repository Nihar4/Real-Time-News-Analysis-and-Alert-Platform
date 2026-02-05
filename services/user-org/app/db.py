from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import text
from .config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Optional helper: make sure password column exists (if you didn't run ALTER)
async def ensure_password_column():
    async with engine.begin() as conn:
        res = await conn.execute(text("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'password_hash'
        """))
        if res.scalar() is None:
            await conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT
            """))
