"""タグモデル。"""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin

# (user_id, name) の UNIQUE 制約名。制約定義と例外判定の両方で参照するので定数化。
# モジュール内のローカル詳細として閉じ込め、外部は Tag.is_user_name_unique_violation を使う。
_UQ_TAGS_USER_NAME = "uq_tags_user_name"


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name=_UQ_TAGS_USER_NAME),
        Index("idx_tags_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)

    @staticmethod
    def is_user_name_unique_violation(exc: IntegrityError) -> bool:
        """`(user_id, name)` の UNIQUE 制約違反かどうかを判定する。

        psycopg は IntegrityError の `orig.diag.constraint_name` に
        違反した制約名を入れてくれる。これが一致するときだけ
        Service 層が ConflictError へ変換する。
        """
        orig = getattr(exc, "orig", None)
        diag = getattr(orig, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None)
        return constraint_name == _UQ_TAGS_USER_NAME
