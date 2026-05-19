"""MemoRepository のテスト（実DBでの memos + memo_tags 操作）。"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Memo, MemoTag, Tag, UserProfile
from app.repositories.memo_repository import MemoRepository


def _make_user(db: Session, display_name: str = "テスト") -> UserProfile:
    user = UserProfile(display_name=display_name)
    db.add(user)
    db.flush()
    return user


def _make_tag(db: Session, user: UserProfile, name: str) -> Tag:
    tag = Tag(user_id=user.id, name=name)
    db.add(tag)
    db.flush()
    return tag


def test_get_returns_memo_for_owner(db_session: Session) -> None:
    user = _make_user(db_session)
    memo = Memo(user_id=user.id, title="t")
    db_session.add(memo)
    db_session.flush()

    repo = MemoRepository(db_session)
    found = repo.get(memo_id=memo.id, user_id=user.id)

    assert found is not None
    assert found.id == memo.id


def test_get_returns_none_for_other_user(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    memo = Memo(user_id=owner.id, title="own")
    db_session.add(memo)
    db_session.flush()

    repo = MemoRepository(db_session)
    assert repo.get(memo_id=memo.id, user_id=other.id) is None


def test_create_without_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = MemoRepository(db_session)

    memo = repo.create(
        user_id=user.id,
        title="t",
        body="b",
        is_pinned=True,
        tags=[],
    )
    db_session.flush()

    assert memo.id is not None
    assert memo.title == "t"
    assert memo.body == "b"
    assert memo.is_pinned is True
    assert memo.tags == []


def test_create_with_tags_inserts_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    repo = MemoRepository(db_session)

    memo = repo.create(
        user_id=user.id,
        title="t",
        body=None,
        is_pinned=False,
        tags=[tag_b, tag_a],
    )
    db_session.flush()

    # 中間テーブルに2件入っている
    assert db_session.query(MemoTag).filter_by(memo_id=memo.id).count() == 2
    assert {t.id for t in memo.tags} == {tag_a.id, tag_b.id}


def test_get_returns_tags_in_name_order(db_session: Session) -> None:
    """relationship の `order_by` は SELECT 時に効くので、`get()` 経由で確認する。"""
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    tag_c = _make_tag(db_session, user, "c")
    repo = MemoRepository(db_session)

    memo = repo.create(
        user_id=user.id,
        title="t",
        body=None,
        is_pinned=False,
        tags=[tag_c, tag_a, tag_b],
    )
    db_session.flush()
    db_session.expire(memo)  # キャッシュを捨てて selectinload を強制

    fetched = repo.get(memo_id=memo.id, user_id=user.id)

    assert fetched is not None
    assert [t.name for t in fetched.tags] == ["a", "b", "c"]


def test_replace_updates_fields_and_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    tag_c = _make_tag(db_session, user, "c")
    repo = MemoRepository(db_session)

    memo = repo.create(user_id=user.id, title="old", body="ob", is_pinned=False, tags=[tag_a])
    db_session.flush()

    repo.replace(memo, title="new", body="nb", is_pinned=True, tags=[tag_b, tag_c])
    db_session.flush()

    assert memo.title == "new"
    assert memo.body == "nb"
    assert memo.is_pinned is True
    assert {t.name for t in memo.tags} == {"b", "c"}
    # 旧 memo_tags は消えていて、新しい2件のみ
    assert db_session.query(MemoTag).filter_by(memo_id=memo.id).count() == 2


def test_replace_with_empty_tags_removes_all_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    repo = MemoRepository(db_session)

    memo = repo.create(user_id=user.id, title="t", body=None, is_pinned=False, tags=[tag_a])
    db_session.flush()

    repo.replace(memo, title="t2", body=None, is_pinned=False, tags=[])
    db_session.flush()

    assert memo.tags == []
    assert db_session.query(MemoTag).filter_by(memo_id=memo.id).count() == 0


def test_delete_removes_memo_and_cascades_memo_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = _make_tag(db_session, user, "x")
    repo = MemoRepository(db_session)

    memo = repo.create(user_id=user.id, title="t", body=None, is_pinned=False, tags=[tag])
    db_session.flush()
    memo_id = memo.id

    repo.delete(memo)
    db_session.flush()

    assert db_session.get(Memo, memo_id) is None
    assert db_session.query(MemoTag).filter_by(memo_id=memo_id).count() == 0
    # タグ本体は残る
    assert db_session.get(Tag, tag.id) is not None


def test_update_pinned_changes_flag_and_updated_at(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = MemoRepository(db_session)
    memo = repo.create(user_id=user.id, title="t", body=None, is_pinned=False, tags=[])
    db_session.flush()

    # savepoint 内では func.now() が固定値のため、onupdate の効きを検証するには
    # 一度 raw SQL で過去日に backdate しておく必要がある。
    past = datetime.now(UTC) - timedelta(days=1)
    db_session.execute(
        text("UPDATE memos SET updated_at = :ts WHERE id = :id"),
        {"ts": past, "id": memo.id},
    )
    db_session.expire(memo)
    db_session.refresh(memo)
    before = memo.updated_at

    repo.update_pinned(memo, is_pinned=True)
    db_session.flush()
    db_session.refresh(memo)

    assert memo.is_pinned is True
    assert memo.updated_at > before


def test_find_user_tags_returns_matching_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    repo = MemoRepository(db_session)

    found = repo.find_user_tags(user_id=user.id, tag_ids=[tag_a.id, tag_b.id])

    assert {t.id for t in found} == {tag_a.id, tag_b.id}


def test_find_user_tags_excludes_other_users_tags(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    tag_own = _make_tag(db_session, owner, "own")
    tag_other = _make_tag(db_session, other, "other_tag")
    repo = MemoRepository(db_session)

    found = repo.find_user_tags(user_id=owner.id, tag_ids=[tag_own.id, tag_other.id])

    assert [t.id for t in found] == [tag_own.id]


def test_find_user_tags_excludes_nonexistent_ids(db_session: Session) -> None:
    user = _make_user(db_session)
    tag = _make_tag(db_session, user, "x")
    repo = MemoRepository(db_session)

    found = repo.find_user_tags(user_id=user.id, tag_ids=[tag.id, uuid4()])

    assert [t.id for t in found] == [tag.id]


def test_find_user_tags_with_empty_input_returns_empty(db_session: Session) -> None:
    user = _make_user(db_session)
    repo = MemoRepository(db_session)

    assert repo.find_user_tags(user_id=user.id, tag_ids=[]) == []


# ===== Repository.search のテスト =====


def _make_memo(
    db: Session,
    user: UserProfile,
    title: str,
    *,
    body: str | None = None,
    is_pinned: bool = False,
    tags: list[Tag] | None = None,
) -> Memo:
    memo = Memo(user_id=user.id, title=title, body=body, is_pinned=is_pinned)
    if tags:
        memo.tags = tags
    db.add(memo)
    db.flush()
    return memo


def _backdate(db: Session, memo: Memo, days_ago: int) -> None:
    """savepoint 内では now() が固定なので、updated_at を raw SQL でずらす。"""
    ts = datetime.now(UTC) - timedelta(days=days_ago)
    db.execute(
        text("UPDATE memos SET updated_at = :ts WHERE id = :id"),
        {"ts": ts, "id": memo.id},
    )


def test_search_returns_all_user_memos_sorted_by_pinned_then_updated(
    db_session: Session,
) -> None:
    user = _make_user(db_session)
    m1 = _make_memo(db_session, user, "old", is_pinned=False)
    m2 = _make_memo(db_session, user, "new", is_pinned=False)
    _make_memo(db_session, user, "pinned", is_pinned=True)
    db_session.flush()
    # updated_at: m1 が一番古い、m2 がそのつぎ、pinned は新しめ。だが is_pinned が優先される
    _backdate(db_session, m1, days_ago=2)
    _backdate(db_session, m2, days_ago=1)
    db_session.expire_all()

    repo = MemoRepository(db_session)
    items, total = repo.search(user_id=user.id, q=None, tag_ids=[], pinned=None, limit=20, offset=0)

    assert total == 3
    titles = [m.title for m in items]
    assert titles[0] == "pinned"  # is_pinned=True が最上位
    assert titles[1:] == ["new", "old"]  # updated_at DESC


def test_search_isolates_other_users(db_session: Session) -> None:
    owner = _make_user(db_session, "owner")
    other = _make_user(db_session, "other")
    _make_memo(db_session, owner, "own")
    _make_memo(db_session, other, "other_memo")
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=owner.id, q=None, tag_ids=[], pinned=None, limit=20, offset=0
    )

    assert total == 1
    assert items[0].title == "own"


def test_search_pagination_limits_and_offsets(db_session: Session) -> None:
    user = _make_user(db_session)
    for i in range(5):
        m = _make_memo(db_session, user, f"m{i}")
        db_session.flush()
        _backdate(db_session, m, days_ago=5 - i)  # m0 が最も古い → m4 が最新
    db_session.expire_all()

    repo = MemoRepository(db_session)
    items, total = repo.search(user_id=user.id, q=None, tag_ids=[], pinned=None, limit=2, offset=1)

    assert total == 5  # 全件数を返す
    assert len(items) == 2
    # updated_at DESC: m4, m3, m2, m1, m0 → offset=1 から limit=2 で m3, m2
    assert [m.title for m in items] == ["m3", "m2"]


def test_search_query_matches_title_case_insensitively(db_session: Session) -> None:
    user = _make_user(db_session)
    _make_memo(db_session, user, "Hello World")
    _make_memo(db_session, user, "Goodbye")
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=user.id, q="hello", tag_ids=[], pinned=None, limit=20, offset=0
    )

    assert total == 1
    assert items[0].title == "Hello World"


def test_search_query_matches_body(db_session: Session) -> None:
    user = _make_user(db_session)
    _make_memo(db_session, user, "t1", body="本文に検索ワード含む")
    _make_memo(db_session, user, "t2", body="関係ない")
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=user.id, q="検索ワード", tag_ids=[], pinned=None, limit=20, offset=0
    )

    assert total == 1
    assert items[0].title == "t1"


def test_search_query_returns_empty_when_no_match(db_session: Session) -> None:
    user = _make_user(db_session)
    _make_memo(db_session, user, "t", body="b")
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=user.id, q="存在しない", tag_ids=[], pinned=None, limit=20, offset=0
    )

    assert items == []
    assert total == 0


def test_search_tag_and_requires_all_tags(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    tag_b = _make_tag(db_session, user, "b")
    _make_memo(db_session, user, "only_a", tags=[tag_a])
    _make_memo(db_session, user, "only_b", tags=[tag_b])
    _make_memo(db_session, user, "a_and_b", tags=[tag_a, tag_b])
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=user.id, q=None, tag_ids=[tag_a.id, tag_b.id], pinned=None, limit=20, offset=0
    )

    assert total == 1
    assert items[0].title == "a_and_b"


def test_search_tag_and_with_single_tag(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_a = _make_tag(db_session, user, "a")
    _make_memo(db_session, user, "with_a", tags=[tag_a])
    _make_memo(db_session, user, "without_a")
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=user.id, q=None, tag_ids=[tag_a.id], pinned=None, limit=20, offset=0
    )

    assert total == 1
    assert items[0].title == "with_a"


def test_search_pinned_true_filters_only_pinned(db_session: Session) -> None:
    user = _make_user(db_session)
    _make_memo(db_session, user, "p", is_pinned=True)
    _make_memo(db_session, user, "np", is_pinned=False)
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(user_id=user.id, q=None, tag_ids=[], pinned=True, limit=20, offset=0)

    assert total == 1
    assert items[0].title == "p"


def test_search_pinned_none_returns_all(db_session: Session) -> None:
    user = _make_user(db_session)
    _make_memo(db_session, user, "p", is_pinned=True)
    _make_memo(db_session, user, "np", is_pinned=False)
    db_session.flush()

    repo = MemoRepository(db_session)
    _, total = repo.search(user_id=user.id, q=None, tag_ids=[], pinned=None, limit=20, offset=0)

    assert total == 2


def test_search_combined_conditions(db_session: Session) -> None:
    user = _make_user(db_session)
    tag_work = _make_tag(db_session, user, "work")
    # 検索語＋タグ＋ピン留めすべて一致
    target = _make_memo(
        db_session, user, "会議メモ", body="重要な議題", is_pinned=True, tags=[tag_work]
    )
    # 検索語のみ一致 (タグなし、ピンなし) — 除外される
    _make_memo(db_session, user, "会議の予定")
    # タグ + ピンのみ一致 — 検索語なしで除外
    _make_memo(db_session, user, "他のメモ", is_pinned=True, tags=[tag_work])
    db_session.flush()

    repo = MemoRepository(db_session)
    items, total = repo.search(
        user_id=user.id,
        q="会議メモ",
        tag_ids=[tag_work.id],
        pinned=True,
        limit=20,
        offset=0,
    )

    assert total == 1
    assert items[0].id == target.id


def test_search_loads_tags_eagerly(db_session: Session) -> None:
    """selectinload(Memo.tags) で N+1 を避け、tags も name 昇順で取得する。"""
    user = _make_user(db_session)
    tag_z = _make_tag(db_session, user, "z")
    tag_a = _make_tag(db_session, user, "a")
    _make_memo(db_session, user, "m", tags=[tag_z, tag_a])
    db_session.flush()
    db_session.expire_all()

    repo = MemoRepository(db_session)
    items, _ = repo.search(user_id=user.id, q=None, tag_ids=[], pinned=None, limit=20, offset=0)

    assert [t.name for t in items[0].tags] == ["a", "z"]
