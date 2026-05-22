"""ProfileService のテスト。"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import UserProfile
from app.schemas.profile import ProfileUpdate
from app.services.profile_service import ProfileService


def _make_user(db: Session, display_name: str = "しん") -> UserProfile:
    user = UserProfile(display_name=display_name)
    db.add(user)
    db.flush()
    return user


def test_get_profile_returns_existing(db_session: Session) -> None:
    user = _make_user(db_session)
    service = ProfileService(db_session)

    fetched = service.get_profile(user_id=user.id)

    assert fetched.id == user.id


def test_get_profile_raises_not_found(db_session: Session) -> None:
    service = ProfileService(db_session)
    with pytest.raises(NotFoundError):
        service.get_profile(user_id=uuid4())


def test_update_profile_replaces_fields(db_session: Session) -> None:
    user = _make_user(db_session, "旧")
    service = ProfileService(db_session)

    updated = service.update_profile(
        user_id=user.id,
        payload=ProfileUpdate(display_name="新", bio="自己紹介", avatar_url="https://e/a.png"),
    )

    assert updated.display_name == "新"
    assert updated.bio == "自己紹介"
    assert updated.avatar_url == "https://e/a.png"


def test_update_profile_can_clear_optional_to_none(db_session: Session) -> None:
    user = _make_user(db_session)
    user.bio = "旧"
    user.avatar_url = "https://e/a.png"
    db_session.flush()
    service = ProfileService(db_session)

    updated = service.update_profile(
        user_id=user.id,
        payload=ProfileUpdate(display_name="しん"),  # bio/avatar_url 省略 → None
    )

    assert updated.bio is None
    assert updated.avatar_url is None


def test_update_profile_raises_not_found_for_unknown_id(db_session: Session) -> None:
    service = ProfileService(db_session)
    with pytest.raises(NotFoundError):
        service.update_profile(
            user_id=uuid4(),
            payload=ProfileUpdate(display_name="x"),
        )
