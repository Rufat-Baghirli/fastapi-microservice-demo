import asyncio
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.db.session import get_session

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db-dev:5432/test_db"

engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)



@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh, isolated database session for each test.
    Drops and recreates all tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Creates a test client that uses the isolated test database.
    """
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()