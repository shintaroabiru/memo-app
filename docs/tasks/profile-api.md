# プロフィール編集 API

## ゴール

プロフィールの取得 / 更新 API（`GET /api/v1/profile` / `PUT /api/v1/profile`）を TDD で実装する。フェーズ1では仮ユーザーのプロフィールのみを対象とする。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §2.3 / §3.8
- API仕様: [`../api-spec.md`](../api-spec.md) §4
- DB設計: [`../db-schema.md`](../db-schema.md) §3.1 `user_profiles`
- 先行タスク: [`tag-api.md`](./tag-api.md)（`Depends(get_current_user_id)` の方針を踏襲）

## 前提・スコープ

- 認証はフェーズ2のため、`Depends(get_current_user_id)` で仮ユーザーUUIDを取得
- **共通エラー基盤**（`AppException` 派生例外と FastAPI ハンドラ）は [`tag-api.md`](./tag-api.md) サブタスク0で実装済みの前提
- 取得対象は **ログイン中ユーザー自身のみ**（他ユーザーIDをパスで受けない）
- `user_profiles` テーブル・SQLAlchemyモデルは既に存在（[backend/app/models/user_profile.py](../../backend/app/models/user_profile.py)）
- フィールド: `id` / `display_name` (1-50) / `bio` (0-200) / `avatar_url` (任意) / `created_at` / `updated_at`
- 更新は **全置換**（`PUT`）。部分更新ではない

## 影響範囲

| レイヤー | 追加/変更ファイル |
|----------|---|
| schemas | `backend/app/schemas/profile.py`（新規: `ProfileUpdate` / `ProfileRead`） |
| repositories | `backend/app/repositories/profile_repository.py`（新規） |
| services | `backend/app/services/profile_service.py`（新規） |
| api | `backend/app/api/v1/profile.py`（新規）, ルータ登録 |
| tests | `backend/tests/repositories/test_profile_repository.py`, `backend/tests/services/test_profile_service.py`, `backend/tests/api/test_profile.py` |

## テスト方針

- Repository層: 実DBで取得 / 更新を検証
- Service層: 例外処理（仮ユーザーが見つからない異常系）
- API層: TestClient でステータスコード / 入出力 / バリデーションを検証

## サブタスク

### 1. Pydantic スキーマ

- [ ] `ProfileRead` / `ProfileUpdate` を定義
- [ ] バリデーションテスト
  - `display_name`: 0文字NG / 1文字OK / 50文字OK / 51文字NG
  - `bio`: 省略可 / 200文字OK / 201文字NG
  - `avatar_url`: 任意（URL形式は当面緩めに `str` で受ける）

### 2. Repository層

- [ ] `get(user_id)` + テスト
- [ ] `update(profile, data)` — `display_name` / `bio` / `avatar_url` を全置換 + テスト

### 3. Service層

> 仮ユーザーは必ず存在する前提だが、不在時は `NotFoundError` を `raise`（共通ハンドラが404に整形）。

- [ ] `get_profile(user_id)` — 不在時は `NotFoundError` + テスト
- [ ] `update_profile(user_id, payload)` + テスト

### 4. API層

- [ ] `GET /api/v1/profile` — 200 + テスト
- [ ] `PUT /api/v1/profile` — 200 / 400 + テスト

### 5. 仕上げ

- [ ] `/openapi.json` で2エンドポイントが見えることを確認
- [ ] Ruff: `ruff check . && ruff format .` を通す
- [ ] `roadmap.md` の「プロフィール編集 API」を `[x]` に更新

## 決定事項

- **`avatar_url` の型（フェーズ1）**: `str` で受ける（URL形式バリデーション `HttpUrl` は使わない）。
  - 理由: フェーズ1は仮ユーザー1名のみで最小要件。厳密なURL検証は不要
  - フェーズ2での再検討事項: 複数ユーザーが登録できるようになった際に、アバターURLの管理方針（外部URL許可 / 自前ストレージ / 画像アップロード対応など）を改めて設計する。型バリデーションもその段階で見直す

## オープンクエスチョン

- なし
