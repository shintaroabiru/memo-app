"""タグAPIエンドポイント。

Service層は SQLAlchemy の ORM オブジェクトを返すが、エンドポイントでは
明示的な変換をせずそのまま返す。`response_model` と `TagRead` 側の
`from_attributes=True` により、FastAPI が1回だけ Pydantic にシリアライズする。
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_session
from app.schemas.tag import TagCreate, TagListResponse, TagRead, TagUpdate
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])

SessionDep = Annotated[Session, Depends(get_session)]
UserIdDep = Annotated[UUID, Depends(get_current_user_id)]


@router.get("", response_model=TagListResponse)
def list_tags(session: SessionDep, user_id: UserIdDep) -> TagListResponse:
    return {"items": TagService(session).list_tags(user_id=user_id)}


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(body: TagCreate, session: SessionDep, user_id: UserIdDep) -> TagRead:
    return TagService(session).create_tag(user_id=user_id, name=body.name)


@router.put("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: UUID,
    body: TagUpdate,
    session: SessionDep,
    user_id: UserIdDep,
) -> TagRead:
    return TagService(session).rename_tag(user_id=user_id, tag_id=tag_id, name=body.name)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: UUID, session: SessionDep, user_id: UserIdDep) -> Response:
    TagService(session).delete_tag(user_id=user_id, tag_id=tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
