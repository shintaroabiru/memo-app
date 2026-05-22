"""プロフィールの Pydantic スキーマ。

`display_name` は requirements.md §2.0 の共通規則に従い `BeforeValidator(strip_str)`
で前後空白をトリムし、空白のみは `min_length=1` で 400 を返す。
`bio` / `avatar_url` は **空文字列を null に正規化** する（`strip_or_none`）。
クライアントが空欄を `""` で送っても `null` で送っても DB 表現は単一の `null` に揃える。
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.schemas._validators import strip_or_none, strip_str

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


class ProfileUpdate(BaseModel):
    """プロフィール更新リクエスト（全置換）。"""

    display_name: DisplayName
    # `Field(max_length=...)` を `str | None` に直接付けると None 値で TypeError になるため、
    # 内側の Annotated で str にだけ max_length を付与し、外側で BeforeValidator を適用する。
    bio: Annotated[
        Annotated[str, Field(max_length=BIO_MAX_LENGTH)] | None,
        BeforeValidator(strip_or_none),
    ] = None
    avatar_url: Annotated[
        Annotated[str, Field(max_length=AVATAR_URL_MAX_LENGTH)] | None,
        BeforeValidator(strip_or_none),
    ] = None


class ProfileRead(BaseModel):
    """プロフィール取得レスポンス。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
