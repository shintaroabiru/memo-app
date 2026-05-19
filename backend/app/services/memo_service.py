"""MemoService — メモのビジネスロジック。HTTPは扱わない。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.models import Memo, Tag
from app.repositories.memo_repository import MemoRepository
from app.schemas.memo import MemoCreate


class MemoService:
    """メモの操作を Repository に委譲しつつ、ビジネスルールを適用する。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = MemoRepository(session)

    def get_memo(self, *, user_id: UUID, memo_id: UUID) -> Memo:
        memo = self._repo.get(memo_id=memo_id, user_id=user_id)
        if memo is None:
            raise NotFoundError(message="メモが見つかりません")
        return memo

    def create_memo(self, *, user_id: UUID, payload: MemoCreate) -> Memo:
        tags = self._resolve_tags(user_id=user_id, tag_ids=payload.tag_ids)
        memo = self._repo.create(
            user_id=user_id,
            title=payload.title,
            body=payload.body,
            is_pinned=payload.is_pinned,
            tags=tags,
        )
        self._session.commit()
        return memo

    def update_memo(self, *, user_id: UUID, memo_id: UUID, payload: MemoCreate) -> Memo:
        memo = self.get_memo(user_id=user_id, memo_id=memo_id)
        tags = self._resolve_tags(user_id=user_id, tag_ids=payload.tag_ids)
        self._repo.replace(
            memo,
            title=payload.title,
            body=payload.body,
            is_pinned=payload.is_pinned,
            tags=tags,
        )
        self._session.commit()
        return memo

    def delete_memo(self, *, user_id: UUID, memo_id: UUID) -> None:
        memo = self.get_memo(user_id=user_id, memo_id=memo_id)
        self._repo.delete(memo)
        self._session.commit()

    def toggle_pin(self, *, user_id: UUID, memo_id: UUID, is_pinned: bool) -> Memo:
        memo = self.get_memo(user_id=user_id, memo_id=memo_id)
        self._repo.update_pinned(memo, is_pinned=is_pinned)
        self._session.commit()
        return memo

    def _resolve_tags(self, *, user_id: UUID, tag_ids: list[UUID]) -> list[Tag]:
        """指定された tag_ids のすべてがユーザー所有であることを確認して Tag を返す。

        存在しない / 他ユーザー所有の ID が1つでもあれば `BadRequestError`。
        スキーマで重複は弾かれているので入力は一意な前提。
        """
        if not tag_ids:
            return []

        found = self._repo.find_user_tags(user_id=user_id, tag_ids=tag_ids)
        if len(found) == len(tag_ids):
            return found

        found_ids = {tag.id for tag in found}
        missing = [str(tid) for tid in tag_ids if tid not in found_ids]
        raise BadRequestError(
            message="指定されたタグIDが無効です",
            details=[
                {
                    "field": "tag_ids",
                    "message": f"存在しないか権限のないタグID: {', '.join(missing)}",
                }
            ],
        )
