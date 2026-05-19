# フロント実装: プロフィール編集

## ゴール

`/profile` ルートでプロフィール（`display_name` / `bio` / `avatar_url`）を表示・編集できるようにする。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §3.8
- UIデザイン: [`../design/`](../design/)
- アーキテクチャ: [`../architecture.md`](../architecture.md) §3
- API仕様: [`../api-spec.md`](../api-spec.md) §4
- 先行タスク: [`profile-api.md`](./profile-api.md) / [`frontend-memo-crud.md`](./frontend-memo-crud.md)（共通基盤の流用）

## 前提・スコープ

- App Router の `/profile` 1ページのみ
- 機能固有のロジックは `frontend/src/features/profile/` に閉じる
- 共通基盤（`lib/api-client.ts` / `lib/backend-client.ts` / `components/ui/*`）は前タスクで整備済みの想定

## 影響範囲

| 領域 | 追加/変更ファイル |
|------|---|
| ルート | `app/profile/page.tsx` |
| BFF | `app/api/profile/route.ts` — GET / PUT |
| features | `features/profile/{api.ts, schemas.ts, types.ts}` |
| features components | `features/profile/components/ProfileForm.tsx` |
| features hooks | `features/profile/hooks/useProfileForm.ts` |
| tests | Zodスキーマ / hook / `ProfileForm` の Vitest テスト |

## テスト方針

- Zodスキーマの境界値（`display_name` 1-50 / `bio` 0-200）
- hook の保存処理（バリデーション → API呼び出し → 成功・失敗ハンドリング）
- `ProfileForm` の入力 → 保存ボタン押下の最小フロー

## サブタスク

### 1. スキーマ・API

- [ ] Zodスキーマ: `profileResponseSchema` / `profileUpdateSchema` + テスト
- [ ] `app/api/profile/route.ts` — GET / PUT
- [ ] `features/profile/api.ts` — `getProfile`, `updateProfile`

### 2. ProfileForm

- [ ] `ProfileForm` コンポーネント（`display_name` / `bio` / `avatar_url` の入力欄、保存ボタン）+ テスト
- [ ] `useProfileForm` hook（`useSWR('/api/profile')` で初期値プリフィル、バリデーション、保存時は `mutate('/api/profile')` でキャッシュ更新、`ApiError.code === "VALIDATION_ERROR"` のフィールド別表示）+ テスト
- [ ] 保存成功後はメモ一覧（`/`）に遷移する（`router.push('/')`）

### 3. ページ

- [ ] `app/profile/page.tsx` — サーバーコンポーネントで初期データ取得 → `ProfileForm` に渡す

### 4. 仕上げ

- [ ] ESLint / Prettier 通過
- [ ] ローカル起動して 表示 → 編集 → 保存 → 再読み込みで反映を手動確認
- [ ] `roadmap.md` の「フロント実装（プロフィール編集）」を `[x]` に更新

## 決定事項

- **保存成功後の遷移**: メモ一覧（`/`）に戻す。同ページ留まりのトースト等は実装しない
- **`avatar_url` のプレビュー表示**: フェーズ1スコープ外。入力欄のみ提供する

## オープンクエスチョン

- なし
