"""ProfileRepository のテスト。"""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import UserProfile
from app.repositories.profile_repository import ProfileRepository


def _make_user(db: Session, display_name: str = "しん") -> UserProfile:
    user = UserProfile(display_name=display_name)
    db.add(user)
    db.flush()
    return user


def test_get_returns_existing_profile(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = ProfileRepository(db_session)

    found = repo.get(user_id=user.id)

    assert found is not None
    assert found.id == user.id
    assert found.display_name == "しん"


def test_get_returns_none_for_unknown_id(db_session: Session) -> None:
    repo = ProfileRepository(db_session)
    assert repo.get(user_id=uuid4()) is None


def test_update_replaces_all_fields(db_session: Session) -> None:
    user = _make_user(db_session, "旧")
    repo = ProfileRepository(db_session)

    repo.update(user, display_name="新", bio="自己紹介", avatar_url="https://e/a.png")
    db_session.flush()

    assert user.display_name == "新"
    assert user.bio == "自己紹介"
    assert user.avatar_url == "https://e/a.png"


def test_update_can_clear_optional_fields_to_none(db_session: Session) -> None:
    user = _make_user(db_session)
    user.bio = "旧"
    user.avatar_url = "https://e/a.png"
    db_session.flush()

    repo = ProfileRepository(db_session)
    repo.update(user, display_name="しん", bio=None, avatar_url=None)
    db_session.flush()

    assert user.bio is None
    assert user.avatar_url is None
