"""API層の共通 Depends。

- `get_session`: DBセッションを取得する（`app.core.database.get_session` の再エクスポート）
- `get_current_user_id`: 現在のユーザーIDを取得する
  - フェーズ1では `settings.default_user_id` を返す
  - フェーズ2で認証を入れる際は、この関数の中身だけをトークン検証に差し替える
"""

from __future__ import annotations

from uuid import UUID

from app.core.config import settings
from app.core.database import get_session

__all__ = ["get_current_user_id", "get_session"]


def get_current_user_id() -> UUID:
    """現在のユーザーIDを返す。フェーズ1では仮ユーザーUUID固定。"""
    return settings.default_user_id
