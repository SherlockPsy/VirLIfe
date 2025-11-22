from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config.settings import settings

# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    connect_args={"ssl": False},  # Disable SSL for Railway
    echo=settings.environment == "development",
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
