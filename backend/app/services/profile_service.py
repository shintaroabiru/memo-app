"""ProfileService — プロフィールのビジネスロジック。HTTPは扱わない。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import UserProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileUpdate


class ProfileService:
    """プロフィールの操作を Repository に委譲しつつ、ビジネスルールを適用する。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ProfileRepository(session)

    def get_profile(self, *, user_id: UUID) -> UserProfile:
        profile = self._repo.get(user_id=user_id)
        if profile is None:
            raise NotFoundError(message="プロフィールが見つかりません")
        return profile

    def update_profile(self, *, user_id: UUID, payload: ProfileUpdate) -> UserProfile:
        profile = self.get_profile(user_id=user_id)
        self._repo.update(
            profile,
            display_name=payload.display_name,
            bio=payload.bio,
            avatar_url=payload.avatar_url,
        )
        self._session.commit()
        return profile
