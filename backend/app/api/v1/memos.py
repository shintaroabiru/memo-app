"""メモAPIエンドポイント。

Service層は SQLAlchemy の ORM オブジェクトを返すが、エンドポイントでは
明示的な変換をせずそのまま返す。`response_model` と `from_attributes=True`
により FastAPI が 1 回だけ Pydantic にシリアライズする。
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_session
from app.schemas.memo import MemoCreate, MemoPinResponse, MemoPinUpdate, MemoRead
from app.services.memo_service import MemoService

router = APIRouter(prefix="/memos", tags=["memos"])

SessionDep = Annotated[Session, Depends(get_session)]
UserIdDep = Annotated[UUID, Depends(get_current_user_id)]


@router.get("/{memo_id}", response_model=MemoRead)
def get_memo(memo_id: UUID, session: SessionDep, user_id: UserIdDep) -> MemoRead:
    return MemoService(session).get_memo(user_id=user_id, memo_id=memo_id)


@router.post("", response_model=MemoRead, status_code=status.HTTP_201_CREATED)
def create_memo(body: MemoCreate, session: SessionDep, user_id: UserIdDep) -> MemoRead:
    return MemoService(session).create_memo(user_id=user_id, payload=body)


@router.put("/{memo_id}", response_model=MemoRead)
def update_memo(
    memo_id: UUID,
    body: MemoCreate,
    session: SessionDep,
    user_id: UserIdDep,
) -> MemoRead:
    return MemoService(session).update_memo(user_id=user_id, memo_id=memo_id, payload=body)


@router.delete("/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memo(memo_id: UUID, session: SessionDep, user_id: UserIdDep) -> Response:
    MemoService(session).delete_memo(user_id=user_id, memo_id=memo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{memo_id}/pin", response_model=MemoPinResponse)
def toggle_pin(
    memo_id: UUID,
    body: MemoPinUpdate,
    session: SessionDep,
    user_id: UserIdDep,
) -> MemoPinResponse:
    return MemoService(session).toggle_pin(
        user_id=user_id, memo_id=memo_id, is_pinned=body.is_pinned
    )
