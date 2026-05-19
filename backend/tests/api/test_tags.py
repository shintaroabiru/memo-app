"""タグAPIのテスト。"""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.main import app as fastapi_app
from app.models import Tag, UserProfile


def test_list_tags_returns_200_with_sorted_items(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    db_session.add_all(
        [
            Tag(user_id=default_user.id, name="b"),
            Tag(user_id=default_user.id, name="a"),
        ]
    )
    db_session.flush()

    res = api_client.get("/api/v1/tags")

    assert res.status_code == 200
    body = res.json()
    assert [item["name"] for item in body["items"]] == ["a", "b"]
    for item in body["items"]:
        assert {"id", "name", "created_at", "updated_at"} <= item.keys()


def test_list_tags_isolates_other_users(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    other = UserProfile(display_name="other")
    db_session.add(other)
    db_session.flush()
    db_session.add(Tag(user_id=other.id, name="他人のタグ"))
    db_session.add(Tag(user_id=default_user.id, name="自分のタグ"))
    db_session.flush()

    res = api_client.get("/api/v1/tags")
    body = res.json()
    assert [item["name"] for item in body["items"]] == ["自分のタグ"]


def test_create_tag_returns_201(api_client: TestClient) -> None:
    res = api_client.post("/api/v1/tags", json={"name": "新規"})

    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "新規"
    assert "id" in body


def test_create_tag_returns_400_on_validation_error(api_client: TestClient) -> None:
    res = api_client.post("/api/v1/tags", json={"name": ""})

    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_tag_returns_400_when_name_too_long(api_client: TestClient) -> None:
    res = api_client.post("/api/v1/tags", json={"name": "a" * 21})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_tag_returns_409_on_duplicate(api_client: TestClient) -> None:
    api_client.post("/api/v1/tags", json={"name": "重複"})

    res = api_client.post("/api/v1/tags", json={"name": "重複"})

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CONFLICT"


def test_update_tag_returns_200(api_client: TestClient) -> None:
    created = api_client.post("/api/v1/tags", json={"name": "旧"}).json()

    res = api_client.put(f"/api/v1/tags/{created['id']}", json={"name": "新"})

    assert res.status_code == 200
    assert res.json()["name"] == "新"


def test_update_tag_returns_404_when_missing(api_client: TestClient) -> None:
    res = api_client.put(f"/api/v1/tags/{uuid4()}", json={"name": "x"})

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_update_tag_returns_409_on_duplicate(api_client: TestClient) -> None:
    api_client.post("/api/v1/tags", json={"name": "A"})
    b = api_client.post("/api/v1/tags", json={"name": "B"}).json()

    res = api_client.put(f"/api/v1/tags/{b['id']}", json={"name": "A"})

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CONFLICT"


def test_update_tag_returns_400_on_validation_error(api_client: TestClient) -> None:
    created = api_client.post("/api/v1/tags", json={"name": "ok"}).json()

    res = api_client.put(f"/api/v1/tags/{created['id']}", json={"name": ""})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_delete_tag_returns_204(api_client: TestClient) -> None:
    created = api_client.post("/api/v1/tags", json={"name": "削除"}).json()

    res = api_client.delete(f"/api/v1/tags/{created['id']}")

    assert res.status_code == 204
    assert res.content == b""


def test_delete_tag_returns_404_when_missing(api_client: TestClient) -> None:
    res = api_client.delete(f"/api/v1/tags/{uuid4()}")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_create_tag_strips_surrounding_whitespace(api_client: TestClient) -> None:
    res = api_client.post("/api/v1/tags", json={"name": "  仕事  "})

    assert res.status_code == 201
    assert res.json()["name"] == "仕事"


def test_create_tag_returns_400_for_whitespace_only_name(api_client: TestClient) -> None:
    res = api_client.post("/api/v1/tags", json={"name": "   "})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_tag_detects_duplicate_after_strip(api_client: TestClient) -> None:
    """空白の有無で別タグになってしまわないことを保証する。"""
    api_client.post("/api/v1/tags", json={"name": "仕事"})

    res = api_client.post("/api/v1/tags", json={"name": "  仕事  "})

    assert res.status_code == 409


def test_other_user_cannot_access_tag(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    """`dependency_overrides[get_current_user_id]` を差し替えて権限分離を検証する。"""
    other = UserProfile(display_name="other")
    db_session.add(other)
    db_session.flush()
    other_tag = Tag(user_id=other.id, name="他人")
    db_session.add(other_tag)
    db_session.flush()

    # default_user として更新を試みると 404
    res = api_client.put(f"/api/v1/tags/{other_tag.id}", json={"name": "x"})
    assert res.status_code == 404

    # `other` ユーザーに差し替えると同じタグを操作できる
    fastapi_app.dependency_overrides[get_current_user_id] = lambda: other.id
    res = api_client.put(f"/api/v1/tags/{other_tag.id}", json={"name": "更新後"})
    assert res.status_code == 200
    assert res.json()["name"] == "更新後"
