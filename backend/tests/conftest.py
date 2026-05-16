"""pytest共通フィクスチャ。

- `client`: FastAPIのテスト用HTTPクライアント
- `db_session`: テストDBに接続したSQLAlchemyセッション（各テストでロールバック）
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
from app.core.database import Base
from app.main import app as fastapi_app

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
def client() -> TestClient:
    """FastAPIのテスト用HTTPクライアント。"""
    return TestClient(fastapi_app)
