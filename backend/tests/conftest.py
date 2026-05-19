"""pytest共通フィクスチャ。

- `client`: 素の FastAPI テスト用HTTPクライアント（DB・ユーザーに依存しない）
- `api_client`: `client` に DB セッションとデフォルトユーザーを差し込んだ APIテスト用
- `db_session`: テストDBに接続したSQLAlchemyセッション（各テストでロールバック）
- `default_user`: API テスト用の仮ユーザー（`get_current_user_id` 経由で参照される）
- テスト用DB (`memo_app_test`) は初回テスト時に自動作成される
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

import app.models  # noqa: F401  Base.metadata に全モデルを登録するための副作用 import
from app.api.deps import get_current_user_id, get_session
from app.core.database import Base
from app.main import app as fastapi_app
from app.models import UserProfile

DEFAULT_TEST_DB_URL = "postgresql+psycopg://memo:memo@localhost:5432/memo_app_test"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)


def _ensure_test_db_exists() -> None:
    """テスト用DBが存在しなければ作成する。"""
    url = make_url(TEST_DATABASE_URL)
    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            existing = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).first()
            if existing is None:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """テスト用DBのエンジン。スキーマを毎セッション再作成する。"""
    _ensure_test_db_exists()
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """各テストはトランザクション内で実行し、終了時にロールバックする。"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def default_user(db_session: Session) -> UserProfile:
    """API テストで `get_current_user_id` が返すデフォルトの仮ユーザー。"""
    user = UserProfile(display_name="API テストユーザー")
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def client() -> TestClient:
    """素の FastAPI テスト用 HTTP クライアント。

    DB・ユーザーに依存しないエンドポイント（`/health` など）のテスト向け。
    DB やユーザーが必要な API テストは `api_client` を使う。
    """
    return TestClient(fastapi_app)


@pytest.fixture
def api_client(
    db_session: Session, default_user: UserProfile
) -> Generator[TestClient, None, None]:
    """API テスト用のクライアント。

    `get_session` をテスト用セッションに、`get_current_user_id` を `default_user` に差し替える。
    """
    fastapi_app.dependency_overrides[get_session] = lambda: db_session
    fastapi_app.dependency_overrides[get_current_user_id] = lambda: default_user.id
    try:
        yield TestClient(fastapi_app)
    finally:
        fastapi_app.dependency_overrides.clear()
