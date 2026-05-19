# フロント実装: タグ管理モーダル

## ゴール

タグの一覧表示・新規作成・リネーム・削除を行うモーダルを実装し、メモ作成・編集画面の `TagSelector` 内および一覧画面のタグフィルタ近くから開けるようにする。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §3.7
- UIデザイン: [`../design/`](../design/)
- アーキテクチャ: [`../architecture.md`](../architecture.md) §3
- API仕様: [`../api-spec.md`](../api-spec.md) §3
- 先行タスク: [`tag-api.md`](./tag-api.md) / [`frontend-memo-crud.md`](./frontend-memo-crud.md)

## 前提・スコープ

- タグ機能のフロント実装は `frontend/src/features/tag/` に閉じる
- モーダルUI（`components/ui/Modal` / `components/ui/ConfirmDialog`）は [`frontend-memo-crud.md`](./frontend-memo-crud.md) の共通基盤サブタスクで作成済みの前提
- タグの作成・削除はモーダル内で完結。メモ保存時の自動タグ作成はしない（既存タグのみ紐付け可能）
- タグ削除時は紐付くメモ側の表示にも反映が必要 → 削除完了後にメモ一覧を再フェッチ

## 影響範囲

| 領域 | 追加/変更ファイル |
|------|---|
| BFF | `app/api/tags/route.ts`, `app/api/tags/[id]/route.ts` |
| features | `features/tag/{api.ts, schemas.ts, types.ts}` |
| features components | `features/tag/components/{TagSelector, TagManageModal, TagListItem, TagCreateForm}.tsx` |
| features hooks | `features/tag/hooks/{useTagList, useTagMutations}.ts` |
| 共通UI | `components/ui/Modal.tsx` / `components/ui/ConfirmDialog.tsx` を利用（[`frontend-memo-crud.md`](./frontend-memo-crud.md) で作成済みの前提） |
| ストア | `stores/tagStore.ts`（モーダル開閉状態、選択中タグ） |
| tests | Zodスキーマ / hooks / 主要コンポーネントの Vitest テスト |

## テスト方針

- Zodスキーマ: タグ名の境界値（1-20文字）
- hooks: 作成・リネーム・削除後にローカル状態が更新されることをテスト
- コンポーネント: モーダル開閉、作成フォーム送信、削除確認の最小フロー

## サブタスク

### 1. 共通基盤

- [ ] Zodスキーマ: `tagCreateSchema` / `tagUpdateSchema` / `tagResponseSchema` + テスト

### 2. BFF（Route Handler）

- [ ] `app/api/tags/route.ts` — GET / POST
- [ ] `app/api/tags/[id]/route.ts` — PUT / DELETE

### 3. features/tag の API ラッパ

- [ ] `features/tag/api.ts` — `listTags`, `createTag`, `renameTag`, `deleteTag`

### 4. TagManageModal

- [ ] `TagListItem`（タグ名表示 / リネーム / 削除ボタン）+ テスト
- [ ] `TagCreateForm`（新規作成フォーム + `ApiError.code === "CONFLICT"` をインラインで表示）+ テスト
- [ ] `TagManageModal`（一覧 + 新規作成フォームを内包）+ テスト
- [ ] `useTagList`（`useSWR('/api/tags')`）/ `useTagMutations`（作成・リネーム・削除後に関連キャッシュを `mutate` で無効化）hooks + テスト
- [ ] 削除確認ダイアログ（共通の `ConfirmDialog` を利用、紐付くメモから紐付けが外れる旨を `message` で表示）

### 5. TagSelector との連携

- [ ] `TagSelector` 本体を完成させる（メモ作成・編集画面で利用、既存タグから複数選択）
- [ ] `TagSelector` 内に「タグを新規作成」ボタンを設置 → `TagManageModal` を開く
- [ ] メモ一覧画面のタグフィルタ近くに「タグ管理」ボタンを設置 → 同モーダルを開く

### 6. 削除後の再同期

- [ ] タグ削除後、SWR の `mutate('/api/memos')` でメモ一覧キャッシュを無効化し再フェッチさせる。同様にタグ一覧（`/api/tags`）も無効化
- [ ] テスト: 削除 → `mutate` が呼ばれる / SWRキャッシュが更新されることを検証

### 7. 仕上げ

- [ ] ESLint / Prettier 通過
- [ ] ローカル起動して 一覧 → 作成 → リネーム → 削除（メモ側からタグが消える）を手動確認
- [ ] `roadmap.md` の「フロント実装（タグ管理モーダル）」を `[x]` に更新

## 決定事項

- **削除確認ダイアログの件数表示はしない**（フェーズ1スコープ外）。「紐付くメモから紐付けが外れます」程度の固定文言のみ表示する。件数を出すには削除前にAPI追加が必要なため、必要になったフェーズで再検討する。

## オープンクエスチョン

- なし
