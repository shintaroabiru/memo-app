import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Memo, MemoTag, Tag, UserProfile


def _setup(db: Session) -> tuple[UserProfile, Memo, Tag]:
    user = UserProfile(display_name="しん")
    db.add(user)
    db.flush()
    memo = Memo(user_id=user.id, title="メモ")
    tag = Tag(user_id=user.id, name="仕事")
    db.add_all([memo, tag])
    db.flush()
    return user, memo, tag


def test_create_memo_tag(db_session: Session) -> None:
    _, memo, tag = _setup(db_session)
    db_session.add(MemoTag(memo_id=memo.id, tag_id=tag.id))
    db_session.flush()

    rows = db_session.execute(select(MemoTag)).scalars().all()
    assert len(rows) == 1
    assert rows[0].created_at is not None


def test_memo_tag_composite_pk_prevents_duplicate(db_session: Session) -> None:
    _, memo, tag = _setup(db_session)
    db_session.add(MemoTag(memo_id=memo.id, tag_id=tag.id))
    db_session.flush()
    db_session.add(MemoTag(memo_id=memo.id, tag_id=tag.id))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_memo_delete_cascades_memo_tags(db_session: Session) -> None:
    _, memo, tag = _setup(db_session)
    db_session.add(MemoTag(memo_id=memo.id, tag_id=tag.id))
    db_session.flush()

    db_session.delete(memo)
    db_session.flush()

    assert db_session.execute(select(MemoTag)).first() is None


def test_tag_delete_cascades_memo_tags(db_session: Session) -> None:
    _, memo, tag = _setup(db_session)
    db_session.add(MemoTag(memo_id=memo.id, tag_id=tag.id))
    db_session.flush()

    db_session.delete(tag)
    db_session.flush()

    assert db_session.execute(select(MemoTag)).first() is None
