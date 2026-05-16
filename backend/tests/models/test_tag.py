import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Tag, UserProfile


def _make_user(db: Session, name: str = "しん") -> UserProfile:
    user = UserProfile(display_name=name)
    db.add(user)
    db.flush()
    return user


def test_create_tag(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = Tag(user_id=user.id, name="仕事")
    db_session.add(tag)
    db_session.flush()

    assert tag.id is not None
    assert tag.name == "仕事"
    assert tag.created_at is not None


def test_tag_name_is_unique_per_user(db_session: Session) -> None:
    """同一ユーザー内では同名タグは作れない。"""
    user = _make_user(db_session)
    db_session.add(Tag(user_id=user.id, name="仕事"))
    db_session.flush()
    db_session.add(Tag(user_id=user.id, name="仕事"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tag_name_can_duplicate_across_users(db_session: Session) -> None:
    """別ユーザーであれば同名タグを作れる。"""
    user_a = _make_user(db_session, name="しんA")
    user_b = _make_user(db_session, name="しんB")
    db_session.add(Tag(user_id=user_a.id, name="仕事"))
    db_session.add(Tag(user_id=user_b.id, name="仕事"))
    db_session.flush()
