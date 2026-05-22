"""プロフィールAPIエンドポイント。

Service層は SQLAlchemy の ORM オブジェクトを返すが、エンドポイントでは
明示的な変換をせずそのまま返す。`response_model` と `from_attributes=True`
により FastAPI が 1 回だけ Pydantic にシリアライズする。
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_session
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])

SessionDep = Annotated[Session, Depends(get_session)]
UserIdDep = Annotated[UUID, Depends(get_current_user_id)]


@router.get("", response_model=ProfileRead)
def get_profile(session: SessionDep, user_id: UserIdDep) -> ProfileRead:
    return ProfileService(session).get_profile(user_id=user_id)


@router.put("", response_model=ProfileRead)
def update_profile(body: ProfileUpdate, session: SessionDep, user_id: UserIdDep) -> ProfileRead:
    return ProfileService(session).update_profile(user_id=user_id, payload=body)
