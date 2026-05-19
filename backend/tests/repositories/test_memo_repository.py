"""MemoRepository のテスト（実DBでの memos + memo_tags 操作）。"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Memo, MemoTag, Tag, UserProfile
from app.repositories.memo_repository import MemoRepository


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


def test_get_returns_memo_for_owner(db_session: Session) -> None:
    user = _make_user(db_session)
    memo = Memo(user_id=user.id, title="t")
    db_session.add(memo)
    db_session.flush()

    repo = MemoRepository(db_session)
    found = repo.get(memo_id=memo.id, user_id=user.id)

    assert found is not None
    assert found.id == memo.id


def test_get_returns_none_for_other_user(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    memo = Memo(user_id=owner.id, title="own")
    db_session.add(memo)
    db_session.flush()

    repo = MemoRepository(db_session)
    assert repo.get(memo_id=memo.id, user_id=other.id) is None


def test_create_without_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = MemoRepository(db_session)

    memo = repo.create(
        user_id=user.id,
        title="t",
        body="b",
        is_pinned=True,
        tags=[],
    )
    db_session.flush()

    assert memo.id is not None
    assert memo.title == "t"
    assert memo.body == "b"
    assert memo.is_pinned is True
    assert memo.tags == []


def test_create_with_tags_inserts_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    repo = MemoRepository(db_session)

    memo = repo.create(
        user_id=user.id,
        title="t",
        body=None,
        is_pinned=False,
        tags=[tag_b, tag_a],
    )
    db_session.flush()

    # 中間テーブルに2件入っている
    assert db_session.query(MemoTag).filter_by(memo_id=memo.id).count() == 2
    assert {t.id for t in memo.tags} == {tag_a.id, tag_b.id}


def test_get_returns_tags_in_name_order(db_session: Session) -> None:
    """relationship の `order_by` は SELECT 時に効くので、`get()` 経由で確認する。"""
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    tag_c = _make_tag(db_session, user, "c")
    repo = MemoRepository(db_session)

    memo = repo.create(
        user_id=user.id,
        title="t",
        body=None,
        is_pinned=False,
        tags=[tag_c, tag_a, tag_b],
    )
    db_session.flush()
    db_session.expire(memo)  # キャッシュを捨てて selectinload を強制

    fetched = repo.get(memo_id=memo.id, user_id=user.id)

    assert fetched is not None
    assert [t.name for t in fetched.tags] == ["a", "b", "c"]


def test_replace_updates_fields_and_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    tag_c = _make_tag(db_session, user, "c")
    repo = MemoRepository(db_session)

    memo = repo.create(user_id=user.id, title="old", body="ob", is_pinned=False, tags=[tag_a])
    db_session.flush()

    repo.replace(memo, title="new", body="nb", is_pinned=True, tags=[tag_b, tag_c])
    db_session.flush()

    assert memo.title == "new"
    assert memo.body == "nb"
    assert memo.is_pinned is True
    assert {t.name for t in memo.tags} == {"b", "c"}
    # 旧 memo_tags は消えていて、新しい2件のみ
    assert db_session.query(MemoTag).filter_by(memo_id=memo.id).count() == 2


def test_replace_with_empty_tags_removes_all_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    repo = MemoRepository(db_session)

    memo = repo.create(user_id=user.id, title="t", body=None, is_pinned=False, tags=[tag_a])
    db_session.flush()

    repo.replace(memo, title="t2", body=None, is_pinned=False, tags=[])
    db_session.flush()

    assert memo.tags == []
    assert db_session.query(MemoTag).filter_by(memo_id=memo.id).count() == 0


def test_delete_removes_memo_and_cascades_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = _make_tag(db_session, user, "x")
    repo = MemoRepository(db_session)

    memo = repo.create(user_id=user.id, title="t", body=None, is_pinned=False, tags=[tag])
    db_session.flush()
    memo_id = memo.id

    repo.delete(memo)
    db_session.flush()

    assert db_session.get(Memo, memo_id) is None
    assert db_session.query(MemoTag).filter_by(memo_id=memo_id).count() == 0
    # タグ本体は残る
    assert db_session.get(Tag, tag.id) is not None


def test_update_pinned_changes_flag_and_updated_at(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = MemoRepository(db_session)
    memo = repo.create(user_id=user.id, title="t", body=None, is_pinned=False, tags=[])
    db_session.flush()

    # savepoint 内では func.now() が固定値のため、onupdate の効きを検証するには
    # 一度 raw SQL で過去日に backdate しておく必要がある。
    past = datetime.now(UTC) - timedelta(days=1)
    db_session.execute(
        text("UPDATE memos SET updated_at = :ts WHERE id = :id"),
        {"ts": past, "id": memo.id},
    )
    db_session.expire(memo)
    db_session.refresh(memo)
    before = memo.updated_at

    repo.update_pinned(memo, is_pinned=True)
    db_session.flush()
    db_session.refresh(memo)

    assert memo.is_pinned is True
    assert memo.updated_at > before


def test_find_user_tags_returns_matching_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    repo = MemoRepository(db_session)

    found = repo.find_user_tags(user_id=user.id, tag_ids=[tag_a.id, tag_b.id])

    assert {t.id for t in found} == {tag_a.id, tag_b.id}


def test_find_user_tags_excludes_other_users_tags(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    tag_own = _make_tag(db_session, owner, "own")
    tag_other = _make_tag(db_session, other, "other_tag")
    repo = MemoRepository(db_session)

    found = repo.find_user_tags(user_id=owner.id, tag_ids=[tag_own.id, tag_other.id])

    assert [t.id for t in found] == [tag_own.id]


def test_find_user_tags_excludes_nonexistent_ids(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = _make_tag(db_session, user, "x")
    repo = MemoRepository(db_session)

    found = repo.find_user_tags(user_id=user.id, tag_ids=[tag.id, uuid4()])

    assert [t.id for t in found] == [tag.id]


def test_find_user_tags_with_empty_input_returns_empty(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = MemoRepository(db_session)

    assert repo.find_user_tags(user_id=user.id, tag_ids=[]) == []
