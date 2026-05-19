"""TagService — タグのビジネスロジック。HTTPは扱わない。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models import Tag
from app.models.tag import UQ_TAGS_USER_NAME
from app.repositories.tag_repository import TagRepository


class TagService:
    """タグの操作を Repository に委譲しつつ、ビジネスルールを適用する。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = TagRepository(session)

    def list_tags(self, *, user_id: UUID) -> list[Tag]:
        return self._repo.list_by_user(user_id)

    def create_tag(self, *, user_id: UUID, name: str) -> Tag:
        tag = self._repo.create(user_id=user_id, name=name)
        self._commit_or_conflict()
        return tag

    def rename_tag(self, *, user_id: UUID, tag_id: UUID, name: str) -> Tag:
        tag = self._repo.get(tag_id=tag_id, user_id=user_id)
        if tag is None:
            raise NotFoundError(message="タグが見つかりません")

        self._repo.update(tag, name=name)
        self._commit_or_conflict()
        return tag

    def delete_tag(self, *, user_id: UUID, tag_id: UUID) -> None:
        tag = self._repo.get(tag_id=tag_id, user_id=user_id)
        if tag is None:
            raise NotFoundError(message="タグが見つかりません")
        self._repo.delete(tag)
        self._session.commit()

    def _commit_or_conflict(self) -> None:
        """commit を試み、tags の UNIQUE 違反なら ConflictError に変換する。

        FK違反など他要因の IntegrityError は ConflictError に丸めず、
        そのまま伝播させて 500 とハンドラに任せる（誤誘導を避けるため）。
        """
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if not _is_tag_unique_violation(exc):
                raise
            raise ConflictError(
                message="同名のタグが既に存在します",
                details=[{"field": "name", "message": "既に登録されています"}],
            ) from exc


def _is_tag_unique_violation(exc: IntegrityError) -> bool:
    """`uq_tags_user_name` の UNIQUE 制約違反かどうかを判定する。

    psycopg は IntegrityError の `orig.diag.constraint_name` に
    違反した制約名を入れてくれる。これが一致するときだけ ConflictError に変換する。
    """
    orig = getattr(exc, "orig", None)
    diag = getattr(orig, "diag", None)
    constraint_name = getattr(diag, "constraint_name", None)
    return constraint_name == UQ_TAGS_USER_NAME
