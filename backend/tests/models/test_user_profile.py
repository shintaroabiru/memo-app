from sqlalchemy.orm import Session

from app.models import UserProfile


def test_create_user_profile_with_minimum_fields(db_session: Session) -> None:
    """display_name のみでUserProfileを作成でき、idと時刻が自動採番される。"""
    user = UserProfile(display_name="しん")
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert user.display_name == "しん"
    assert user.bio is None
    assert user.avatar_url is None
    assert user.created_at is not None
    assert user.updated_at is not None


def test_create_user_profile_with_all_fields(db_session: Session) -> None:
    user = UserProfile(
        display_name="しん",
        bio="AIアプリエンジニア",
        avatar_url="https://example.com/avatar.png",
    )
    db_session.add(user)
    db_session.flush()

    assert user.bio == "AIアプリエンジニア"
    assert user.avatar_url == "https://example.com/avatar.png"
