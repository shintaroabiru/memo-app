import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPIのテスト用HTTPクライアント。"""
    return TestClient(app)
