# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app  # Your FastAPI app
from app.middleware import security
@pytest.fixture
def client():
    """Provides a test client for making requests"""
    return TestClient(app)
@pytest.fixture(autouse=True)
def reset_blocked():
    """Reset BLOCKED dict before each test to ensure isolation"""
    security.BLOCKED.clear()
    yield
    security.BLOCKED.clear()