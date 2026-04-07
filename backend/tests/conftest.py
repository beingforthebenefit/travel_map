import asyncio
import tempfile
from pathlib import Path

import pytest
import httpx

from app.config import settings


@pytest.fixture(autouse=True)
def tmp_data_dir(tmp_path):
    """Point data_dir at a temp directory for each test."""
    original = settings.data_dir
    settings.data_dir = str(tmp_path)
    # Reset cached db path
    import app.database as db_mod
    db_mod._db_path = None
    yield tmp_path
    settings.data_dir = original
    db_mod._db_path = None


@pytest.fixture
async def db(tmp_data_dir):
    from app.database import init_db, get_db
    await init_db()
    conn = await get_db()
    yield conn
    await conn.close()


@pytest.fixture
async def client(tmp_data_dir):
    from app.database import init_db
    await init_db()
    from app.main import app
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
