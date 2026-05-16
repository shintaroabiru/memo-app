# Backend (FastAPI)

メモアプリのバックエンド。

## セットアップ（ローカル開発）

### 1. 仮想環境を作成して依存関係をインストール

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. テスト実行

テストは PostgreSQL に接続する。事前に DB を起動しておくこと。

```bash
# リポジトリルートで
docker compose up -d db

# backend/ で
pytest
```

テスト用DB `memo_app_test` は初回テスト時に自動作成される。
別ホスト/ポートを使う場合は環境変数 `TEST_DATABASE_URL` を上書きする。

### 3. Lint / Format

```bash
ruff check .
ruff format .
```

### 4. マイグレーション

```bash
# DB を起動した状態で
alembic upgrade head        # 最新までマイグレーション
alembic downgrade -1        # 1つ戻す
alembic revision -m "msg"   # 新しい空マイグレーションを生成
```

DB接続先は `app.core.config.Settings.database_url`（環境変数 `DATABASE_URL`）から自動取得する。

### 5. ローカルでサーバー起動

```bash
uvicorn app.main:app --reload
# http://localhost:8000/health
# http://localhost:8000/docs (Swagger UI)
```

## Docker 経由で起動

リポジトリルートで:

```bash
docker compose up backend
```

## ディレクトリ構成

```
backend/
├── alembic/                # マイグレーションスクリプト
│   ├── env.py
│   └── versions/
├── app/
│   ├── core/
│   │   ├── config.py       # 環境変数読み込み
│   │   └── database.py     # SQLAlchemy エンジン / Base / セッション
│   ├── models/             # SQLAlchemy モデル
│   └── main.py             # FastAPI エントリポイント
├── tests/
│   ├── conftest.py
│   ├── models/             # モデル単体テスト
│   └── test_health.py
├── alembic.ini
├── Dockerfile
└── pyproject.toml
```

詳細は [`../docs/architecture.md`](../docs/architecture.md) を参照。
