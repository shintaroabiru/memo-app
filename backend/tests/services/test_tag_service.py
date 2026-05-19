"""TagService のテスト（Repositoryを直接呼ぶ統合テスト寄り）。"""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models import Tag, UserProfile
from app.services.tag_service import TagService


def _make_user(db: Session, display_name: str = "テスト") -> UserProfile:
    user = UserProfile(display_name=display_name)
    db.add(user)
    db.flush()
    return user


def test_list_tags_returns_sorted_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    db_session.add_all(
        [
            Tag(user_id=user.id, name="b"),
            Tag(user_id=user.id, name="a"),
        ]
    )
    db_session.flush()

    service = TagService(db_session)
    result = service.list_tags(user_id=user.id)

    assert [t.name for t in result] == ["a", "b"]


def test_create_tag_returns_new_tag(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)

    tag = service.create_tag(user_id=user.id, name="新規")

    assert tag.id is not None
    assert tag.name == "新規"


def test_create_tag_raises_conflict_on_duplicate(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)
    service.create_tag(user_id=user.id, name="重複")

    with pytest.raises(ConflictError):
        service.create_tag(user_id=user.id, name="重複")


def test_rename_tag_updates_name(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)
    tag = service.create_tag(user_id=user.id, name="旧")

    renamed = service.rename_tag(user_id=user.id, tag_id=tag.id, name="新")

    assert renamed.name == "新"


def test_rename_tag_raises_not_found_when_missing(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)
    other_user = _make_user(db_session, "other")
    tag = service.create_tag(user_id=other_user.id, name="他人のタグ")

    with pytest.raises(NotFoundError):
        service.rename_tag(user_id=user.id, tag_id=tag.id, name="x")


def test_rename_tag_raises_conflict_on_duplicate(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)
    service.create_tag(user_id=user.id, name="A")
    b = service.create_tag(user_id=user.id, name="B")

    with pytest.raises(ConflictError):
        service.rename_tag(user_id=user.id, tag_id=b.id, name="A")


def test_delete_tag_removes_tag(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)
    tag = service.create_tag(user_id=user.id, name="t")

    service.delete_tag(user_id=user.id, tag_id=tag.id)
    db_session.flush()

    assert db_session.get(Tag, tag.id) is None


def test_delete_tag_raises_not_found_when_missing(db_session: Session) -> None:
    user = _make_user(db_session)
    service = TagService(db_session)
    other_user = _make_user(db_session, "other")
    tag = service.create_tag(user_id=other_user.id, name="他人のタグ")

    with pytest.raises(NotFoundError):
        service.delete_tag(user_id=user.id, tag_id=tag.id)


def test_create_tag_propagates_fk_violation_as_integrity_error(db_session: Session) -> None:
    """UNIQUE違反以外のIntegrityError（FK違反など）は ConflictError に丸めず伝播させる。"""
    service = TagService(db_session)
    nonexistent_user_id = uuid4()  # user_profiles に存在しない UUID

    # ConflictError ではなく IntegrityError がそのまま raise されること
    with pytest.raises(IntegrityError):
        service.create_tag(user_id=nonexistent_user_id, name="test")
