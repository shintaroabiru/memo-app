from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health は 200 OK と {"status": "ok"} を返す。"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
