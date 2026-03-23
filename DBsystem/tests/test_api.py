import asyncio
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import engine
from app.models.models import Base

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.mark.anyio
async def test_create_member():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/members/", json={"name": "Alice", "role": "Mentor"})
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"

@pytest.mark.anyio
async def test_create_equipment():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/equipment/", json={
            "name": "Microscope", 
            "maintenance_interval": 30,
            "last_maintenance_date": "2024-03-01"
        })
    assert response.status_code == 200
    assert response.json()["name"] == "Microscope"

@pytest.mark.anyio
async def test_create_consumable():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/inventory/consumables", json={
            "name": "Pipettes",
            "quantity": 100,
            "threshold": 20
        })
    assert response.status_code == 200
    assert response.json()["name"] == "Pipettes"
