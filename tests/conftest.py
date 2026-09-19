import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Use test sqlite DB
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_pnbc.db"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///./test_pnbc.db"
os.environ["CELERY_ENABLED"] = "False"
os.environ["STORAGE_DIR"] = "data/test_uploads"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User

test_engine = create_async_engine("sqlite+aiosqlite:///./test_pnbc.db", echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(client):
    async with TestSessionLocal() as session:
        user = User(
            email="test_evaluator@pragatibharati.edu",
            hashed_password=get_password_hash("Secret@123"),
            full_name="Test Evaluator",
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(
        subject=test_user.id,
        claims={"role": test_user.role, "email": test_user.email}
    )
    return {"Authorization": f"Bearer {token}"}
