# Memo App

プログラミングスキル向上を目的とした、学習用メモアプリです。
**AI駆動開発 / ドキュメント駆動開発** をコンセプトに、設計ドキュメントを起点として実装を進めるプロジェクトです。

---

## ✨ 主な機能

### フェーズ1（実装対象）
- 📝 メモのCRUD（作成・編集・削除・一覧表示）
- 🔍 メモの検索（タイトル + 本文の部分一致）
- 🏷️ タグによる分類とフィルタ
- 📌 ピン留め（お気に入り）
- 👤 ユーザープロフィールの編集

### フェーズ2（予定）
- 🔐 ユーザー登録・認証機能

---

## 🛠 技術スタック

### フロントエンド
- [Next.js](https://nextjs.org/)（App Router）
- TypeScript
- React
- [Zod](https://zod.dev/) — バリデーション
- [Zustand](https://zustand-demo.pmnd.rs/) — 状態管理
- Tailwind CSS

### バックエンド
- [FastAPI](https://fastapi.tiangolo.com/)
- Python 3.11+
- [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 — ORM
- [Alembic](https://alembic.sqlalchemy.org/) — マイグレーション
- [Pydantic](https://docs.pydantic.dev/) — スキーマ
- [pytest](https://docs.pytest.org/) — テスト

### インフラ
- PostgreSQL
- Docker Compose（バックエンド + DB）

### 開発環境
- エディタ: Cursor
- AIアシスタント: Claude Code

---

## 📁 プロジェクト構成

```
memo-app/
├── frontend/              # Next.js アプリケーション
├── backend/               # FastAPI アプリケーション
├── docs/                  # 設計ドキュメント
│   ├── project-overview.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── db-schema.md
│   └── api-spec.md
├── docker-compose.yml     # バックエンド + DB の環境定義
├── CLAUDE.md              # Claude Code 向け指示書
└── README.md              # 本ファイル
```

詳細は [`docs/architecture.md`](./docs/architecture.md) を参照してください。

---

## 📚 ドキュメント

このプロジェクトは**ドキュメント駆動開発**で進めています。実装の前にまず以下のドキュメントを参照してください。

| ドキュメント                                          | 内容                                |
|------------------------------------------------------|------------------------------------|
| [project-overview.md](./docs/project-overview.md)    | プロジェクト全体像                  |
| [requirements.md](./docs/requirements.md)            | 機能要件・データモデル               |
| [architecture.md](./docs/architecture.md)            | システム構成・ディレクトリ構造        |
| [db-schema.md](./docs/db-schema.md)                  | データベース設計                    |
| [api-spec.md](./docs/api-spec.md)                    | API仕様                            |
| [CLAUDE.md](./CLAUDE.md)                             | Claude Code 向けプロジェクト指示書   |

---

## 🚀 セットアップ

### 前提条件
- Node.js 20以上
- Python 3.11以上
- Docker / Docker Compose
- Git

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd memo-app
```

### 2. 環境変数の設定

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
cp backend/.env.example backend/.env
```

各 `.env` ファイルを必要に応じて編集してください。

### 3. バックエンド + DB の起動（Docker）

```bash
docker compose up -d
```

### 4. データベースマイグレーション

```bash
docker compose exec backend alembic upgrade head
```

### 5. フロントエンドの起動

```bash
cd frontend
npm install
npm run dev
```

ブラウザで `http://localhost:3000` にアクセスしてください。

---

## 🧪 テスト実行

このプロジェクトは **TDD（テスト駆動開発）** を採用しています。

### バックエンド

```bash
docker compose exec backend pytest
```

### フロントエンド

```bash
cd frontend
npm test
```

---

## 🔄 開発ワークフロー

1. **ドキュメントを読む** — `docs/` 配下の関連ドキュメントを確認
2. **ブランチを切る** — `feature/xxx`、`fix/xxx` 等
3. **テストを書く** — 期待する振る舞いをテストで定義（Red）
4. **実装する** — テストを通す最小限のコード（Green）
5. **リファクタする** — 整理する（Refactor）
6. **コミット** — Conventional Commits に準拠

詳細は [`CLAUDE.md`](./CLAUDE.md) を参照してください。

---

## 📦 ブランチ戦略

| ブランチ                | 用途                                  |
|-------------------------|--------------------------------------|
| `main`                  | 常に動作する状態を保つ                  |
| `feature/{機能名}`      | 機能単位の実装ブランチ                  |
| `fix/{修正内容}`        | バグ修正                              |
| `docs/{ドキュメント名}` | ドキュメントのみの変更                  |
| `refactor/{対象}`       | リファクタリング                       |

---

## 🤝 コントリビューション

このプロジェクトは学習用途のため、現時点では外部からのコントリビューションは想定していません。

ただし、設計やコードに対するフィードバックは Issue で歓迎します。

---

## 📝 ライセンス

学習用途のプロジェクトのため、特定のライセンスは設定していません。

---

## 🙋 作者

しん（[@nonon](#)）

- AIアプリエンジニア / マーケティング戦略コンサルタント
- 本プロジェクトは Claude Code を活用したAI駆動開発の実践プロジェクトです
