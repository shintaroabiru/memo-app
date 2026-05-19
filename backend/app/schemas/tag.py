"""タグの Pydantic スキーマ。"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.schemas._validators import strip_str

TAG_NAME_MIN_LENGTH = 1
TAG_NAME_MAX_LENGTH = 20


# 前後の空白をトリムしてから長さ制約を適用するタグ名の型。
# `BeforeValidator` で先に strip するため、`"   "` は `""` に正規化されて
# `min_length=1` のバリデーションエラーになる。
TagName = Annotated[
    str,
    BeforeValidator(strip_str),
    Field(min_length=TAG_NAME_MIN_LENGTH, max_length=TAG_NAME_MAX_LENGTH),
]


class TagCreate(BaseModel):
    """タグ作成リクエスト。"""

    name: TagName


class TagUpdate(BaseModel):
    """タグ更新リクエスト（リネーム）。"""

    name: TagName


class TagRead(BaseModel):
    """タグ取得レスポンス。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class TagListResponse(BaseModel):
    """タグ一覧レスポンス。"""

    items: list[TagRead]
