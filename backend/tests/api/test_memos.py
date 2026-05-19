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


def test_create_memo_returns_tags_in_name_order_regardless_of_input(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    """POST レスポンスの tags はタグ名昇順で返る（api-spec.md §2.1-2.2）。

    タグの挿入順をアルファベット逆順にすることで、挿入順序とソート順の偶然の一致を排除する。
    """
    tag_z = Tag(user_id=default_user.id, name="z")
    tag_a = Tag(user_id=default_user.id, name="a")
    db_session.add_all([tag_z, tag_a])
    db_session.flush()

    res = api_client.post(
        "/api/v1/memos",
        json={"title": "t", "tag_ids": [str(tag_z.id), str(tag_a.id)]},
    )

    assert res.status_code == 201
    assert [t["name"] for t in res.json()["tags"]] == ["a", "z"]


def test_update_memo_returns_tags_in_name_order_regardless_of_input(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    tag_z = Tag(user_id=default_user.id, name="z")
    tag_a = Tag(user_id=default_user.id, name="a")
    db_session.add_all([tag_z, tag_a])
    db_session.flush()
    created = _create(api_client, title="t")

    res = api_client.put(
        f"/api/v1/memos/{created['id']}",
        json={"title": "t", "tag_ids": [str(tag_z.id), str(tag_a.id)]},
    )

    assert res.status_code == 200
    assert [t["name"] for t in res.json()["tags"]] == ["a", "z"]


def test_create_memo_returns_clean_message_for_duplicate_tag_ids(api_client: TestClient) -> None:
    """API レスポンスの details.message は Pydantic 内部前置き ("Value error, ") を含まない。"""
    tag_id = str(uuid4())
    res = api_client.post(
        "/api/v1/memos",
        json={"title": "t", "tag_ids": [tag_id, tag_id]},
    )

    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    tag_ids_detail = next(d for d in body["error"]["details"] if d["field"] == "tag_ids")
    assert tag_ids_detail["message"] == "重複したタグIDが含まれています"


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


# ===== GET /api/v1/memos =====


def test_list_memos_returns_200_with_envelope(api_client: TestClient) -> None:
    _create(api_client, title="a")
    _create(api_client, title="b")

    res = api_client.get("/api/v1/memos")

    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert {m["title"] for m in body["items"]} == {"a", "b"}


def test_list_memos_filters_by_q(api_client: TestClient) -> None:
    _create(api_client, title="Hello", body="World")
    _create(api_client, title="Foo")

    res = api_client.get("/api/v1/memos", params={"q": "hello"})

    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Hello"


def test_list_memos_filters_by_pinned(api_client: TestClient) -> None:
    _create(api_client, title="p", is_pinned=True)
    _create(api_client, title="np", is_pinned=False)

    res = api_client.get("/api/v1/memos", params={"pinned": "true"})

    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "p"


def test_list_memos_filters_by_tag_ids_and_condition(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    tag_a = Tag(user_id=default_user.id, name="a")
    tag_b = Tag(user_id=default_user.id, name="b")
    db_session.add_all([tag_a, tag_b])
    db_session.flush()
    _create(api_client, title="only_a", tag_ids=[str(tag_a.id)])
    _create(api_client, title="a_and_b", tag_ids=[str(tag_a.id), str(tag_b.id)])

    res = api_client.get(
        "/api/v1/memos",
        # ?tag_ids=...&tag_ids=... の形式
        params=[("tag_ids", str(tag_a.id)), ("tag_ids", str(tag_b.id))],
    )

    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "a_and_b"


def test_list_memos_limit_offset(api_client: TestClient) -> None:
    for i in range(5):
        _create(api_client, title=f"m{i}")

    res = api_client.get("/api/v1/memos", params={"limit": 2, "offset": 1})

    body = res.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2


def test_list_memos_returns_400_when_limit_exceeds_max(api_client: TestClient) -> None:
    res = api_client.get("/api/v1/memos", params={"limit": 101})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_memos_returns_400_when_offset_negative(api_client: TestClient) -> None:
    res = api_client.get("/api/v1/memos", params={"offset": -1})

    assert res.status_code == 400


def test_list_memos_returns_400_for_invalid_uuid_in_tag_ids(api_client: TestClient) -> None:
    res = api_client.get("/api/v1/memos", params={"tag_ids": "not-a-uuid"})

    assert res.status_code == 400


def test_list_memos_returns_400_when_q_exceeds_max_length(api_client: TestClient) -> None:
    res = api_client.get("/api/v1/memos", params={"q": "a" * 201})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_memos_isolates_other_users(
    api_client: TestClient, db_session: Session, default_user: UserProfile
) -> None:
    other = UserProfile(display_name="other")
    db_session.add(other)
    db_session.flush()
    from app.models import Memo

    db_session.add(Memo(user_id=other.id, title="他人のメモ"))
    db_session.flush()
    _create(api_client, title="自分のメモ")

    res = api_client.get("/api/v1/memos")

    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "自分のメモ"
