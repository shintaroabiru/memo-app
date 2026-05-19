# タグ管理 API

## ゴール

タグの CRUD API（一覧 / 作成 / リネーム / 削除）を TDD で実装し、後続のメモCRUD APIから「既存タグへの紐付け」を行える状態にする。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §2.2 / §3.7
- API仕様: [`../api-spec.md`](../api-spec.md) §3 タグAPI
- DB設計: [`../db-schema.md`](../db-schema.md) §3.3 `tags`
- アーキテクチャ: [`../architecture.md`](../architecture.md)

## 前提・スコープ

- 認証はフェーズ2のため、ユーザーは **仮ユーザー（シード済み）固定** で扱う
- `tags` テーブル・SQLAlchemyモデルは既に存在（[backend/app/models/tag.py](../../backend/app/models/tag.py)）
- フィールド: `id` (UUID) / `user_id` (UUID, FK) / `name` (varchar 1-20) / `created_at` / `updated_at`
- UNIQUE制約: `(user_id, name)` — 同名タグはユーザー内で重複不可
- 削除時、`memo_tags` は CASCADE で消える（メモ本体は残る）

## 影響範囲

| レイヤー | 追加/変更ファイル |
|----------|---|
| schemas | `backend/app/schemas/tag.py`（新規） |
| repositories | `backend/app/repositories/tag_repository.py`（新規） |
| services | `backend/app/services/tag_service.py`（新規） |
| api | `backend/app/api/v1/tags.py`（新規）, `backend/app/api/v1/__init__.py`（ルータ登録） |
| main | `backend/app/main.py`（v1ルータ取り込み） |
| 依存性 | `backend/app/api/deps.py`（DBセッション / 仮ユーザーID取得用Depends、必要なら新規） |
| tests | `backend/tests/repositories/test_tag_repository.py`, `backend/tests/services/test_tag_service.py`, `backend/tests/api/test_tags.py` |

## テスト方針

- Repository層: テスト用Postgres（既存の `conftest.py` のフィクスチャを利用）で実DB操作を検証
- Service層: Repositoryを直接呼ぶ統合テスト寄り（モックは使わない方針。CLAUDE.md準拠）
- API層: FastAPI `TestClient` でエンドポイント単位の入出力・ステータスコードを検証
- 異常系を必ず1ケース以上含める（404 / 409 / 400）

## サブタスク（TDDの1サイクル ≒ 1コミット）

### 0. 共通エラー基盤（最初に実装）

- [ ] `backend/app/core/errors.py` を新規作成し、以下を定義
  - `AppException`（`code: str`, `http_status: int`, `message: str`, `details: list[dict] | None`）
  - `NotFoundError`（404 / `NOT_FOUND`） / `ConflictError`（409 / `CONFLICT`） / `BadRequestError`（400 / `BAD_REQUEST`）
- [ ] `backend/app/main.py` に2つの例外ハンドラを登録
  - `AppException` → `api-spec.md` §1.4 の形式（`{"error": {"code", "message", "details"}}`）でレスポンス
  - FastAPI標準 `RequestValidationError` → 同形式で `code: "VALIDATION_ERROR"`
- [ ] ハンドラのテスト（ダミーのテスト用エンドポイントを立て、各例外型ごとにステータスコード + ボディ形をassert）

> Service層はHTTPを知らず、`raise NotFoundError(...)` のように例外を投げる。API層では原則 try/except を書かない（ハンドラに任せる）。

### 1. Pydantic スキーマ

- [ ] `TagCreate` / `TagUpdate` / `TagRead` を定義（name: 1-20文字）
- [ ] スキーマのバリデーションテスト（境界値: 0文字 / 1文字 / 20文字 / 21文字）

### 2. Repository層

- [ ] `list_by_user(user_id)` — name 昇順で全件 + テスト
- [ ] `create(user_id, name)` — 重複時は IntegrityError を投げる + テスト
- [ ] `get(tag_id, user_id)` — 他ユーザーのタグは取得不可 + テスト
- [ ] `update(tag, name)` — リネーム + テスト（同名衝突含む）
- [ ] `delete(tag)` — 物理削除、`memo_tags` がCASCADEで消えることをテスト

### 3. Service層

> 404 は `NotFoundError`、409 は `ConflictError` を `raise` する（共通エラー基盤を利用）。

- [ ] `list_tags(user_id)` + テスト
- [ ] `create_tag(user_id, name)` — 同名衝突時に `ConflictError` を投げる + テスト
- [ ] `rename_tag(user_id, tag_id, name)` — `NotFoundError` / `ConflictError` の各パターン + テスト
- [ ] `delete_tag(user_id, tag_id)` — `NotFoundError` パターン + テスト

### 4. API層

- [ ] `GET /api/v1/tags` — 200 + テスト
- [ ] `POST /api/v1/tags` — 201 / 400 / 409 + テスト
- [ ] `PUT /api/v1/tags/{id}` — 200 / 404 / 409 / 400 + テスト
- [ ] `DELETE /api/v1/tags/{id}` — 204 / 404 + テスト

### 5. 仕上げ

- [ ] `main.py` に v1 ルータを取り込み、`/openapi.json` で4エンドポイントが見えることを確認
- [ ] Ruff: `ruff check . && ruff format .` を通す
- [ ] `roadmap.md` の「タグ管理 API」を `[x]` に更新

## 決定事項

- **仮ユーザーIDの取り回し**: `Depends(get_current_user_id)` で関数化し、中身は `settings.DEV_USER_ID`（環境変数経由）から仮ユーザーUUIDを返す。
  - 配置: `backend/app/api/deps.py`
  - フェーズ2で認証を入れる際は、この関数の中身だけをトークン検証に差し替える（エンドポイント側のシグネチャは変えない）
  - テストでは `app.dependency_overrides[get_current_user_id]` で別ユーザーに差し替えて権限分離を検証できるようにする
- **共通エラーレスポンス**: 本タスクのサブタスク0で `backend/app/core/errors.py` に共通基盤を実装する。
  - Service層は HTTP を知らず `AppException` 派生例外を `raise` するだけ
  - API層では原則 try/except を書かず、共通ハンドラに整形を委ねる
  - レスポンス形は [`../api-spec.md`](../api-spec.md) §1.4 準拠（`{"error": {"code", "message", "details"}}`）
  - 後続のメモCRUD / メモ一覧・検索 / プロフィール編集APIはこの基盤を前提とする

## オープンクエスチョン

- なし（決定事項に反映済み）
