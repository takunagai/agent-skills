# deploy-nextjs-cloudflare

**Next.js + OpenNext 構成専用**の Cloudflare Workers デプロイ自動化スキルです。`@opennextjs/cloudflare` で Next.js アプリをビルドし、Wrangler で Cloudflare Workers へデプロイする一連の流れ（状態確認 → ビルド確認 → プッシュ → デプロイ → 確認）を自動実行します。本番環境（production）とプレビュー環境（preview）に対応します。

> **適用範囲の注意**: Astro 構成のデプロイには別スキル **deploy-astro-cloudflare** を使用してください。両者ともトリガー語が近いため、対象プロジェクトのフレームワークを必ず確認してから実行します。

---

## 対応構成

| 項目 | 内容 |
|------|------|
| フレームワーク | Next.js |
| アダプター | `@opennextjs/cloudflare`（OpenNext） |
| デプロイ先 | Cloudflare Workers |
| デプロイツール | Wrangler |
| 対応環境 | production / preview |

---

## インストール

このリポジトリを clone し、スキル本体（`skills/deploy-nextjs-cloudflare`）を各エージェントのスキルディレクトリへ symlink します。実体は 1 つ、参照を複数張る方式です。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets
ln -s /Users/$USER/Projects/agent-assets/skills/deploy-nextjs-cloudflare ~/.agents/skills/deploy-nextjs-cloudflare
ln -s ../../.agents/skills/deploy-nextjs-cloudflare ~/.claude/skills/deploy-nextjs-cloudflare
```

> Codex など他のエージェントは `~/.agents/skills/deploy-nextjs-cloudflare` を直接読みます。Claude Code は `~/.claude/skills/` を経由して同じ実体を参照します。

スキル本体の構成は次の通りです（人間用マニュアルである本ファイルは、スキル本体の外＝`docs/` に置いています）。

```
skills/deploy-nextjs-cloudflare/
├── SKILL.md          # スキル定義（Claude がトリガー時に読む）
└── scripts/
    └── deploy.sh     # デプロイ自動化スクリプト（状態確認〜デプロイ〜確認）
```

---

## クイックスタート

```bash
# 本番環境にデプロイ（デフォルト）
/deploy-nextjs-cloudflare
/deploy-nextjs-cloudflare production

# プレビュー環境にデプロイ
/deploy-nextjs-cloudflare preview

# ビルドチェックを省略（緊急時のみ）
/deploy-nextjs-cloudflare production --skip-build
```

自然言語でも発動します。「Next.js をデプロイして」「本番に反映」「Cloudflare にデプロイ」「プレビューにデプロイ」など。

---

## 使い方

### 本番 / プレビューの切り替え

第 1 引数で環境を指定します。省略時は `production` です。

| コマンド | 動作 |
|----------|------|
| `/deploy-nextjs-cloudflare` または `/deploy-nextjs-cloudflare production` | 本番環境にデプロイ（`npm run deploy:production`） |
| `/deploy-nextjs-cloudflare preview` | プレビュー環境にデプロイ（`npm run deploy:preview`） |

### `--skip-build` オプション

事前ビルドチェック（`npm run build`）を省略します。デプロイコマンド自体が内部で再ビルドするため、この事前ビルドはあくまで早期にエラーを検知するための確認です。急ぎの再デプロイなど、ビルドが通ることが分かっている場面でのみ使用してください。

### ワークフロー

```
1. 状態確認    → 未コミット変更・未プッシュコミットを確認
2. コミット    → 未コミット変更があれば /commit スキルでコミット
3. ビルド確認  → npm run build で事前ビルドチェック（--skip-build で省略可）
4. プッシュ    → git push origin main でリモートに反映
5. デプロイ    → npm run deploy:production or deploy:preview を実行
6. 確認       → ブラウザで本番サイトの動作を目視確認
```

未コミットの変更がある場合はデプロイを中止します。先にコミットを済ませてから再実行してください。

---

## 前提要件

- **`package.json` に以下のスクリプトが定義されていること**
  - `deploy:production`（例: `opennextjs-cloudflare build && wrangler deploy --env production`）
  - `deploy:preview`（例: `opennextjs-cloudflare build && wrangler deploy --env preview`）
  - `build`（事前ビルドチェック用。`--skip-build` 指定時は不要）
- **Wrangler でのログインが済んでいること**（`wrangler login`）
- **`wrangler.toml`** に本番・プレビューの環境定義（`[env.production]` / `[env.preview]`）と routes が設定されていること
- Git リポジトリであり、リモート `origin` の `main` ブランチが存在すること

---

## 環境変数

`scripts/deploy.sh` は環境変数で挙動を上書きできます。いずれも未指定でそのまま動作します。

| 環境変数 | 説明 | デフォルト |
|----------|------|-----------|
| `DEPLOY_PROJECT_DIR` | デプロイ対象プロジェクトのルートディレクトリ。スクリプトはここに `cd` してから処理を実行する | 実行時のカレントディレクトリ（`$(pwd)`） |
| `PRODUCTION_URL` | デプロイ完了時に表示する本番サイト URL（任意）。未指定の場合は `wrangler.toml` の routes を参照するようメッセージが出る | 空 |

```bash
# 例: プロジェクトルートと本番 URL を明示して実行
DEPLOY_PROJECT_DIR=~/Projects/my-next-app PRODUCTION_URL=https://example.com \
  bash ~/.agents/skills/deploy-nextjs-cloudflare/scripts/deploy.sh production
```

---

## 注意点

### Next.js メジャーアップグレード後の OpenNext 互換性

Next.js のメジャーアップグレード後は、`@opennextjs/cloudflare` との互換性を事前に確認してください。バンドル生成時に `File server/middleware.js does not exist` のようなエラーが出る場合があります。

- **proxy.ts 非対応問題（2026-02 時点）**: OpenNext は Next.js 16 の `proxy.ts`（旧 `middleware.ts`）を未サポート。回避策として `proxy.ts` → `middleware.ts` にリネームし、`export proxy` → `export middleware` に変更します。
- 追跡: [opennextjs/opennextjs-cloudflare#1082](https://github.com/opennextjs/opennextjs-cloudflare/issues/1082)
- OpenNext が Adapters API を実装し次第、`proxy.ts` に再移行可能です。

### deploy-astro-cloudflare との使い分け

| 対象構成 | 使うスキル |
|----------|-----------|
| Next.js + OpenNext | **deploy-nextjs-cloudflare**（本スキル） |
| Astro + Cloudflare Workers | **deploy-astro-cloudflare** |

トリガー語（「デプロイして」「Cloudflare にデプロイ」など）が両スキルで近いため、誤発動を避ける目的で本スキルは Next.js + OpenNext 構成専用であることを明示しています。対象プロジェクトのフレームワークを確認してから実行してください。

### その他

- デプロイコマンドは内部で再ビルドします。事前の `npm run build` はあくまで早期エラー検知のためのチェックです。
- `wrangler.toml` の `assets.exclude` 警告、`duplicate key "options"` 警告（floating-ui 由来）は既知の問題で、動作には影響しません。
- アセットのアップロードに時間がかかることがあるため、デプロイのタイムアウトは 10 分（600000ms）程度に設定することを推奨します。

---

## 詳細

詳細な仕様・各ステップの挙動・エラー対応表は、スキル本体の `SKILL.md` および `scripts/deploy.sh` を参照してください。

## 外部リファレンス

- [OpenNext for Cloudflare](https://opennext.js.org/cloudflare)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)
