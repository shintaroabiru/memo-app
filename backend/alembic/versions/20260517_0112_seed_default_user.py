"""seed_default_user

Revision ID: 71611558cc7c
Revises: b88a4775d238
Create Date: 2026-05-17 01:12:57.799099

フェーズ1用の仮ユーザーを投入する。
固定UUID は app.core.config.Settings.default_user_id と一致させる。
"""

from collections.abc import Sequence

from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from alembic import op

revision: str = "71611558cc7c"
down_revision: str | Sequence[str] | None = "b88a4775d238"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.execute(
        text(
            """
            INSERT INTO user_profiles (id, display_name, bio, created_at, updated_at)
            VALUES (:id, :display_name, :bio, now(), now())
            ON CONFLICT (id) DO NOTHING
            """
        ).bindparams(
            bindparam("id", value=DEFAULT_USER_ID, type_=PGUUID(as_uuid=False)),
            bindparam("display_name", value="デフォルトユーザー", type_=String(50)),
            bindparam("bio", value="フェーズ1用の仮ユーザーです", type_=String(200)),
        )
    )


def downgrade() -> None:
    op.execute(
        text("DELETE FROM user_profiles WHERE id = :id").bindparams(
            bindparam("id", value=DEFAULT_USER_ID, type_=PGUUID(as_uuid=False)),
        )
    )
