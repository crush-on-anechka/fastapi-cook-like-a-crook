from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from settings import POSTGRES_URL

engine = create_async_engine(POSTGRES_URL)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
