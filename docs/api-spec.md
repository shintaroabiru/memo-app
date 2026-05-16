# API仕様書（API Spec）

本ドキュメントは、メモアプリのAPIエンドポイント仕様を定義する。
[requirements.md](./requirements.md) / [architecture.md](./architecture.md) / [db-schema.md](./db-schema.md) と併せて参照すること。

---

## 1. 共通仕様

### 1.1 ベースURL

| 環境               | ベースURL                          |
|--------------------|-----------------------------------|
| ブラウザ → BFF      | `/api/`                           |
| BFF → FastAPI（内部）| `http://backend:8000/api/v1/`     |

> 本ドキュメントでは **BFF（Next.js Route Handler）が公開するAPI** を中心に記述する。FastAPI側のパスはプレフィックスを `/api/v1/` に置き換えれば同じ仕様で動作する。

### 1.2 リクエスト形式

- メソッド: `GET` / `POST` / `PUT` / `PATCH` / `DELETE`
- Content-Type: `application/json`
- 文字コード: UTF-8

### 1.3 認証

- **フェーズ1**: 認証なし。サーバー側で固定の仮ユーザーID（`DEFAULT_USER_ID`）を使用
- **フェーズ2**: 認証セッション（HTTPOnly Cookie）で `user_id` を解決（別途設計）

### 1.4 共通レスポンス形式

#### 成功時

ステータスコード `200` / `201` / `204` を返し、JSON形式でデータを返す（`204` はボディなし）。

#### エラー時

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "タイトルは必須です",
    "details": [
      { "field": "title", "message": "1文字以上で入力してください" }
    ]
  }
}
```

### 1.5 エラーコード一覧

| HTTPステータス | エラーコード             | 用途                                |
|---------------|-------------------------|-------------------------------------|
| 400           | `VALIDATION_ERROR`      | リクエストボディのバリデーション失敗  |
| 400           | `BAD_REQUEST`           | その他の不正リクエスト                |
| 404           | `NOT_FOUND`             | リソースが存在しない                  |
| 409           | `CONFLICT`              | 一意制約違反（タグ名重複など）        |
| 500           | `INTERNAL_SERVER_ERROR` | サーバー内部エラー                    |

### 1.6 ページング共通パラメータ

| パラメータ | 型      | デフォルト | 説明                |
|-----------|---------|-----------|---------------------|
| `limit`   | integer | 20        | 1ページの件数（最大100） |
| `offset`  | integer | 0         | 取得開始位置          |

### 1.7 共通フィールド

すべてのリソースは以下を含む。

| フィールド    | 型              | 説明              |
|---------------|-----------------|------------------|
| `id`          | string (UUID)   | リソースID         |
| `created_at`  | string (ISO8601)| 作成日時           |
| `updated_at`  | string (ISO8601)| 最終更新日時       |

---

## 2. メモAPI

### 2.1 メモ一覧取得

メモの一覧を取得する。検索・タグフィルタ・ピン留めフィルタに対応。

**エンドポイント**

```
GET /api/memos
```

**クエリパラメータ**

| 名前         | 型              | 必須 | 説明                                    |
|--------------|----------------|------|-----------------------------------------|
| `q`          | string         | ❌   | 検索キーワード（タイトル+本文の部分一致）    |
| `tag_ids`    | string[]       | ❌   | タグIDの配列（AND条件で絞り込み）           |
| `pinned`     | boolean        | ❌   | ピン留めのみ取得する場合 `true`             |
| `limit`      | integer        | ❌   | デフォルト20、最大100                       |
| `offset`     | integer        | ❌   | デフォルト0                                |

**リクエスト例**

```
GET /api/memos?q=会議&tag_ids=tag-uuid-1&tag_ids=tag-uuid-2&limit=20&offset=0
```

**レスポンス例（200 OK）**

```json
{
  "items": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "title": "週次会議メモ",
      "body": "今週のトピック...",
      "is_pinned": true,
      "tags": [
        { "id": "tag-uuid-1", "name": "仕事" },
        { "id": "tag-uuid-2", "name": "会議" }
      ],
      "created_at": "2026-05-10T09:00:00+09:00",
      "updated_at": "2026-05-15T14:30:00+09:00"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**ソート順**: `is_pinned DESC, updated_at DESC`（固定）

---

### 2.2 メモ詳細取得

**エンドポイント**

```
GET /api/memos/{id}
```

**パスパラメータ**

| 名前 | 型            | 説明    |
|------|---------------|--------|
| `id` | string (UUID) | メモID  |

**レスポンス例（200 OK）**

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "title": "週次会議メモ",
  "body": "今週のトピック...",
  "is_pinned": true,
  "tags": [
    { "id": "tag-uuid-1", "name": "仕事" },
    { "id": "tag-uuid-2", "name": "会議" }
  ],
  "created_at": "2026-05-10T09:00:00+09:00",
  "updated_at": "2026-05-15T14:30:00+09:00"
}
```

**エラー**: `404 NOT_FOUND`（メモが存在しない）

---

### 2.3 メモ新規作成

**エンドポイント**

```
POST /api/memos
```

**リクエストボディ**

| フィールド    | 型              | 必須 | 説明                                |
|---------------|----------------|------|------------------------------------|
| `title`       | string (1-100) | ✅   | タイトル                            |
| `body`        | string (0-10000)| ❌   | 本文                                |
| `tag_ids`     | string[]       | ❌   | 既存タグIDの配列（最大10件）          |
| `is_pinned`   | boolean        | ❌   | デフォルト `false`                  |

**リクエスト例**

```json
{
  "title": "週次会議メモ",
  "body": "今週のトピック...",
  "tag_ids": ["tag-uuid-1", "tag-uuid-2"],
  "is_pinned": false
}
```

**レスポンス例（201 Created）**

2.2 と同じ形式でメモ詳細を返す。

**エラー**
- `400 VALIDATION_ERROR`: タイトル未入力、文字数超過など
- `400 BAD_REQUEST`: 存在しない `tag_ids` を指定（新規タグはタグAPIで先に作成すること）

---

### 2.4 メモ更新

**エンドポイント**

```
PUT /api/memos/{id}
```

**リクエストボディ**

2.3 と同じ。全フィールドを送信する（部分更新ではない）。

**レスポンス例（200 OK）**

2.2 と同じ形式でメモ詳細を返す。

**エラー**
- `404 NOT_FOUND`
- `400 VALIDATION_ERROR`
- `400 BAD_REQUEST`（存在しない `tag_ids`）

---

### 2.5 メモ削除

**エンドポイント**

```
DELETE /api/memos/{id}
```

**レスポンス**: `204 No Content`（ボディなし）

**エラー**: `404 NOT_FOUND`

**備考**: 物理削除。関連する `memo_tags` レコードもCASCADEで削除される。

---

### 2.6 ピン留めトグル

ピン留め状態を切り替える専用エンドポイント。

**エンドポイント**

```
PATCH /api/memos/{id}/pin
```

**リクエストボディ**

```json
{
  "is_pinned": true
}
```

**レスポンス例（200 OK）**

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "is_pinned": true,
  "updated_at": "2026-05-15T14:30:00+09:00"
}
```

**エラー**: `404 NOT_FOUND`

---

## 3. タグAPI

### 3.1 タグ一覧取得

**エンドポイント**

```
GET /api/tags
```

**クエリパラメータ**: なし（フェーズ1ではユーザーの全タグを返す）

**レスポンス例（200 OK）**

```json
{
  "items": [
    {
      "id": "tag-uuid-1",
      "name": "仕事",
      "created_at": "2026-04-01T10:00:00+09:00",
      "updated_at": "2026-04-01T10:00:00+09:00"
    },
    {
      "id": "tag-uuid-2",
      "name": "会議",
      "created_at": "2026-04-05T11:00:00+09:00",
      "updated_at": "2026-04-05T11:00:00+09:00"
    }
  ]
}
```

**ソート順**: `name` 昇順

---

### 3.2 タグ新規作成

**エンドポイント**

```
POST /api/tags
```

**リクエストボディ**

| フィールド | 型             | 必須 | 説明                |
|-----------|---------------|------|---------------------|
| `name`    | string (1-20) | ✅   | タグ名（ユーザー内ユニーク） |

**リクエスト例**

```json
{
  "name": "プライベート"
}
```

**レスポンス例（201 Created）**

```json
{
  "id": "tag-uuid-3",
  "name": "プライベート",
  "created_at": "2026-05-15T14:00:00+09:00",
  "updated_at": "2026-05-15T14:00:00+09:00"
}
```

**エラー**
- `400 VALIDATION_ERROR`: タグ名の文字数超過など
- `409 CONFLICT`: 同名タグが既に存在

---

### 3.3 タグ更新（リネーム）

**エンドポイント**

```
PUT /api/tags/{id}
```

**リクエストボディ**

```json
{
  "name": "プライベート（更新）"
}
```

**レスポンス例（200 OK）**

3.2 と同じ形式。

**エラー**
- `404 NOT_FOUND`
- `400 VALIDATION_ERROR`
- `409 CONFLICT`

---

### 3.4 タグ削除

**エンドポイント**

```
DELETE /api/tags/{id}
```

**レスポンス**: `204 No Content`

**エラー**: `404 NOT_FOUND`

**備考**: タグ削除時、`memo_tags` の関連レコードはCASCADEで削除される（メモ自体は削除されない）。

---

## 4. プロフィールAPI

### 4.1 プロフィール取得

**エンドポイント**

```
GET /api/profile
```

**レスポンス例（200 OK）**

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "display_name": "デフォルトユーザー",
  "bio": "フェーズ1用の仮ユーザーです",
  "avatar_url": null,
  "created_at": "2026-04-01T00:00:00+09:00",
  "updated_at": "2026-04-01T00:00:00+09:00"
}
```

---

### 4.2 プロフィール更新

**エンドポイント**

```
PUT /api/profile
```

**リクエストボディ**

| フィールド       | 型              | 必須 | 説明                |
|-----------------|----------------|------|---------------------|
| `display_name`  | string (1-50)  | ✅   | 表示名               |
| `bio`           | string (0-200) | ❌   | 自己紹介             |
| `avatar_url`    | string         | ❌   | アバター画像URL       |

**リクエスト例**

```json
{
  "display_name": "しん",
  "bio": "AIアプリエンジニア",
  "avatar_url": "https://example.com/avatar.png"
}
```

**レスポンス例（200 OK）**

4.1 と同じ形式。

**エラー**
- `400 VALIDATION_ERROR`

---

## 5. データスキーマ参照（Zod / Pydantic）

### 5.1 Memo

```typescript
// frontend/src/features/memo/schemas.ts
import { z } from "zod";

export const memoCreateSchema = z.object({
  title: z.string().min(1).max(100),
  body: z.string().max(10000).optional(),
  tag_ids: z.array(z.string().uuid()).max(10).optional(),
  is_pinned: z.boolean().optional(),
});

export const memoResponseSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  body: z.string().nullable(),
  is_pinned: z.boolean(),
  tags: z.array(z.object({
    id: z.string().uuid(),
    name: z.string(),
  })),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export type MemoCreate = z.infer<typeof memoCreateSchema>;
export type MemoResponse = z.infer<typeof memoResponseSchema>;
```

```python
# backend/app/schemas/memo.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class TagBrief(BaseModel):
    id: UUID
    name: str

class MemoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str | None = Field(default=None, max_length=10000)
    tag_ids: list[UUID] = Field(default_factory=list, max_length=10)
    is_pinned: bool = False

class MemoResponse(BaseModel):
    id: UUID
    title: str
    body: str | None
    is_pinned: bool
    tags: list[TagBrief]
    created_at: datetime
    updated_at: datetime
```

> 他のリソース（Tag、Profile）も同様の方針でZodとPydanticを並行定義する。

---

## 6. エンドポイント一覧（早見表）

| メソッド | パス                       | 概要                  | ステータス |
|---------|---------------------------|----------------------|-----------|
| GET     | `/api/memos`              | メモ一覧（検索・フィルタ含む） | 200       |
| POST    | `/api/memos`              | メモ新規作成           | 201       |
| GET     | `/api/memos/{id}`         | メモ詳細取得           | 200       |
| PUT     | `/api/memos/{id}`         | メモ更新               | 200       |
| DELETE  | `/api/memos/{id}`         | メモ削除               | 204       |
| PATCH   | `/api/memos/{id}/pin`     | ピン留めトグル         | 200       |
| GET     | `/api/tags`               | タグ一覧               | 200       |
| POST    | `/api/tags`               | タグ新規作成           | 201       |
| PUT     | `/api/tags/{id}`          | タグ更新               | 200       |
| DELETE  | `/api/tags/{id}`          | タグ削除               | 204       |
| GET     | `/api/profile`            | プロフィール取得       | 200       |
| PUT     | `/api/profile`            | プロフィール更新       | 200       |

---

## 7. 決定事項まとめ

| 項目               | 決定                                          |
|-------------------|----------------------------------------------|
| APIパス命名        | 複数形（`/memos`, `/tags`）                    |
| バージョニング      | FastAPI側で `/api/v1/`、BFF側で `/api/`         |
| 認証（フェーズ1）   | なし。サーバー側で固定 `DEFAULT_USER_ID` を使用 |
| エラーレスポンス形式 | `{ error: { code, message, details } }`       |
| ピン留めトグル      | 専用エンドポイント `PATCH /memos/{id}/pin`     |
| メモ更新方式        | PUT（全フィールド送信、部分更新ではない）         |
| 日時形式           | ISO 8601（タイムゾーン付き）                    |
| ページング         | オフセット方式（`limit` + `offset`）            |

---

## 8. 今後の検討事項

- [ ] OpenAPI仕様書（YAML/JSON）の自動生成方針
- [ ] フェーズ2での認証エンドポイント仕様（`/api/auth/login` 等）
- [ ] レート制限（必要に応じて）
- [ ] バルク操作（複数メモの一括削除など）の必要性
- [ ] 検索の全文検索化に伴うAPI仕様変更
