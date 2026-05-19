"""MemoService のテスト。"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.models import Memo, Tag, UserProfile
from app.schemas.memo import MemoCreate, MemoListQuery
from app.services.memo_service import MemoService


def _make_user(db: Session, display_name: str = "テスト") -> UserProfile:
    user = UserProfile(display_name=display_name)
    db.add(user)
    db.flush()
    return user


def _make_tag(db: Session, user: UserProfile, name: str) -> Tag:
    tag = Tag(user_id=user.id, name=name)
    db.add(tag)
    db.flush()
    return tag


def test_get_memo_returns_memo(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)
    memo = service.create_memo(user_id=user.id, payload=MemoCreate(title="t"))

    fetched = service.get_memo(user_id=user.id, memo_id=memo.id)

    assert fetched.id == memo.id


def test_get_memo_raises_not_found_for_other_user(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    service = MemoService(db_session)
    memo = service.create_memo(user_id=owner.id, payload=MemoCreate(title="own"))

    with pytest.raises(NotFoundError):
        service.get_memo(user_id=other.id, memo_id=memo.id)


def test_create_memo_persists_fields(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)

    memo = service.create_memo(
        user_id=user.id,
        payload=MemoCreate(title="新規", body="本文", is_pinned=True),
    )

    assert memo.id is not None
    assert memo.title == "新規"
    assert memo.body == "本文"
    assert memo.is_pinned is True


def test_create_memo_links_existing_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    service = MemoService(db_session)

    memo = service.create_memo(
        user_id=user.id,
        payload=MemoCreate(title="t", tag_ids=[tag_a.id, tag_b.id]),
    )

    assert {t.id for t in memo.tags} == {tag_a.id, tag_b.id}


def test_create_memo_rejects_nonexistent_tag_id(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)

    with pytest.raises(BadRequestError):
        service.create_memo(
            user_id=user.id,
            payload=MemoCreate(title="t", tag_ids=[uuid4()]),
        )


def test_create_memo_rejects_other_users_tag_id(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    other_tag = _make_tag(db_session, other, "other_tag")
    service = MemoService(db_session)

    with pytest.raises(BadRequestError):
        service.create_memo(
            user_id=owner.id,
            payload=MemoCreate(title="t", tag_ids=[other_tag.id]),
        )


def test_update_memo_replaces_fields_and_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    service = MemoService(db_session)
    memo = service.create_memo(
        user_id=user.id,
        payload=MemoCreate(title="old", body="ob", tag_ids=[tag_a.id]),
    )

    updated = service.update_memo(
        user_id=user.id,
        memo_id=memo.id,
        payload=MemoCreate(title="new", body="nb", tag_ids=[tag_b.id], is_pinned=True),
    )

    assert updated.title == "new"
    assert updated.body == "nb"
    assert updated.is_pinned is True
    assert {t.id for t in updated.tags} == {tag_b.id}


def test_update_memo_raises_not_found(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)

    with pytest.raises(NotFoundError):
        service.update_memo(
            user_id=user.id,
            memo_id=uuid4(),
            payload=MemoCreate(title="x"),
        )


def test_update_memo_rejects_invalid_tag_id(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)
    memo = service.create_memo(user_id=user.id, payload=MemoCreate(title="t"))

    with pytest.raises(BadRequestError):
        service.update_memo(
            user_id=user.id,
            memo_id=memo.id,
            payload=MemoCreate(title="t", tag_ids=[uuid4()]),
        )


def test_delete_memo_removes_memo(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)
    memo = service.create_memo(user_id=user.id, payload=MemoCreate(title="t"))

    service.delete_memo(user_id=user.id, memo_id=memo.id)

    assert db_session.get(Memo, memo.id) is None


def test_delete_memo_raises_not_found(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)

    with pytest.raises(NotFoundError):
        service.delete_memo(user_id=user.id, memo_id=uuid4())


def test_toggle_pin_updates_flag_and_updated_at(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)
    memo = service.create_memo(user_id=user.id, payload=MemoCreate(title="t"))

    # savepoint 内で now() が固定値のため、過去日にバックデートしてから検証
    past = datetime.now(UTC) - timedelta(days=1)
    db_session.execute(
        text("UPDATE memos SET updated_at = :ts WHERE id = :id"),
        {"ts": past, "id": memo.id},
    )
    db_session.expire(memo)
    db_session.refresh(memo)
    before = memo.updated_at

    updated = service.toggle_pin(user_id=user.id, memo_id=memo.id, is_pinned=True)

    assert updated.is_pinned is True
    assert updated.updated_at > before


def test_toggle_pin_raises_not_found(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)

    with pytest.raises(NotFoundError):
        service.toggle_pin(user_id=user.id, memo_id=uuid4(), is_pinned=True)


# ===== list_memos のテスト =====


def test_list_memos_returns_items_total_limit_offset(db_session: Session) -> None:
    user = _make_user(db_session)
    service = MemoService(db_session)
    service.create_memo(user_id=user.id, payload=MemoCreate(title="a"))
    service.create_memo(user_id=user.id, payload=MemoCreate(title="b"))

    result = service.list_memos(user_id=user.id, query=MemoListQuery(limit=10, offset=0))

    assert result["total"] == 2
    assert result["limit"] == 10
    assert result["offset"] == 0
    assert {m.title for m in result["items"]} == {"a", "b"}


def test_list_memos_normalizes_q_with_strip(db_session: Session) -> None:
    """前後空白を含むキーワードはトリムされる。"""
    user = _make_user(db_session)
    service = MemoService(db_session)
    service.create_memo(user_id=user.id, payload=MemoCreate(title="買い物"))

    result = service.list_memos(user_id=user.id, query=MemoListQuery(q="  買い物  "))

    assert result["total"] == 1
    assert result["items"][0].title == "買い物"


def test_list_memos_treats_whitespace_only_q_as_no_filter(db_session: Session) -> None:
    """空白のみの q は「未指定」と同じ扱いで全件返す。"""
    user = _make_user(db_session)
    service = MemoService(db_session)
    service.create_memo(user_id=user.id, payload=MemoCreate(title="a"))
    service.create_memo(user_id=user.id, payload=MemoCreate(title="b"))

    result = service.list_memos(user_id=user.id, query=MemoListQuery(q="   "))

    assert result["total"] == 2


def test_list_memos_items_tags_are_sorted_by_name(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_z = _make_tag(db_session, user, "z")
    tag_a = _make_tag(db_session, user, "a")
    service = MemoService(db_session)
    service.create_memo(
        user_id=user.id,
        payload=MemoCreate(title="t", tag_ids=[tag_z.id, tag_a.id]),
    )

    result = service.list_memos(user_id=user.id, query=MemoListQuery())

    assert [t.name for t in result["items"][0].tags] == ["a", "z"]
