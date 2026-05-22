"""プロフィールの Pydantic スキーマ。

全フィールドは requirements.md §2.0 の共通規則に従い `BeforeValidator(strip_str)`
で前後空白をトリムする。`bio` / `avatar_url` は空文字列を許可する（フィールド表に明記）。
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.schemas._validators import strip_str

DISPLAY_NAME_MIN_LENGTH = 1
DISPLAY_NAME_MAX_LENGTH = 50
BIO_MAX_LENGTH = 200
# 一般的なブラウザ・サーバが許容する URL の長さ目安。avatar_url の上限として採用。
AVATAR_URL_MAX_LENGTH = 2048


DisplayName = Annotated[
    str,
    BeforeValidator(strip_str),
    Field(min_length=DISPLAY_NAME_MIN_LENGTH, max_length=DISPLAY_NAME_MAX_LENGTH),
]

# 任意・空文字列許可の文字列フィールド型。トリムは適用、min_length は設けない。
OptionalStrippedStr = Annotated[str, BeforeValidator(strip_str)]


class ProfileUpdate(BaseModel):
    """プロフィール更新リクエスト（全置換）。"""

    display_name: DisplayName
    bio: Annotated[OptionalStrippedStr, Field(max_length=BIO_MAX_LENGTH)] | None = None
    avatar_url: Annotated[OptionalStrippedStr, Field(max_length=AVATAR_URL_MAX_LENGTH)] | None = (
        None
    )


class ProfileRead(BaseModel):
    """プロフィール取得レスポンス。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
