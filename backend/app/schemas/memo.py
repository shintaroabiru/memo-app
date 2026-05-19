"""メモの Pydantic スキーマ。

文字列入力（`title`）は requirements.md §2.0 の共通規則に従い
`BeforeValidator` で前後空白をトリムしてから長さ制約を適用する。
本文 `body` は仕様上トリムしない（末尾改行の保持など）。
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

TITLE_MIN_LENGTH = 1
TITLE_MAX_LENGTH = 100
BODY_MAX_LENGTH = 10000
TAG_IDS_MAX_COUNT = 10


def _strip_str(value: object) -> object:
    """文字列なら前後空白をトリム。空白のみは min_length=1 で弾かれる。"""
    return value.strip() if isinstance(value, str) else value


Title = Annotated[
    str,
    BeforeValidator(_strip_str),
    Field(min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH),
]


class TagBrief(BaseModel):
    """メモに含まれるタグの簡易情報。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class MemoCreate(BaseModel):
    """メモ作成リクエスト。

    PUT による全置換更新でも同じスキーマを流用する（部分更新ではない）。
    """

    title: Title
    body: str | None = Field(default=None, max_length=BODY_MAX_LENGTH)
    tag_ids: list[UUID] = Field(default_factory=list, max_length=TAG_IDS_MAX_COUNT)
    is_pinned: bool = False

    @field_validator("tag_ids")
    @classmethod
    def _no_duplicate_tag_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("重複したタグIDが含まれています")
        return value


class MemoRead(BaseModel):
    """メモ詳細レスポンス。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str | None
    is_pinned: bool
    tags: list[TagBrief]
    created_at: datetime
    updated_at: datetime


class MemoPinUpdate(BaseModel):
    """ピン留めトグルのリクエストボディ。"""

    is_pinned: bool


class MemoPinResponse(BaseModel):
    """ピン留めトグルのレスポンス（id / is_pinned / updated_at のみ返す）。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_pinned: bool
    updated_at: datetime
