"""MemoRepository — memos / memo_tags テーブルへのDB操作。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, distinct, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Memo, MemoTag, Tag

# ILIKE のメタ文字。`\` を先頭にして二重エスケープを防ぐ
# （先に `%` を `\%` に置換した後で `\` を `\\` に置換すると `\%` -> `\\%` になってしまう）。
_ILIKE_SPECIAL_CHARS = ("\\", "%", "_")


def _escape_ilike(value: str) -> str:
    """ILIKE のメタ文字 (`\\`, `%`, `_`) を `\\` でエスケープしてリテラル化する。"""
    for ch in _ILIKE_SPECIAL_CHARS:
        value = value.replace(ch, f"\\{ch}")
    return value


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

    def search(
        self,
        *,
        user_id: UUID,
        q: str | None,
        tag_ids: list[UUID],
        pinned: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Memo], int]:
        """検索条件にマッチするメモのリストと総件数を返す。

        - キーワード `q`: タイトル + 本文の ILIKE 部分一致（大小無視）
        - `tag_ids`: AND 条件（全タグを含むメモのみ。`db-schema.md` §5.3 準拠）
        - `pinned=True` のみピン留めを絞り込み、`None` / `False` の指定はフィルタなし
        - ソートは `is_pinned DESC, updated_at DESC, id DESC` で安定化
        - `selectinload(Memo.tags)` で N+1 を避け、tags はリレーションの order_by で name 昇順
        - `total` はページング適用前の全件数
        """
        base_filter = self._build_filter(user_id=user_id, q=q, tag_ids=tag_ids, pinned=pinned)

        total = self._session.scalar(select(func.count(Memo.id)).where(*base_filter)) or 0

        items_stmt = (
            select(Memo)
            .where(*base_filter)
            .order_by(
                Memo.is_pinned.desc(),
                Memo.updated_at.desc(),
                Memo.id.desc(),
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(Memo.tags))
        )
        items = list(self._session.scalars(items_stmt).all())
        return items, total

    def _build_filter(
        self,
        *,
        user_id: UUID,
        q: str | None,
        tag_ids: list[UUID],
        pinned: bool | None,
    ) -> list:
        """search の COUNT / SELECT 両方で使う WHERE 条件を組み立てる。"""
        conditions: list = [Memo.user_id == user_id]

        if q:
            pattern = f"%{_escape_ilike(q)}%"
            # `escape="\\"` で PostgreSQL に「`\` がメタ文字のエスケープ」と伝える
            conditions.append(
                or_(
                    Memo.title.ilike(pattern, escape="\\"),
                    Memo.body.ilike(pattern, escape="\\"),
                )
            )

        if tag_ids:
            conditions.append(Memo.id.in_(self._memo_ids_having_all_tags(tag_ids)))

        if pinned is True:
            conditions.append(Memo.is_pinned.is_(True))

        return conditions

    @staticmethod
    def _memo_ids_having_all_tags(tag_ids: list[UUID]) -> Select[tuple[UUID]]:
        """指定タグを **すべて** 持つメモIDを返すサブクエリ。db-schema.md §5.3 準拠。"""
        unique_ids = list(set(tag_ids))
        return (
            select(MemoTag.memo_id)
            .where(MemoTag.tag_id.in_(unique_ids))
            .group_by(MemoTag.memo_id)
            .having(func.count(distinct(MemoTag.tag_id)) == len(unique_ids))
        )
