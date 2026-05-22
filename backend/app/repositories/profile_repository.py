"""ProfileRepository — user_profiles テーブルへのDB操作。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserProfile


class ProfileRepository:
    """プロフィールの永続化操作。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, *, user_id: UUID) -> UserProfile | None:
        """指定ユーザーのプロフィールを取得。存在しなければ None。"""
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        return self._session.scalars(stmt).first()

    def update(
        self,
        profile: UserProfile,
        *,
        display_name: str,
        bio: str | None,
        avatar_url: str | None,
    ) -> UserProfile:
        """プロフィールを全置換更新する。flush/commit は呼び出し側の責務。"""
        profile.display_name = display_name
        profile.bio = bio
        profile.avatar_url = avatar_url
        return profile
