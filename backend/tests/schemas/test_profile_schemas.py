"""プロフィール Pydantic スキーマのバリデーションテスト。"""

import pytest
from pydantic import ValidationError

from app.schemas.profile import ProfileUpdate


def test_profile_update_accepts_minimum_payload() -> None:
    schema = ProfileUpdate(display_name="しん")
    assert schema.display_name == "しん"
    assert schema.bio is None
    assert schema.avatar_url is None


def test_profile_update_strips_display_name_whitespace() -> None:
    schema = ProfileUpdate(display_name="  しん  ")
    assert schema.display_name == "しん"


def test_profile_update_rejects_whitespace_only_display_name() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdate(display_name="   ")


def test_profile_update_rejects_empty_display_name() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdate(display_name="")


def test_profile_update_accepts_50_char_display_name_after_strip() -> None:
    name = "a" * 50
    schema = ProfileUpdate(display_name=f"  {name}  ")
    assert schema.display_name == name


def test_profile_update_rejects_51_char_display_name_after_strip() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdate(display_name="a" * 51)


def test_profile_update_accepts_empty_bio() -> None:
    """bio は空文字列を許可（requirements.md §2.0 の例外）。"""
    schema = ProfileUpdate(display_name="しん", bio="")
    assert schema.bio == ""


def test_profile_update_strips_bio_whitespace() -> None:
    schema = ProfileUpdate(display_name="しん", bio="  自己紹介  ")
    assert schema.bio == "自己紹介"


def test_profile_update_accepts_200_char_bio() -> None:
    bio = "a" * 200
    schema = ProfileUpdate(display_name="しん", bio=bio)
    assert schema.bio == bio


def test_profile_update_rejects_201_char_bio() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdate(display_name="しん", bio="a" * 201)


def test_profile_update_allows_omitted_bio() -> None:
    schema = ProfileUpdate(display_name="しん")
    assert schema.bio is None


def test_profile_update_strips_avatar_url() -> None:
    schema = ProfileUpdate(display_name="しん", avatar_url="  https://example.com/a.png  ")
    assert schema.avatar_url == "https://example.com/a.png"


def test_profile_update_allows_omitted_avatar_url() -> None:
    schema = ProfileUpdate(display_name="しん")
    assert schema.avatar_url is None


def test_profile_update_accepts_null_bio_explicitly() -> None:
    schema = ProfileUpdate(display_name="しん", bio=None)
    assert schema.bio is None
