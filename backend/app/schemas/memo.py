"""メモの Pydantic スキーマ。

文字列入力（`title`）は requirements.md §2.0 の共通規則に従い
`BeforeValidator` で前後空白をトリムしてから長さ制約を適用する。
本文 `body` は仕様上トリムしない（末尾改行の保持など）。
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas._validators import strip_str

TITLE_MIN_LENGTH = 1
TITLE_MAX_LENGTH = 100
BODY_MAX_LENGTH = 10000
TAG_IDS_MAX_COUNT = 10


Title = Annotated[
    str,
    BeforeValidator(strip_str),
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
        # `ValueError` を raise すると Pydantic がメッセージに "Value error, " を前置するため、
        # クライアントに返す details.message を整えるべく PydanticCustomError を使う。
        if len(value) != len(set(value)):
            raise PydanticCustomError(
                "duplicate_tag_ids",
                "重複したタグIDが含まれています",
            )
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


LIST_LIMIT_DEFAULT = 20
LIST_LIMIT_MAX = 100


class MemoListQuery(BaseModel):
    """メモ一覧/検索のクエリパラメータ。

    `q` は前後空白のトリムや空白のみの扱いを Service 層で正規化する。
    `tag_ids` の AND/OR 条件や `pinned` の解釈は Repository 層に渡す。
    """

    q: str | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    pinned: bool | None = None
    limit: int = Field(default=LIST_LIMIT_DEFAULT, ge=1, le=LIST_LIMIT_MAX)
    offset: int = Field(default=0, ge=0)


class MemoListResponse(BaseModel):
    """メモ一覧/検索のレスポンス。"""

    items: list[MemoRead]
    total: int
    limit: int
    offset: int
