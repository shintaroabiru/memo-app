# ロードマップ / 進捗

プロジェクトの現在地と今後の予定を管理するドキュメントです。
進捗はこのファイルを更新して可視化します。

---

## フェーズ1（実装中）

- [x] プロジェクト初期セットアップ（Next.js / FastAPI / Docker Compose）
- [x] DBマイグレーション（初期スキーマ + 仮ユーザーシード）
- [x] タグ管理 API → [`tasks/tag-api.md`](./tasks/tag-api.md)
- [x] メモCRUD API（タグ紐付け含む） → [`tasks/memo-crud.md`](./tasks/memo-crud.md)
- [x] メモ一覧・検索 API（タグフィルタ含む） → [`tasks/memo-search.md`](./tasks/memo-search.md)
- [x] プロフィール編集 API → [`tasks/profile-api.md`](./tasks/profile-api.md)
- [ ] フロント実装（メモCRUD画面） → [`tasks/frontend-memo-crud.md`](./tasks/frontend-memo-crud.md)
- [ ] フロント実装（タグ管理モーダル） → [`tasks/frontend-tag-modal.md`](./tasks/frontend-tag-modal.md)
- [ ] フロント実装（プロフィール編集） → [`tasks/frontend-profile.md`](./tasks/frontend-profile.md)

## フェーズ2（未着手）

- [ ] ユーザー登録
- [ ] 認証機能
- [ ] 既存データの実ユーザーへの移行
