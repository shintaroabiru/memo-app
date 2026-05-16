from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Memo, UserProfile


def _make_user(db: Session) -> UserProfile:
    user = UserProfile(display_name="しん")
    db.add(user)
    db.flush()
    return user


def test_create_memo_with_minimum_fields(db_session: Session) -> None:
    """title と user_id だけでメモを作成でき、is_pinned はデフォルト False。"""
    user = _make_user(db_session)
    memo = Memo(user_id=user.id, title="買い物リスト")
    db_session.add(memo)
    db_session.flush()

    assert memo.id is not None
    assert memo.title == "買い物リスト"
    assert memo.body is None
    assert memo.is_pinned is False
    assert memo.created_at is not None
    assert memo.updated_at is not None


def test_create_memo_with_all_fields(db_session: Session) -> None:
    user = _make_user(db_session)
    memo = Memo(
        user_id=user.id,
        title="今日の振り返り",
        body="TDDを実践した",
        is_pinned=True,
    )
    db_session.add(memo)
    db_session.flush()

    assert memo.body == "TDDを実践した"
    assert memo.is_pinned is True


def test_memo_requires_existing_user(db_session: Session) -> None:
    """存在しない user_id でメモを作成するとFK違反になる。"""
    memo = Memo(user_id=uuid4(), title="孤児メモ")
    db_session.add(memo)
    with pytest.raises(IntegrityError):
        db_session.flush()
