"""タグ Pydantic スキーマのバリデーションテスト。"""

import pytest
from pydantic import ValidationError

from app.schemas.tag import TagCreate, TagUpdate


def test_tag_create_accepts_1_char_name() -> None:
    schema = TagCreate(name="a")
    assert schema.name == "a"


def test_tag_create_accepts_20_char_name() -> None:
    name = "a" * 20
    schema = TagCreate(name=name)
    assert schema.name == name


def test_tag_create_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        TagCreate(name="")


def test_tag_create_rejects_21_char_name() -> None:
    with pytest.raises(ValidationError):
        TagCreate(name="a" * 21)


def test_tag_update_accepts_1_char_name() -> None:
    schema = TagUpdate(name="b")
    assert schema.name == "b"


def test_tag_update_rejects_21_char_name() -> None:
    with pytest.raises(ValidationError):
        TagUpdate(name="a" * 21)


def test_tag_create_strips_surrounding_whitespace() -> None:
    """前後の空白はトリムされる。"""
    schema = TagCreate(name="  仕事  ")
    assert schema.name == "仕事"


def test_tag_create_strips_tab_and_newline() -> None:
    """タブや改行もトリムされる。"""
    schema = TagCreate(name="\t仕事\n")
    assert schema.name == "仕事"


def test_tag_create_rejects_whitespace_only_name() -> None:
    """空白のみの入力はバリデーションエラー。"""
    with pytest.raises(ValidationError):
        TagCreate(name="   ")


def test_tag_create_rejects_tab_only_name() -> None:
    with pytest.raises(ValidationError):
        TagCreate(name="\t\n ")


def test_tag_create_max_length_applies_after_strip() -> None:
    """前後空白を除いた本体が20文字以内ならOK。"""
    name = "a" * 20
    schema = TagCreate(name=f"  {name}  ")
    assert schema.name == name


def test_tag_create_max_length_rejects_21_chars_after_strip() -> None:
    """前後空白を除いた本体が21文字なら拒否。"""
    with pytest.raises(ValidationError):
        TagCreate(name=f"  {'a' * 21}  ")


def test_tag_update_strips_surrounding_whitespace() -> None:
    schema = TagUpdate(name="  新  ")
    assert schema.name == "新"


def test_tag_update_rejects_whitespace_only_name() -> None:
    with pytest.raises(ValidationError):
        TagUpdate(name="   ")
