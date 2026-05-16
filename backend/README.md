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

```bash
pytest
```

### 3. Lint / Format

```bash
ruff check .
ruff format .
```

### 4. ローカルでサーバー起動

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
├── app/
│   ├── core/
│   │   └── config.py       # 環境変数読み込み
│   └── main.py             # FastAPIエントリポイント
├── tests/
│   ├── conftest.py
│   └── test_health.py
├── Dockerfile
└── pyproject.toml
```

詳細は [`../docs/architecture.md`](../docs/architecture.md) を参照。
