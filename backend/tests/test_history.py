"""Milestone 1.5 — History API Tests."""

from __future__ import annotations

import os
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from models.database import EnhancementJob, User, ModelConfig

@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    yield

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
async def setup_database():
    from db.session import AsyncSessionLocal, engine, init_db
    from models.database import Base

    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_verify_token():
    with patch("middleware.auth.firebase_auth.verify_id_token") as mock:
        mock.return_value = {
            "uid": "test-uid-001",
            "email": "test@neurallens.com",
            "name": "Test User",
        }
        yield mock

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_empty_history(client, mock_verify_token):
    """Test 1: Empty history -> 200, items=[], total=0."""
    response = client.get("/api/history", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_history_pagination_and_soft_delete(client, mock_verify_token):
    """Test 2, 3, 4, 5: Pagination, completed jobs only, soft deleted exclusion."""
    from db.session import AsyncSessionLocal
    
    # Call once to create user
    client.get("/api/history", headers={"Authorization": "Bearer fake-token"})
    
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.firebase_uid == "test-uid-001"))).scalar_one()
        model = (await session.execute(select(ModelConfig).limit(1))).scalar_one()
        
        # Create 3 completed jobs
        for i in range(3):
            session.add(EnhancementJob(
                id=str(uuid4()), user_id=user.id, model_config_id=model.id, 
                original_filename=f"test{i}.png", status="completed", scale_factor=4.0,
                input_file_path="/tmp/fake", input_size_bytes=100, input_width=100, input_height=100, input_format="PNG"
            ))
            
        # Create 1 failed job
        session.add(EnhancementJob(
            id=str(uuid4()), user_id=user.id, model_config_id=model.id, 
            original_filename="fail.png", status="failed", scale_factor=4.0,
            input_file_path="/tmp/fake", input_size_bytes=100, input_width=100, input_height=100, input_format="PNG"
        ))
        
        # Create 1 deleted job (soft delete)
        session.add(EnhancementJob(
            id=str(uuid4()), user_id=user.id, model_config_id=model.id, 
            original_filename="deleted.png", status="completed", scale_factor=4.0,
            input_file_path="/tmp/fake", input_size_bytes=100, input_width=100, input_height=100, input_format="PNG",
            deleted_at=datetime.now(timezone.utc)
        ))
        await session.commit()
        
    # Get page 1, size 2
    response = client.get("/api/history?page=1&page_size=2", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3 # Only completed, non-deleted
    assert len(data["items"]) == 2
    
    # Get page 2, size 2
    response2 = client.get("/api/history?page=2&page_size=2", headers={"Authorization": "Bearer fake-token"})
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total"] == 3
    assert len(data2["items"]) == 1
    
    # Get page 1, size 100 -> should clamp to 50 but TestClient actually raises validation error for page_size=100
    response3 = client.get("/api/history?page=1&page_size=100", headers={"Authorization": "Bearer fake-token"})
    assert response3.status_code == 422 # Pydantic Query(le=50) validation fails

def test_history_unauthenticated(client):
    """Test 6: Unauthenticated -> 422/401."""
    response = client.get("/api/history")
    assert response.status_code == 422
