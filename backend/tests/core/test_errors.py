"""共通エラー基盤のテスト。

ダミーのエンドポイントを立て、各例外型ごとにステータスコードとレスポンスボディ形を検証する。
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.errors import (
    AppException,
    BadRequestError,
    ConflictError,
    NotFoundError,
    register_exception_handlers,
)


def _make_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    class _Body(BaseModel):
        name: str = Field(min_length=1, max_length=5)

    @app.get("/raise/not-found")
    def _not_found() -> None:
        raise NotFoundError(message="タグが見つかりません")

    @app.get("/raise/conflict")
    def _conflict() -> None:
        raise ConflictError(
            message="同名タグが存在します",
            details=[{"field": "name", "message": "重複"}],
        )

    @app.get("/raise/bad-request")
    def _bad_request() -> None:
        raise BadRequestError(message="不正なリクエストです")

    @app.get("/raise/app-exception")
    def _custom() -> None:
        raise AppException(code="CUSTOM_CODE", http_status=418, message="custom")

    @app.post("/validate")
    def _validate(body: _Body) -> dict[str, str]:
        return {"name": body.name}

    return app


def test_not_found_error_returns_404_with_app_format() -> None:
    client = TestClient(_make_app())
    res = client.get("/raise/not-found")

    assert res.status_code == 404
    body = res.json()
    assert body == {
        "error": {
            "code": "NOT_FOUND",
            "message": "タグが見つかりません",
            "details": None,
        }
    }


def test_conflict_error_returns_409_with_details() -> None:
    client = TestClient(_make_app())
    res = client.get("/raise/conflict")

    assert res.status_code == 409
    body = res.json()
    assert body["error"]["code"] == "CONFLICT"
    assert body["error"]["message"] == "同名タグが存在します"
    assert body["error"]["details"] == [{"field": "name", "message": "重複"}]


def test_bad_request_error_returns_400() -> None:
    client = TestClient(_make_app())
    res = client.get("/raise/bad-request")

    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["message"] == "不正なリクエストです"


def test_generic_app_exception_uses_provided_code_and_status() -> None:
    client = TestClient(_make_app())
    res = client.get("/raise/app-exception")

    assert res.status_code == 418
    body = res.json()
    assert body["error"]["code"] == "CUSTOM_CODE"
    assert body["error"]["message"] == "custom"


def test_request_validation_error_returns_400_with_app_format() -> None:
    client = TestClient(_make_app())
    res = client.post("/validate", json={"name": "toolongname"})

    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) >= 1
    # details 各要素は field / message を含む
    first = body["error"]["details"][0]
    assert "field" in first
    assert "message" in first
