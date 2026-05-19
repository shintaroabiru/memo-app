"""メモ Pydantic スキーマのバリデーションテスト。"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.memo import MemoCreate, MemoListQuery, MemoPinUpdate


def test_memo_create_accepts_minimum_payload() -> None:
    schema = MemoCreate(title="買い物")
    assert schema.title == "買い物"
    assert schema.body is None
    assert schema.tag_ids == []
    assert schema.is_pinned is False


def test_memo_create_strips_title_whitespace() -> None:
    schema = MemoCreate(title="  振り返り  ")
    assert schema.title == "振り返り"


def test_memo_create_rejects_whitespace_only_title() -> None:
    with pytest.raises(ValidationError):
        MemoCreate(title="   ")


def test_memo_create_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        MemoCreate(title="")


def test_memo_create_accepts_100_char_title_after_strip() -> None:
    schema = MemoCreate(title=" " + "a" * 100 + " ")
    assert len(schema.title) == 100


def test_memo_create_rejects_101_char_title_after_strip() -> None:
    with pytest.raises(ValidationError):
        MemoCreate(title="a" * 101)


def test_memo_create_accepts_10000_char_body() -> None:
    schema = MemoCreate(title="t", body="a" * 10000)
    assert schema.body is not None
    assert len(schema.body) == 10000


def test_memo_create_rejects_10001_char_body() -> None:
    with pytest.raises(ValidationError):
        MemoCreate(title="t", body="a" * 10001)


def test_memo_create_allows_omitted_body() -> None:
    schema = MemoCreate(title="t")
    assert schema.body is None


def test_memo_create_accepts_up_to_10_tag_ids() -> None:
    tag_ids = [uuid4() for _ in range(10)]
    schema = MemoCreate(title="t", tag_ids=tag_ids)
    assert len(schema.tag_ids) == 10


def test_memo_create_rejects_11_tag_ids() -> None:
    tag_ids = [uuid4() for _ in range(11)]
    with pytest.raises(ValidationError):
        MemoCreate(title="t", tag_ids=tag_ids)


def test_memo_create_rejects_duplicate_tag_ids() -> None:
    dup = uuid4()
    with pytest.raises(ValidationError):
        MemoCreate(title="t", tag_ids=[dup, dup])


def test_memo_create_duplicate_tag_ids_message_has_no_value_error_prefix() -> None:
    """重複エラーのメッセージは Pydantic デフォルトの "Value error, " 前置きを含まない。"""
    dup = uuid4()
    with pytest.raises(ValidationError) as exc_info:
        MemoCreate(title="t", tag_ids=[dup, dup])

    msgs = [err["msg"] for err in exc_info.value.errors() if err["loc"] == ("tag_ids",)]
    assert msgs == ["重複したタグIDが含まれています"]


def test_memo_create_rejects_invalid_uuid_in_tag_ids() -> None:
    with pytest.raises(ValidationError):
        MemoCreate(title="t", tag_ids=["not-a-uuid"])


def test_memo_create_is_pinned_defaults_to_false() -> None:
    schema = MemoCreate(title="t")
    assert schema.is_pinned is False


def test_memo_pin_update_requires_is_pinned() -> None:
    schema = MemoPinUpdate(is_pinned=True)
    assert schema.is_pinned is True

    with pytest.raises(ValidationError):
        MemoPinUpdate()  # type: ignore[call-arg]


def test_memo_list_query_defaults() -> None:
    q = MemoListQuery()
    assert q.q is None
    assert q.tag_ids == []
    assert q.pinned is None
    assert q.limit == 20
    assert q.offset == 0


def test_memo_list_query_accepts_limit_1_to_100() -> None:
    assert MemoListQuery(limit=1).limit == 1
    assert MemoListQuery(limit=100).limit == 100


def test_memo_list_query_rejects_limit_0() -> None:
    with pytest.raises(ValidationError):
        MemoListQuery(limit=0)


def test_memo_list_query_rejects_limit_101() -> None:
    with pytest.raises(ValidationError):
        MemoListQuery(limit=101)


def test_memo_list_query_accepts_offset_0_and_positive() -> None:
    assert MemoListQuery(offset=0).offset == 0
    assert MemoListQuery(offset=1000).offset == 1000


def test_memo_list_query_rejects_negative_offset() -> None:
    with pytest.raises(ValidationError):
        MemoListQuery(offset=-1)


def test_memo_list_query_accepts_uuid_tag_ids() -> None:
    ids = [uuid4(), uuid4()]
    q = MemoListQuery(tag_ids=ids)
    assert q.tag_ids == ids


def test_memo_list_query_rejects_invalid_uuid() -> None:
    with pytest.raises(ValidationError):
        MemoListQuery(tag_ids=["not-a-uuid"])  # type: ignore[list-item]


def test_memo_list_query_accepts_pinned_bool() -> None:
    assert MemoListQuery(pinned=True).pinned is True
    assert MemoListQuery(pinned=False).pinned is False
