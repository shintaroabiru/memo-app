"""TagRepository — タグテーブルへのDB操作。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tag


class TagRepository:
    """タグの永続化操作。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: UUID) -> list[Tag]:
        """指定ユーザーのタグを name 昇順で全件返す。"""
        stmt = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
        return list(self._session.scalars(stmt).all())

    def get(self, *, tag_id: UUID, user_id: UUID) -> Tag | None:
        """指定ユーザーが所有するタグを取得。他ユーザーのタグは None。"""
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        return self._session.scalars(stmt).first()

    def create(self, *, user_id: UUID, name: str) -> Tag:
        """新規タグを追加してセッションに乗せる（flush は呼び出し側の責務）。"""
        tag = Tag(user_id=user_id, name=name)
        self._session.add(tag)
        return tag

    def update(self, tag: Tag, *, name: str) -> Tag:
        """タグ名を更新。"""
        tag.name = name
        return tag

    def delete(self, tag: Tag) -> None:
        """タグを物理削除する。関連する memo_tags は CASCADE で消える。"""
        self._session.delete(tag)
