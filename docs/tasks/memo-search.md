# メモ一覧・検索 API（タグフィルタ含む）

## ゴール

`GET /api/v1/memos` を TDD で実装する。キーワード検索 / タグAND絞り込み / ピン留めフィルタ / ページネーション / 固定ソートに対応する。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §3.3 メモ一覧
- API仕様: [`../api-spec.md`](../api-spec.md) §2.1
- DB設計: [`../db-schema.md`](../db-schema.md) §3.2 `memos` / §5.3 タグAND絞り込み / §5.4 検索+タグ併用
- 先行タスク: [`memo-crud.md`](./memo-crud.md)（モデル・スキーマ・Repository基盤が完了している前提）

## 前提・スコープ

- 認証はフェーズ2のため、`Depends(get_current_user_id)` で仮ユーザーUUIDを取得
- **共通エラー基盤**（`AppException` 派生例外と FastAPI ハンドラ）は [`tag-api.md`](./tag-api.md) サブタスク0で実装済みの前提。本タスクではクエリパラメータの `RequestValidationError` を共通ハンドラに任せ、API層で try/except は書かない
- 本タスクで実装するエンドポイントは **`GET /api/v1/memos` のみ**
- メモの詳細取得/作成/更新/削除/ピン留めは [`memo-crud.md`](./memo-crud.md) で完了済み

## 仕様サマリ

### クエリパラメータ

| 名前 | 型 | デフォルト | 備考 |
|------|---|---|---|
| `q` | string | なし | タイトル + 本文の **部分一致**（大小無視） |
| `tag_ids` | UUID[] | `[]` | **AND条件**（全タグを含むメモのみ） |
| `pinned` | boolean | なし（指定時のみ絞り込み） | `true` でピン留めのみ |
| `limit` | int | 20 | 最大100 |
| `offset` | int | 0 | 0以上 |

### ソート

固定: `is_pinned DESC, updated_at DESC`

### レスポンス

`{ items: MemoRead[], total: int, limit: int, offset: int }`
`items[].tags` は `name` 昇順（memo-crud と同じ整形ルール）

## 影響範囲

| レイヤー | 追加/変更ファイル |
|----------|---|
| schemas | `backend/app/schemas/memo.py`（`MemoListQuery`, `MemoListResponse` を追加） |
| repositories | `backend/app/repositories/memo_repository.py`（`search` メソッド追加） |
| services | `backend/app/services/memo_service.py`（`list_memos` 追加） |
| api | `backend/app/api/v1/memos.py`（`GET /` ハンドラ追加） |
| tests | `backend/tests/repositories/test_memo_repository.py`, `backend/tests/services/test_memo_service.py`, `backend/tests/api/test_memos.py` |

## テスト方針

- Repository層: 条件の組み合わせ（検索 / タグAND / ピン留め / ページネーション / ソート）を実DBで検証
- Service層: クエリパラメータ → Repository呼び出しのマッピングと `total` の整合
- API層: クエリ文字列の解釈と異常系（不正なUUID、`limit` 超過など）

## サブタスク（TDDの1サイクル ≒ 1コミット）

### 1. スキーマ追加

- [ ] `MemoListQuery`（`q`, `tag_ids`, `pinned`, `limit`, `offset`）+ バリデーションテスト
  - `limit`: 0NG / 1OK / 100OK / 101NG
  - `offset`: 負数NG
  - `tag_ids`: UUID不正NG / 上限は設けない（一覧側は10件制限は不要）
- [ ] `MemoListResponse`（`items`, `total`, `limit`, `offset`）

### 2. Repository層: `search`

- [ ] **基本（条件なし）**: ユーザーの全メモが `is_pinned DESC, updated_at DESC` で返る + `total` 一致
- [ ] **ページネーション**: `limit` / `offset` が効く / `total` は全件数を返す
- [ ] **キーワード `q`**: タイトル一致 / 本文一致 / ヒットなし / 大小無視
- [ ] **タグAND**: 1タグ / 2タグAND / 該当なし（`db-schema.md` §5.3 の GROUP BY + HAVING 方式）
- [ ] **`pinned=true`**: ピン留めのみ / 未指定時はピン留め有無を問わない
- [ ] **複合条件**: `q` + `tag_ids` + `pinned` の同時指定
- [ ] **他ユーザー分離**: 他ユーザーのメモが混ざらない
- [ ] `selectinload(Memo.tags)` で N+1 を避ける

### 3. Service層: `list_memos`

- [ ] クエリ → Repository呼び出し + `MemoListResponse` 組み立て + テスト
- [ ] `items[].tags` の `name` 昇順を保証 + テスト

### 4. API層: `GET /api/v1/memos`

- [ ] 条件なし 200 + テスト
- [ ] `q` / `tag_ids`（複数指定の `?tag_ids=a&tag_ids=b` 形式）/ `pinned` / `limit` / `offset` の各クエリ反映 + テスト
- [ ] 400: `limit > 100` / `offset < 0` / 不正UUID + テスト

### 5. 仕上げ

- [ ] `/openapi.json` でクエリパラメータが正しく見えることを確認
- [ ] Ruff: `ruff check . && ruff format .` を通す
- [ ] `roadmap.md` の「メモ一覧・検索 API（タグフィルタ含む）」を `[x]` に更新

## 設計メモ

- **タグAND の実装**: サブクエリで `memo_tags` を `tag_id IN (...)` で集計し、`HAVING COUNT(DISTINCT tag_id) = :n` のメモIDを抽出 → 本クエリで `memos.id IN (...)` で絞る（`db-schema.md` §5.3 に準拠）
- **キーワード検索**: 当面は `ILIKE '%q%'` で実装（フェーズ1スコープ）。将来全文検索に置き換える際は Repository 内で完結させる
- **`total` の取りまわし**: `items` 取得とは別に `SELECT COUNT(*)` を発行する素直な実装にする（最適化は計測してから）
- **ソートの安定化**: `updated_at` が同値の場合に備えて `id DESC` を末尾タイブレーカに入れる

## 決定事項

- **`q` の正規化（フェーズ1）**: **前後空白トリムのみ実施** する。トリム後に空文字となった場合は「未指定」と同じ扱い（フィルタを掛けない）。
  - 全角/半角変換や表記ゆれ対応（全角空白の扱いを含む）はフェーズ2以降で検討する
  - 配置: Service層で `q.strip()` を行ってから Repository に渡す（半角空白のみ対象）
  - テスト: 「前後に半角空白を含むキーワード → トリム後の語で一致」「半角空白のみ / 空文字 → フィルタなしと同じ結果」を含める

## オープンクエスチョン

- なし
