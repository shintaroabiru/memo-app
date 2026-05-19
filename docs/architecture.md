# アーキテクチャ設計書（Architecture）

本ドキュメントは、メモアプリのシステム構成・ディレクトリ構造・レイヤー設計を定義する。
[project-overview.md](./project-overview.md) / [requirements.md](./requirements.md) と併せて、AI駆動開発・ドキュメント駆動開発の起点として活用する。

---

## 1. システム構成

### 1.1 全体構成図

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│                 │      │                      │      │                 │
│   ブラウザ       │ ───▶ │   Next.js (BFF)       │ ───▶ │   FastAPI       │
│   (React UI)    │      │   Route Handler       │      │   (Python)      │
│                 │ ◀─── │                      │ ◀─── │                 │
└─────────────────┘      └──────────────────────┘      └────────┬────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────┐
                                                       │   PostgreSQL    │
                                                       │   (Docker)      │
                                                       └─────────────────┘
```

### 1.2 各レイヤーの責務

| レイヤー         | 技術                      | 責務                                                   |
|------------------|---------------------------|--------------------------------------------------------|
| プレゼンテーション | React / Next.js (App Router) | UI描画、ユーザー操作の受付、クライアント状態管理            |
| BFF              | Next.js Route Handler     | リクエスト中継、フロント向けレスポンス整形、将来の認証セッション管理 |
| アプリケーション | FastAPI                   | ビジネスロジック、入力バリデーション、DB操作              |
| 永続化           | PostgreSQL                | データの保存                                            |

### 1.3 API呼び出し方式：BFF構成を採用

フロントから直接 FastAPI を叩くのではなく、**Next.js の Route Handler を経由する BFF（Backend For Frontend）構成** を採用する。

**採用理由**
- フェーズ2で導入する認証セッションを Next.js 側で安全に管理できる（HTTPOnly Cookie 等）
- FastAPI を外部公開する必要がなく、内部通信に限定できる
- フロント向けにレスポンスを整形・集約しやすい
- CORS の取り回しを単純化できる

**通信の流れ**
1. ブラウザ → Next.js Route Handler（`/api/memos` 等）
2. Route Handler → FastAPI（`http://backend:8000/api/v1/memos` 等、Docker内部通信）
3. FastAPI → PostgreSQL

---

## 2. リポジトリ構成（モノレポ）

```
memo-app/
├── frontend/              # Next.js アプリケーション
├── backend/               # FastAPI アプリケーション
├── docs/                  # プロジェクトドキュメント
│   ├── project-overview.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── db-schema.md
│   ├── api-spec.md
│   └── design/            # UIデザイン（Pencil）
│       ├── README.md      # Pencilの使い方・運用ルール
│       └── design.pen     # メインのモックアップファイル
├── docker-compose.yml     # バックエンド + DB の環境定義
├── .env.example           # 環境変数テンプレート
├── .gitignore
├── CLAUDE.md              # Claude Code 向けプロジェクト指示書
└── README.md
```

> フロントエンドの開発サーバーはローカル（`npm run dev`）で動かし、バックエンドとDBのみ Docker で起動する想定。フロントもDocker化する場合は将来検討。

---

## 3. フロントエンド構成（Next.js / App Router）

### 3.1 ディレクトリ構造

```
frontend/
├── src/
│   ├── app/                          # App Router のルート
│   │   ├── layout.tsx                # 全体レイアウト
│   │   ├── page.tsx                  # メモ一覧（ホーム）
│   │   ├── memos/
│   │   │   ├── new/
│   │   │   │   └── page.tsx          # メモ新規作成
│   │   │   └── [id]/
│   │   │       └── page.tsx          # メモ詳細・編集
│   │   ├── profile/
│   │   │   └── page.tsx              # プロフィール編集
│   │   └── api/                      # Route Handler (BFF)
│   │       ├── memos/
│   │       │   ├── route.ts          # GET (一覧) / POST (作成)
│   │       │   └── [id]/
│   │       │       ├── route.ts      # GET / PUT / DELETE
│   │       │       └── pin/
│   │       │           └── route.ts  # PATCH (ピン留めトグル)
│   │       ├── tags/
│   │       │   ├── route.ts          # GET / POST
│   │       │   └── [id]/
│   │       │       └── route.ts      # PUT / DELETE
│   │       └── profile/
│   │           └── route.ts          # GET / PUT
│   │
│   ├── components/                   # 汎用UIコンポーネントのみ
│   │   └── ui/                       # Button, Input, Modal 等
│   │
│   ├── features/                     # 機能単位で集約（components/hooks/api/schemas/types）
│   │   ├── memo/
│   │   │   ├── components/
│   │   │   │   ├── MemoCard.tsx
│   │   │   │   ├── MemoForm.tsx
│   │   │   │   ├── MemoList.tsx
│   │   │   │   └── PinButton.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useMemoList.ts
│   │   │   │   └── useMemoForm.ts
│   │   │   ├── api.ts                # クライアント側API呼び出し関数
│   │   │   ├── schemas.ts            # Zodスキーマ
│   │   │   └── types.ts              # メモ関連の型定義
│   │   ├── tag/
│   │   │   ├── components/
│   │   │   │   ├── TagSelector.tsx       # メモ作成・編集時のタグ選択UI
│   │   │   │   └── TagManageModal.tsx    # タグ管理モーダル
│   │   │   ├── hooks/
│   │   │   ├── api.ts
│   │   │   ├── schemas.ts
│   │   │   └── types.ts
│   │   └── profile/
│   │       ├── components/
│   │       │   └── ProfileForm.tsx
│   │       ├── hooks/
│   │       ├── api.ts
│   │       ├── schemas.ts
│   │       └── types.ts
│   │
│   ├── stores/                       # Zustand ストア
│   │   ├── memoStore.ts
│   │   └── tagStore.ts
│   │
│   ├── lib/                          # 汎用ユーティリティ
│   │   ├── api-client.ts             # fetch ラッパー
│   │   ├── backend-client.ts         # Route Handler → FastAPI 用クライアント
│   │   └── utils.ts
│   │
│   └── types/                        # 共通型定義（features横断で使うもののみ）
│       └── index.ts
│
├── public/
├── .env.local.example
├── next.config.ts
├── tsconfig.json
├── package.json
└── tailwind.config.ts
```

### 3.2 レイヤー責務

| ディレクトリ                | 責務                                                              |
|----------------------------|------------------------------------------------------------------|
| `app/`                     | ルーティングとページコンポーネント。なるべく薄く保ち、`features/` を呼ぶ |
| `app/api/`                 | BFF。リクエストを受けて FastAPI を呼び出し、レスポンスを返す           |
| `components/ui/`           | 汎用UI（複数機能で共通利用）。機能固有のものは置かない                   |
| `features/{機能名}/`       | 機能ごとに凝集。components / hooks / api / schemas / types を内包する  |
| `features/{機能名}/components/` | その機能でのみ使うコンポーネント                                   |
| `features/{機能名}/hooks/`  | その機能のカスタムフック                                            |
| `features/{機能名}/api.ts`  | クライアント側からBFF（`/api/...`）を叩く関数群                       |
| `features/{機能名}/schemas.ts` | Zodスキーマ。フロント側のバリデーションと型生成に使う                |
| `features/{機能名}/types.ts` | その機能の型定義                                                   |
| `stores/`                  | Zustandによるクライアント状態管理（UI状態中心）                         |
| `lib/`                     | プロジェクト全体で使う薄いユーティリティ                                |
| `types/`                   | features横断で使う共通型定義のみ                                     |

### 3.3 features 採用方針

- **原則として、機能固有のコンポーネント・ロジックは `features/{機能名}/` 配下に閉じる**
- **`components/ui/` には汎用UIのみ**（Button, Input, Modal等）。2つ以上の機能で再利用する場合のみここに昇格させる
- **機能横断で使うコンポーネントが出てきた場合**は、`components/` 直下に切り出すか、汎用化して `components/ui/` に移す
- **Claude Codeへの指示**: 「メモ機能の修正」は基本的に `features/memo/` 配下で完結するように設計

### 3.4 状態管理方針（SWR + Zustand）

- **サーバー由来のデータ**（メモ一覧、タグ一覧など）の初期描画は **サーバーコンポーネントでのフェッチ** を優先
- **クライアント側で再フェッチが必要な場面**（検索クエリ変更、フィルタ変更、ミューテーション後の再取得、別機能起因の無効化など）は **SWR** を使う
  - キャッシュキーは URL ベース（例: `/api/memos?q=...&tag_ids=...`）
  - 別コンポーネントからの無効化は `mutate(key)` で行う（例: タグ削除 → `mutate('/api/memos')`）
- **UI状態**（モーダル開閉、フォーム入力、フィルタの一時状態など）は **Zustand** で管理
- 楽観的UI更新が必要な箇所（ピン留めトグル等）は SWR の `mutate(key, optimisticData, { revalidate: true })` で即時反映 → サーバー結果で確定

---

## 4. バックエンド構成（FastAPI / Python）

### 4.1 ディレクトリ構造

```
backend/
├── app/
│   ├── main.py                       # FastAPIエントリポイント
│   ├── core/
│   │   ├── config.py                 # 環境変数読み込み
│   │   └── database.py               # DBセッション管理
│   │
│   ├── api/
│   │   ├── deps.py                   # 共通依存（DBセッション注入等）
│   │   └── v1/
│   │       ├── memos.py              # メモ関連エンドポイント
│   │       ├── tags.py               # タグ関連エンドポイント
│   │       └── profile.py            # プロフィール関連エンドポイント
│   │
│   ├── models/                       # SQLAlchemy モデル
│   │   ├── memo.py
│   │   ├── tag.py
│   │   ├── memo_tag.py               # 中間テーブル
│   │   └── user_profile.py
│   │
│   ├── schemas/                      # Pydantic スキーマ（リクエスト/レスポンス）
│   │   ├── memo.py
│   │   ├── tag.py
│   │   └── profile.py
│   │
│   ├── services/                     # ビジネスロジック
│   │   ├── memo_service.py
│   │   ├── tag_service.py
│   │   └── profile_service.py
│   │
│   └── repositories/                 # DB操作層（任意）
│       ├── memo_repository.py
│       └── tag_repository.py
│
├── tests/
│   ├── conftest.py
│   ├── models/                       # SQLAlchemy モデルの単体テスト
│   ├── repositories/                 # Repository層の単体テスト
│   ├── services/                     # Service層の単体テスト
│   └── api/                          # API層（TestClient）のテスト
│
├── alembic/                          # マイグレーション
│   └── versions/
├── alembic.ini
├── Dockerfile
├── pyproject.toml (or requirements.txt)
└── .env.example
```

### 4.2 レイヤー責務

| レイヤー         | 責務                                                  |
|------------------|------------------------------------------------------|
| `api/`           | HTTPルーティング、リクエスト/レスポンス変換             |
| `schemas/`       | Pydanticによる入出力スキーマ定義（バリデーション含む）    |
| `services/`      | ビジネスロジック。トランザクション境界もここで管理         |
| `repositories/`  | DB操作の抽象化。SQLAlchemyクエリをカプセル化              |
| `models/`        | SQLAlchemyのテーブル定義                                |
| `core/`          | 設定・DBセッション・共通基盤                             |

> `repositories/` は学習目的で導入しているが、規模が小さいうちは `services/` から直接モデルを触ってもよい。プロジェクトの成熟度に応じて段階的に分離する。

#### 共通実装パターン: 外部リソース参照の存在/権限検証

リクエストに「既存リソースの ID 配列」（例: メモ作成時の `tag_ids`、将来のメモ共有先 `user_ids` など）が含まれるとき、**Repository は "ユーザーが所有しているもののみ" を返す検索メソッド**を提供し、**Service が "入力との差分" を計算してエラー化する**ように責務を分ける。

- Repository: `find_*_by_ids(user_id, ids)` で **ホワイトリストされた結果のみ** を返す（存在しない / 他ユーザー所有のものは結果に含めない）
- Service: `len(found) != len(input)` の場合に不足 ID を計算し、`BadRequestError` を投げる
- DB の FK 違反（IntegrityError）に頼って事後検出すると、誤誘導メッセージや不要なロールバックを招くので採用しない

実装例: [`backend/app/services/memo_service.py`](../backend/app/services/memo_service.py) の `_resolve_tags` と [`backend/app/repositories/memo_repository.py`](../backend/app/repositories/memo_repository.py) の `find_user_tags`。同様のニーズが発生する新しいエンドポイントでもこのパターンを踏襲する。

#### 共通実装パターン: relationship 経由で代入したコレクションを order_by 適用で返す

`Memo.tags` のような多対多 relationship に Python 側で `memo.tags = [tag_x, ...]` と代入してコミットした直後に `memo.tags` を読むと、**relationship に定義した `order_by` ではなく、代入時に渡したリストの順序**が返ってくる。これは SQLAlchemy が identity map にキャッシュした InstrumentedList を保持し続け、`selectinload` を含む再ロード戦略は「未ロードの属性のみロード」する仕様のため、既に代入で埋まったコレクションを上書きしないのが理由。

API レスポンスで relationship に定義した `order_by`（例: タグ名昇順）を効かせたいときは、**コミット後に対象属性を `expire` してから `refresh` する**。

```python
self._session.commit()
self._session.expire(memo, ["tags"])
self._session.refresh(memo, ["tags"])
return memo
```

実装例: [`backend/app/services/memo_service.py`](../backend/app/services/memo_service.py) の `_reload_tags`。`POST /memos` / `PUT /memos/{id}` のレスポンスに含まれる `tags` を name 昇順で揃えるために使用している。新規エンドポイントでも、relationship 経由で更新したコレクションをそのままレスポンスで返す場合は同じパターンを踏襲する。

### 4.3 APIバージョニング

- FastAPI 側を **正準パス** とし、`/api/v1/...` プレフィックスで運用する（将来の破壊的変更に備える）
- BFF（Next.js Route Handler）は `/api/...` で薄くプロキシし、内部で `/api/v1/...` を呼び出す
- 詳細は [`api-spec.md`](./api-spec.md) §1.1 を参照

---

## 5. データフロー例：メモ新規作成

```
[ユーザー]
    │ フォーム送信
    ▼
[React Component]  ← Zodでクライアント側バリデーション
    │ POST /api/memos
    ▼
[Next.js Route Handler]  ← 認証チェック（フェーズ2以降）
    │ POST http://backend:8000/api/v1/memos
    ▼
[FastAPI: api/v1/memos.py]  ← Pydanticでバリデーション
    │
    ▼
[services/memo_service.py]  ← ビジネスロジック・トランザクション
    │
    ▼
[repositories/memo_repository.py]
    │
    ▼
[PostgreSQL]
```

---

## 6. 環境構築方針

### 6.1 Docker Compose（バックエンド + DB）

`docker-compose.yml` で以下のサービスを定義：

| サービス   | 役割                  | ポート（ホスト→コンテナ） |
|------------|----------------------|--------------------------|
| `backend`  | FastAPIアプリケーション | `8000:8000`              |
| `db`       | PostgreSQL            | `5432:5432`              |

- `backend` は `db` に依存（`depends_on`）
- ボリュームで PostgreSQL のデータを永続化
- ホットリロード設定（開発時）

### 6.2 フロントエンド

- ローカルで `npm run dev`（`http://localhost:3000`）
- 環境変数 `BACKEND_API_URL` で FastAPI のURLを指定
  - ローカル開発時: `http://localhost:8000`
  - Docker内部通信に切り替える場合: `http://backend:8000`

---

## 7. 命名規約・コーディング規約（概要）

| 対象                   | 規約                                                    |
|-----------------------|--------------------------------------------------------|
| Reactコンポーネント    | PascalCase（`MemoCard.tsx`）                            |
| カスタムフック         | `use` プレフィックス（`useMemoList`）                    |
| Zustandストア          | `xxxStore`（`memoStore.ts`）                            |
| Pythonクラス           | PascalCase                                              |
| Python関数・変数       | snake_case                                              |
| DBテーブル名           | snake_case・複数形（`memos`, `tags`, `memo_tags`）       |
| APIパス               | 複数形（例: `/api/v1/memos`、`/api/v1/tags`）              |

> 詳細な規約は `CLAUDE.md` で Claude Code 向けに明文化する。

---

## 8. フェーズ2を見据えた拡張ポイント

- **認証**: Next.js Route Handler に認証ミドルウェアを追加。FastAPI へは内部認証トークン（or サービス間信頼）で連携
- **マルチユーザー化**: 全API呼び出しでログインユーザーの `user_id` をスコープに含める設計を フェーズ1から徹底
- **権限制御**: 「自分のメモしか操作できない」制約を services 層で強制

---

## 9. 決定事項まとめ

| 項目                  | 決定                                            |
|----------------------|------------------------------------------------|
| リポジトリ構成        | モノレポ（`frontend/` + `backend/`）            |
| ルーティング          | Next.js App Router                              |
| API呼び出し方式       | BFF構成（Next.js Route Handler 経由）            |
| フロント構成方針      | `features/` ディレクトリで機能別に集約            |
| APIバージョニング     | `/api/v1/` プレフィックス                        |
| 環境構築              | バックエンド・DBをDocker Composeで起動            |
| バックエンドのレイヤー | api / services / repositories / models の4層     |
| フロントテスト        | Vitest                                          |
| フロントLint/Format   | ESLint + Prettier                               |
| バックLint/Format     | Ruff                                            |
| UIデザインツール       | Pencil（`docs/design/design.pen`）              |
