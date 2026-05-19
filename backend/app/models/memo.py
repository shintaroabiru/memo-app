"""メモモデル。"""

from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.tag import Tag


class Memo(Base, TimestampMixin):
    __tablename__ = "memos"
    __table_args__ = (
        Index("idx_memos_user_id", "user_id"),
        Index(
            "idx_memos_user_pinned_updated",
            "user_id",
            "is_pinned",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # memo_tags 中間テーブルを介した多対多。`memo.tags = [...]` で全置換できる。
    # API レスポンス用に name 昇順で取得する（api-spec.md §2.1-2.2）。
    tags: Mapped[list[Tag]] = relationship(
        secondary="memo_tags",
        order_by=Tag.name.asc(),
    )
