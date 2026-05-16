# Frontend (Next.js)

メモアプリのフロントエンド。Next.js (App Router) + TypeScript + Tailwind CSS。

## セットアップ

```bash
cd frontend
npm install
```

## 主要スクリプト

| コマンド | 用途 |
|---|---|
| `npm run dev` | 開発サーバー起動（http://localhost:3000） |
| `npm run build` | プロダクションビルド |
| `npm start` | プロダクションサーバー起動 |
| `npm test` | Vitestでテスト実行 |
| `npm run test:watch` | Vitest watchモード |
| `npm run lint` | ESLintで検査 |
| `npm run format` | Prettierでフォーマット |
| `npm run format:check` | Prettierのチェックのみ（CI用） |

## ディレクトリ構成

詳細は [`../docs/architecture.md`](../docs/architecture.md) を参照。

```
frontend/
├── src/
│   ├── app/                # App Router
│   ├── components/         # 汎用UI（今後追加）
│   ├── features/           # 機能単位の集約（今後追加）
│   ├── lib/                # 汎用ユーティリティ
│   └── stores/             # Zustand（今後追加）
├── vitest.config.mts
├── vitest.setup.mts
├── eslint.config.mjs
├── .prettierrc.json
└── package.json
```

## バックエンドとの連携

`/api/*` の Route Handler 経由で FastAPI を呼ぶ BFF 構成。
バックエンドは `docker compose up backend` で起動する。
