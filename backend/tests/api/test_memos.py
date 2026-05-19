"""メモAPIのテスト。"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Memo, MemoTag, Tag, UserProfile


def _create(api_client: TestClient, **fields: object) -> dict:
    payload = {"title": "t"}
    payload.update(fields)
    res = api_client.post("/api/v1/memos", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_get_memo_returns_200(api_client: TestClient) -> None:
    created = _create(api_client, title="詳細", body="本文")

    res = api_client.get(f"/api/v1/memos/{created['id']}")

    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "詳細"
    assert body["body"] == "本文"
    assert body["is_pinned"] is False
    assert body["tags"] == []
    assert {"id", "title", "body", "is_pinned", "tags", "created_at", "updated_at"} <= body.keys()


def test_get_memo_returns_404_when_missing(api_client: TestClient) -> None:
    res = api_client.get(f"/api/v1/memos/{uuid4()}")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_create_memo_returns_201(api_client: TestClient) -> None:
    res = api_client.post(
        "/api/v1/memos",
        json={"title": " 新規 ", "body": "x", "is_pinned": True},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "新規"  # title はトリムされる
    assert body["is_pinned"] is True


def test_create_memo_with_tags(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    tag_a = Tag(user_id=default_user.id, name="a")
    tag_b = Tag(user_id=default_user.id, name="b")
    db_session.add_all([tag_a, tag_b])
    db_session.flush()

    res = api_client.post(
        "/api/v1/memos",
        json={"title": "t", "tag_ids": [str(tag_a.id), str(tag_b.id)]},
    )

    assert res.status_code == 201
    body = res.json()
    assert [t["name"] for t in body["tags"]] == ["a", "b"]


def test_create_memo_returns_400_on_validation_error(api_client: TestClient) -> None:
    res = api_client.post("/api/v1/memos", json={"title": ""})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_memo_returns_400_for_nonexistent_tag_id(api_client: TestClient) -> None:
    res = api_client.post(
        "/api/v1/memos",
        json={"title": "t", "tag_ids": [str(uuid4())]},
    )

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"


def test_create_memo_returns_400_for_other_users_tag(
    api_client: TestClient, db_session: Session
) -> None:
    other = UserProfile(display_name="other")
    db_session.add(other)
    db_session.flush()
    other_tag = Tag(user_id=other.id, name="他人")
    db_session.add(other_tag)
    db_session.flush()

    res = api_client.post(
        "/api/v1/memos",
        json={"title": "t", "tag_ids": [str(other_tag.id)]},
    )

    assert res.status_code == 400


def test_update_memo_returns_200(api_client: TestClient) -> None:
    created = _create(api_client, title="old", body="ob")

    res = api_client.put(
        f"/api/v1/memos/{created['id']}",
        json={"title": "new", "body": "nb", "is_pinned": True},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "new"
    assert body["body"] == "nb"
    assert body["is_pinned"] is True


def test_update_memo_replaces_tags(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    tag_a = Tag(user_id=default_user.id, name="a")
    tag_b = Tag(user_id=default_user.id, name="b")
    db_session.add_all([tag_a, tag_b])
    db_session.flush()
    created = _create(api_client, title="t", tag_ids=[str(tag_a.id)])

    res = api_client.put(
        f"/api/v1/memos/{created['id']}",
        json={"title": "t", "tag_ids": [str(tag_b.id)]},
    )

    assert res.status_code == 200
    assert [t["name"] for t in res.json()["tags"]] == ["b"]


def test_update_memo_returns_404_when_missing(api_client: TestClient) -> None:
    res = api_client.put(f"/api/v1/memos/{uuid4()}", json={"title": "x"})

    assert res.status_code == 404


def test_update_memo_returns_400_for_invalid_tag_id(api_client: TestClient) -> None:
    created = _create(api_client, title="t")

    res = api_client.put(
        f"/api/v1/memos/{created['id']}",
        json={"title": "t", "tag_ids": [str(uuid4())]},
    )

    assert res.status_code == 400


def test_delete_memo_returns_204(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    tag = Tag(user_id=default_user.id, name="t")
    db_session.add(tag)
    db_session.flush()
    created = _create(api_client, title="t", tag_ids=[str(tag.id)])

    res = api_client.delete(f"/api/v1/memos/{created['id']}")

    assert res.status_code == 204
    assert res.content == b""
    # memo_tags も CASCADE で消える、タグ本体は残る
    assert db_session.query(MemoTag).filter_by(memo_id=created["id"]).count() == 0
    assert db_session.get(Tag, tag.id) is not None
    assert db_session.get(Memo, created["id"]) is None


def test_delete_memo_returns_404_when_missing(api_client: TestClient) -> None:
    res = api_client.delete(f"/api/v1/memos/{uuid4()}")

    assert res.status_code == 404


def test_patch_pin_returns_200_with_subset_fields(
    api_client: TestClient, db_session: Session
) -> None:
    created = _create(api_client, title="t")

    # 過去日に backdate して updated_at の変化を検証する
    past = datetime.now(UTC) - timedelta(days=1)
    db_session.execute(
        text("UPDATE memos SET updated_at = :ts WHERE id = :id"),
        {"ts": past, "id": created["id"]},
    )
    db_session.commit()

    res = api_client.patch(
        f"/api/v1/memos/{created['id']}/pin",
        json={"is_pinned": True},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["is_pinned"] is True
    assert body["id"] == created["id"]
    assert "updated_at" in body
    assert datetime.fromisoformat(body["updated_at"]) > past
    # ピン専用レスポンスは title / body / tags を含まない
    assert "title" not in body
    assert "body" not in body
    assert "tags" not in body


def test_patch_pin_returns_404_when_missing(api_client: TestClient) -> None:
    res = api_client.patch(f"/api/v1/memos/{uuid4()}/pin", json={"is_pinned": True})

    assert res.status_code == 404
