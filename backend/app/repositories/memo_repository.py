"""MemoRepository — memos / memo_tags テーブルへのDB操作。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Memo, Tag


class MemoRepository:
    """メモの永続化操作。`memo_tags` は SQLAlchemy のリレーション越しに扱う。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, *, memo_id: UUID, user_id: UUID) -> Memo | None:
        """指定ユーザーが所有するメモを取得。他ユーザーのメモは None。"""
        stmt = (
            select(Memo)
            .where(Memo.id == memo_id, Memo.user_id == user_id)
            .options(selectinload(Memo.tags))
        )
        return self._session.scalars(stmt).first()

    def create(
        self,
        *,
        user_id: UUID,
        title: str,
        body: str | None,
        is_pinned: bool,
        tags: list[Tag],
    ) -> Memo:
        """新規メモを追加し、`memo_tags` も同時に張る。flush/commit は呼び出し側の責務。"""
        memo = Memo(
            user_id=user_id,
            title=title,
            body=body,
            is_pinned=is_pinned,
        )
        memo.tags = list(tags)
        self._session.add(memo)
        return memo

    def replace(
        self,
        memo: Memo,
        *,
        title: str,
        body: str | None,
        is_pinned: bool,
        tags: list[Tag],
    ) -> Memo:
        """メモを全置換更新する。`memo.tags = [...]` で memo_tags も差し替えられる。"""
        memo.title = title
        memo.body = body
        memo.is_pinned = is_pinned
        memo.tags = list(tags)
        return memo

    def delete(self, memo: Memo) -> None:
        """メモを物理削除する。関連する memo_tags は CASCADE で消える。"""
        self._session.delete(memo)

    def update_pinned(self, memo: Memo, *, is_pinned: bool) -> Memo:
        """ピン留めフラグだけを更新する（`updated_at` は TimestampMixin で自動更新）。"""
        memo.is_pinned = is_pinned
        return memo

    def find_user_tags(self, *, user_id: UUID, tag_ids: list[UUID]) -> list[Tag]:
        """指定IDのうち、ユーザーが所有するタグだけを返す。存在/権限の検証用。"""
        if not tag_ids:
            return []
        stmt = select(Tag).where(Tag.user_id == user_id, Tag.id.in_(tag_ids))
        return list(self._session.scalars(stmt).all())
