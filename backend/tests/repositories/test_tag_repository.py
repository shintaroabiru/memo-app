"""TagRepository のテスト（テスト用Postgresに対する実DB操作）。"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Memo, MemoTag, Tag, UserProfile
from app.repositories.tag_repository import TagRepository


def _make_user(db: Session, display_name: str = "テストユーザー") -> UserProfile:
    user = UserProfile(display_name=display_name)
    db.add(user)
    db.flush()
    return user


def test_list_by_user_returns_tags_sorted_by_name(db_session: Session) -> None:
    user = _make_user(db_session)
    db_session.add_all(
        [
            Tag(user_id=user.id, name="仕事"),
            Tag(user_id=user.id, name="あ"),
            Tag(user_id=user.id, name="メモ"),
        ]
    )
    db_session.flush()

    repo = TagRepository(db_session)
    tags = repo.list_by_user(user.id)

    assert [t.name for t in tags] == sorted(["仕事", "あ", "メモ"])


def test_list_by_user_isolates_other_users(db_session: Session) -> None:
    user_a = _make_user(db_session, "A")
    user_b = _make_user(db_session, "B")
    db_session.add_all(
        [
            Tag(user_id=user_a.id, name="A1"),
            Tag(user_id=user_b.id, name="B1"),
        ]
    )
    db_session.flush()

    repo = TagRepository(db_session)
    a_tags = repo.list_by_user(user_a.id)

    assert [t.name for t in a_tags] == ["A1"]


def test_create_inserts_new_tag(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = TagRepository(db_session)

    tag = repo.create(user_id=user.id, name="新規")
    db_session.flush()

    assert tag.id is not None
    assert tag.name == "新規"
    assert tag.user_id == user.id


def test_create_raises_integrity_error_on_duplicate(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = TagRepository(db_session)
    repo.create(user_id=user.id, name="重複")
    db_session.flush()

    repo.create(user_id=user.id, name="重複")
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_get_returns_tag_for_owner(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = Tag(user_id=user.id, name="own")
    db_session.add(tag)
    db_session.flush()

    repo = TagRepository(db_session)
    found = repo.get(tag_id=tag.id, user_id=user.id)

    assert found is not None
    assert found.id == tag.id


def test_get_returns_none_for_other_user(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    tag = Tag(user_id=owner.id, name="x")
    db_session.add(tag)
    db_session.flush()

    repo = TagRepository(db_session)
    assert repo.get(tag_id=tag.id, user_id=other.id) is None


def test_update_renames_tag(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = Tag(user_id=user.id, name="旧")
    db_session.add(tag)
    db_session.flush()

    repo = TagRepository(db_session)
    repo.update(tag, name="新")
    db_session.flush()

    assert tag.name == "新"


def test_update_raises_integrity_error_on_duplicate(db_session: Session) -> None:
    user = _make_user(db_session)
    db_session.add_all(
        [
            Tag(user_id=user.id, name="A"),
            Tag(user_id=user.id, name="B"),
        ]
    )
    db_session.flush()
    target = db_session.query(Tag).filter_by(user_id=user.id, name="B").one()

    repo = TagRepository(db_session)
    repo.update(target, name="A")
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_delete_removes_tag_and_cascades_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = Tag(user_id=user.id, name="t")
    memo = Memo(user_id=user.id, title="m")
    db_session.add_all([tag, memo])
    db_session.flush()
    db_session.add(MemoTag(memo_id=memo.id, tag_id=tag.id))
    db_session.flush()

    repo = TagRepository(db_session)
    repo.delete(tag)
    db_session.flush()

    assert db_session.get(Tag, tag.id) is None
    # メモ本体は残り、memo_tags のみCASCADEで消える
    assert db_session.get(Memo, memo.id) is not None
    remaining = db_session.query(MemoTag).filter_by(tag_id=tag.id).all()
    assert remaining == []
