# フロント実装: メモCRUD画面

## ゴール

メモの一覧表示・新規作成・編集・削除・ピン留めトグルをフロントで実装する。バックエンドの `tags` / `memos` API 完了が前提。

## 関連ドキュメント

- 機能要件: [`../requirements.md`](../requirements.md) §3.2-3.5
- UIデザイン: [`../design/`](../design/)
- アーキテクチャ: [`../architecture.md`](../architecture.md) §3
- API仕様: [`../api-spec.md`](../api-spec.md) §2
- 先行タスク: [`tag-api.md`](./tag-api.md) / [`memo-crud.md`](./memo-crud.md) / [`memo-search.md`](./memo-search.md)

## 前提・スコープ

- App Router を使用（Pages Router は禁止）
- 機能固有のコンポーネント・hooks・型は `frontend/src/features/memo/` に閉じる
- 汎用UI（Button / Input / Modal等）は `components/ui/` に置く
- 状態管理: 初期描画はサーバーコンポーネント、クライアント側再フェッチは **SWR**、UI状態（モーダル開閉・フォーム入力・フィルタの一時状態）は **Zustand**（詳細は [`../architecture.md`](../architecture.md) §3.4）
- BFF（`app/api/...`）は薄いプロキシとし、ビジネスロジックを書かない

## 画面一覧

| ルート | 説明 |
|--------|------|
| `/` | メモ一覧（検索・タグフィルタ・ピン留めフィルタ） |
| `/memos/new` | メモ新規作成 |
| `/memos/[id]` | メモ詳細・編集 |

## 影響範囲

| 領域 | 追加/変更ファイル |
|------|---|
| ルート | `app/page.tsx`, `app/memos/new/page.tsx`, `app/memos/[id]/page.tsx` |
| BFF | `app/api/memos/route.ts`, `app/api/memos/[id]/route.ts`, `app/api/memos/[id]/pin/route.ts` |
| features | `features/memo/{api.ts, schemas.ts, types.ts}` |
| features components | `features/memo/components/{MemoCard, MemoList, MemoForm, PinButton}.tsx` |
| features hooks | `features/memo/hooks/{useMemoList, useMemoForm}.ts` |
| features (tag併用) | `features/tag/{api.ts, schemas.ts}` の最低限（一覧取得） |
| ストア | `stores/memoStore.ts`（検索クエリ・フィルタなどのUI状態） |
| lib | `lib/api-client.ts`, `lib/backend-client.ts` |
| tests | 各 hooks / Zodスキーマ / 主要コンポーネントの Vitest テスト |

## テスト方針

- **Zodスキーマ**: 境界値テスト（タイトル文字数、`tag_ids` 上限など）
- **hooks**: 副作用のない純粋関数化を優先し、Vitest で振る舞いを検証
- **コンポーネント**: 主要操作（入力 → 保存ボタン押下 → API呼び出し）と表示の最小限のテスト
- BFF と FastAPI 間はモック不可方針に従い、結合テストはローカル `npm run dev` + Docker Compose で手動確認

## サブタスク

### 1. 共通基盤

- [ ] `lib/api-client.ts` を作成（fetchラッパ）
  - エラーレスポンス（`{"error": {"code", "message", "details"}}`、[`../api-spec.md`](../api-spec.md) §1.4）をパースして共通の `ApiError` クラスに変換
  - 呼び出し側は `code`（`VALIDATION_ERROR` / `NOT_FOUND` / `CONFLICT` / `BAD_REQUEST` / `INTERNAL_SERVER_ERROR`）で分岐できるようにする
- [ ] `lib/backend-client.ts` を作成（Route Handler から FastAPI を呼ぶ）
- [ ] `components/ui/Modal.tsx` を作成（オーバーレイ + 中央寄せ、ESC / 外側クリックで閉じる）+ テスト
- [ ] `components/ui/ConfirmDialog.tsx` を作成（`Modal` を内包し、`title` / `message` / `confirmLabel` / `onConfirm` / `onCancel` を受ける汎用確認ダイアログ）+ テスト
  - 後続の [`frontend-tag-modal.md`](./frontend-tag-modal.md) のタグ削除確認、本タスクのメモ削除確認の両方で利用する
- [ ] Zodスキーマ: `memoCreateSchema` / `memoResponseSchema` / `memoListQuerySchema` + テスト

### 2. BFF（Route Handler）

- [ ] `app/api/memos/route.ts` — GET（一覧）/ POST（作成）
- [ ] `app/api/memos/[id]/route.ts` — GET / PUT / DELETE
- [ ] `app/api/memos/[id]/pin/route.ts` — PATCH
- [ ] 各ハンドラは FastAPI を叩いてレスポンスをそのまま返す薄い実装

### 3. features/memo の API ラッパ

- [ ] `features/memo/api.ts` — クライアントから BFF を呼ぶ関数群（`listMemos`, `getMemo`, `createMemo`, `updateMemo`, `deleteMemo`, `togglePin`）

### 4. 一覧画面

- [ ] `MemoCard` コンポーネント（タイトル / 本文100文字 / タグ / 更新日時 / ピン留めアイコン）+ テスト
- [ ] `MemoList` コンポーネント（`MemoCard` を並べる、ピン留め優先ソートはAPI側で保証されている前提）+ テスト
- [ ] `useMemoList` hook（検索クエリ・タグフィルタ・ピン留めフィルタの状態を `memoStore` に保持し、`useSWR` でキー `'/api/memos?...'` を組み立てて取得。検索クエリ `q` は 300ms デバウンスしてからキーに反映、[`../requirements.md`](../requirements.md) §3.5 準拠）+ テスト
- [ ] `app/page.tsx` — サーバーコンポーネントで初期データ取得、UI操作はクライアントコンポーネントに委譲

### 5. 作成・編集画面

- [ ] `MemoForm` コンポーネント（タイトル / 本文 / タグセレクタ呼び出し / ピン留めトグル）+ テスト
- [ ] `useMemoForm` hook（バリデーション + 保存）+ テスト
- [ ] `app/memos/new/page.tsx` — 新規作成
- [ ] `app/memos/[id]/page.tsx` — 編集（既存値をプリフィル、削除ボタン）
- [ ] 削除ボタン押下時は `ConfirmDialog`（共通基盤で作成済み）で確認 → 確定で `deleteMemo` を呼び、`mutate('/api/memos')` でメモ一覧キャッシュを無効化してから一覧へ遷移

### 6. ピン留め

- [ ] `PinButton` コンポーネント（SWR の `mutate(key, optimisticData, { revalidate: true })` で楽観的UI更新、失敗時はサーバー結果で巻き戻し）+ テスト

### 7. 仕上げ

- [ ] ESLint / Prettier 通過: `npm run lint && npm run format`
- [ ] ローカル起動して 一覧 → 作成 → 編集 → 削除 → ピン留めの一連を手動確認
- [ ] `roadmap.md` の「フロント実装（メモCRUD画面）」を `[x]` に更新

## 設計メモ

- タグセレクタ本体は次タスク（[`frontend-tag-modal.md`](./frontend-tag-modal.md)）で `features/tag/` に作る。本タスクでは「タグ一覧を取得して `TagSelector` に渡す」呼び出し側のみを用意し、`TagSelector` 本体は最低限のプレースホルダで先行実装してもよい
- ルーティング遷移後のサーバーコンポーネントでのデータ取得は `cache: 'no-store'` を基本に（編集後の即時反映のため）
- SWR の `fetcher` は `lib/api-client.ts` を流用し、`ApiError` を throw する形に揃える（SWR の `error` でハンドリングできるように）

## 決定事項

- **データ取得**: クライアント側再フェッチは **SWR** を使用（CLAUDE.md §3 / [`../architecture.md`](../architecture.md) §3.4）。素の `fetch` + Zustand での自前実装はしない。
  - 採用理由: 検索クエリ変更時の自動再フェッチ・並行リクエスト競合の自動解決・別機能起因のキャッシュ無効化（`mutate(key)`）が必要なため
  - キャッシュキーは URL 文字列（`/api/memos?q=...&tag_ids=...`）を基本にする

## オープンクエスチョン

- なし
