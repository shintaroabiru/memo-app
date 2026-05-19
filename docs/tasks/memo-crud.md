# メモCRUD API（タグ紐付け含む）

## ゴール

メモの詳細取得 / 新規作成 / 更新 / 削除 / ピン留めトグルを TDD で実装する。タグとの多対多紐付け（`tag_ids` での既存タグ参照）まで本タスクでカバーする。
一覧・検索は次タスク（[`memo-search.md`](./memo-search.md)）で扱う。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §2.1 / §3.2-3.5
- API仕様: [`../api-spec.md`](../api-spec.md) §2.2-2.6
- DB設計: [`../db-schema.md`](../db-schema.md) §3.2 `memos` / §3.4 `memo_tags`
- 先行タスク: [`tag-api.md`](./tag-api.md)（タグ管理APIが完了している前提）

## 前提・スコープ

- 認証はフェーズ2のため、`Depends(get_current_user_id)` で仮ユーザーUUIDを取得（[`tag-api.md`](./tag-api.md) の決定事項に従う）
- **共通エラー基盤**（`backend/app/core/errors.py`、`AppException` 派生例外と FastAPI ハンドラ）は [`tag-api.md`](./tag-api.md) サブタスク0で実装済みの前提。本タスクは `NotFoundError` / `BadRequestError` を `raise` するだけ
- `memos` / `memo_tags` テーブル・SQLAlchemyモデルは既に存在
- 本タスクで実装するエンドポイント:
  - `GET /api/v1/memos/{id}` — 詳細取得
  - `POST /api/v1/memos` — 新規作成
  - `PUT /api/v1/memos/{id}` — 全置換更新（部分更新ではない）
  - `DELETE /api/v1/memos/{id}` — 物理削除（`memo_tags` はCASCADE）
  - `PATCH /api/v1/memos/{id}/pin` — ピン留めトグル
- **本タスクのスコープ外**: `GET /api/v1/memos`（一覧・検索）→ 次タスク

## タグ紐付けの仕様

- 入力は **既存タグIDの配列**（最大10件）。未登録タグの自動作成はしない
- 存在しない `tag_ids` を1つでも含む → `400 BAD_REQUEST`
- 他ユーザー所有の `tag_ids` を含む → `400 BAD_REQUEST`（存在しないものとして扱う）
- 更新時は「全置換」: リクエストの `tag_ids` を真として `memo_tags` を差し替える

## 影響範囲

| レイヤー | 追加/変更ファイル |
|----------|---|
| schemas | `backend/app/schemas/memo.py`（新規: `MemoCreate` / `MemoRead` / `MemoPinUpdate` / `TagBrief`）。PUT のリクエストボディは POST と同一形式のため `MemoCreate` を流用する（別スキーマは定義しない） |
| repositories | `backend/app/repositories/memo_repository.py`（新規） |
| services | `backend/app/services/memo_service.py`（新規） |
| api | `backend/app/api/v1/memos.py`（新規）, ルータ登録 |
| tests | `backend/tests/repositories/test_memo_repository.py`, `backend/tests/services/test_memo_service.py`, `backend/tests/api/test_memos.py` |

## テスト方針

- Repository層: 実DBで `memos` + `memo_tags` の同時操作（作成・差し替え・削除のCASCADE）を検証
- Service層: タグ存在検証・全置換ロジック・他ユーザー所有タグの除外を検証
- API層: TestClient でステータスコード / レスポンス形状 / 主要エラーケースを検証
- ピン留めトグルは `updated_at` が更新されることもテスト

## サブタスク（TDDの1サイクル ≒ 1コミット）

### 1. Pydantic スキーマ

- [ ] `TagBrief`（`id`, `name`）、`MemoCreate`、`MemoRead`、`MemoPinUpdate` を定義（PUT は `MemoCreate` を流用するため `MemoUpdate` は定義しない）
- [ ] バリデーションテスト
  - `title`: 0文字NG / 1文字OK / 100文字OK / 101文字NG
  - `body`: 省略可 / 10000文字OK / 10001文字NG
  - `tag_ids`: 重複時の扱い（重複は弾く想定） / 11件目NG / UUID不正NG
  - `is_pinned`: 省略時 `false`

### 2. Repository層

- [ ] `get(memo_id, user_id)` — 他ユーザーのメモは取得不可 + テスト
- [ ] `create(user_id, data, tag_ids)` — `memos` insert + `memo_tags` bulk insert + テスト
- [ ] `replace(memo, data, tag_ids)` — 本体更新 + `memo_tags` を削除して再挿入 + テスト
- [ ] `delete(memo)` — 物理削除、`memo_tags` がCASCADEで消えることをテスト
- [ ] `update_pinned(memo, is_pinned)` — `is_pinned` と `updated_at` を更新 + テスト
- [ ] `find_user_tags(user_id, tag_ids)` — 指定IDのうちユーザー所有タグだけ返す（タグ存在検証用）+ テスト

### 3. Service層

> 404 は `NotFoundError`、存在しない/他ユーザー所有の `tag_ids` は `BadRequestError` を `raise`（共通エラー基盤を利用）。

- [ ] `get_memo(user_id, memo_id)` — `NotFoundError` パターン含む + テスト
- [ ] `create_memo(user_id, payload)` — タグ存在検証 → 不足あれば `BadRequestError` + テスト
- [ ] `update_memo(user_id, memo_id, payload)` — `NotFoundError` / `BadRequestError` + テスト
- [ ] `delete_memo(user_id, memo_id)` — `NotFoundError` パターン + テスト
- [ ] `toggle_pin(user_id, memo_id, is_pinned)` — `NotFoundError` パターン + テスト

### 4. API層

- [ ] `GET /api/v1/memos/{id}` — 200 / 404 + テスト
- [ ] `POST /api/v1/memos` — 201 / 400 (validation) / 400 (invalid tag_ids) + テスト
- [ ] `PUT /api/v1/memos/{id}` — 200 / 404 / 400 + テスト
- [ ] `DELETE /api/v1/memos/{id}` — 204 / 404 + テスト
- [ ] `PATCH /api/v1/memos/{id}/pin` — 200 / 404 + テスト（レスポンスは `id` / `is_pinned` / `updated_at` のみ）

### 5. 仕上げ

- [ ] `/openapi.json` で5エンドポイントが見えることを確認
- [ ] Ruff: `ruff check . && ruff format .` を通す
- [ ] `roadmap.md` の「メモCRUD API（タグ紐付け含む）」を `[x]` に更新

## 設計メモ

- レスポンス整形時の N+1 を避けるため、`memo.tags` 取得は `selectinload(Memo.tags)` を基本にする
- `MemoRead` の `tags` は `name` 昇順で返す（[`../api-spec.md`](../api-spec.md) §2.1-2.2 に準拠、タグ一覧APIと同じソートルール）。ORDERは DB の `ORDER BY name ASC`（デフォルトコレーション）で行う
- タグ存在検証は Service 層に閉じる（Repository が「不足タグID」を返し、Service が例外化）

## オープンクエスチョン

- なし（タグAPIで決まった方針を踏襲）。発生したら本セクションに追記する。
