# deploy-astro-cloudflare

**Astro + `@astrojs/cloudflare` 構成専用**の Cloudflare Workers デプロイスキルです。Workers Builds（GitHub 連携による自動デプロイ）と、ローカルからの `wrangler deploy` の 2 モードに対応します。未コミット変更の処理 → ビルド確認 → デプロイ → 完了報告までをワンコマンドで自動実行します。

---

## 対応環境

| 項目 | 内容 |
|------|------|
| フレームワーク | Astro |
| アダプター | `@astrojs/cloudflare` |
| デプロイ先 | Cloudflare Workers |
| デプロイツール | wrangler（`wrangler.jsonc` で設定） |
| CI/CD | Workers Builds（Cloudflare の GitHub 連携） |

> **注意**: Next.js + OpenNext 構成のデプロイには別スキル `deploy-nextjs-cloudflare` を使ってください（末尾の使い分け表を参照）。

---

## インストール

このリポジトリを clone し、スキル本体（`skills/deploy-astro-cloudflare`）を各エージェントのスキルディレクトリへ symlink します。実体は 1 つ、参照を複数張る方式です。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets
ln -s /Users/$USER/Projects/agent-assets/skills/deploy-astro-cloudflare ~/.agents/skills/deploy-astro-cloudflare
ln -s ../../.agents/skills/deploy-astro-cloudflare ~/.claude/skills/deploy-astro-cloudflare
```

> Codex など他のエージェントは `~/.agents/skills/deploy-astro-cloudflare` を直接読みます。Claude Code は `~/.claude/skills/` を経由して同じ実体を参照します。

スキル本体の構成は次の通りです（人間用マニュアルである本ファイルは、スキル本体の外＝`docs/` に置いています）。

```
skills/deploy-astro-cloudflare/
└── SKILL.md   # スキル定義（Claude がトリガー時に読む）
```

---

## クイックスタート

Claude Code で以下を入力するだけ:

```bash
/deploy-astro-cloudflare
```

これだけで、未コミット変更の処理 → ビルド確認 → デプロイ → 完了報告までを自動で実行します。

自然言語でも発動します。「デプロイして」「本番に反映」「Cloudflare にデプロイ」など。

---

## 2 つのデプロイモード

### モード A: Workers Builds（デフォルト・推奨）

GitHub 連携済みなら、`git push` だけで Cloudflare が自動ビルド・デプロイします。

```bash
/deploy-astro-cloudflare
```

**流れ:** 状態確認 → 未コミット変更をコミット → `git push origin main` → Workers Builds が自動ビルド・デプロイ → 完了報告

> GitHub 連携・Workers Builds がまだの場合は Cloudflare ダッシュボードでセットアップしてください。プロジェクト固有のデプロイ引き継ぎ書・セットアップ手順ノートがあればそれを参照します。セットアップ完了まではモード B を使います。

### モード B: ローカルデプロイ（`--local`）

GitHub 連携が未設定の場合や、手元から直接デプロイしたい場合:

```bash
/deploy-astro-cloudflare --local
```

**流れ:** 状態確認 → コミット → `npm run build`（事前チェック）→ `npm run deploy`（`astro build && wrangler deploy`、タイムアウト 10 分）→ `git push origin main` → 完了報告

> 初回は `wrangler login` で Cloudflare にログインしておく必要があります。

---

## オプション

| オプション | 説明 | 使いどころ |
|-----------|------|-----------|
| （なし） | Workers Builds 経由でデプロイ | 通常のデプロイ |
| `--local` | ローカルから直接 `wrangler deploy` | Workers Builds 未設定時、手元から直接デプロイしたいとき |
| `--skip-build` | ビルドチェックを省略 | 急ぎのデプロイ時（ビルド済みの場合）。緊急時のみ |

---

## 前提条件

- `wrangler.jsonc` がプロジェクトルートに存在すること
- `wrangler.jsonc` に **`"keep_vars": true`** が設定されていること
- `public/.assetsignore` に `_worker.js` が記載されていること
- Cloudflare ダッシュボードで環境変数（API キー等）が設定済みであること

### `keep_vars: true` がなぜ必須か

`wrangler deploy` はデフォルトで、Cloudflare ダッシュボードに設定した環境変数を上書き・削除します。`wrangler.jsonc` に `"keep_vars": true` を設定しておくと、ダッシュボードの環境変数が保持されます。**これがないと、デプロイ後に環境変数が消えてサイトが動作しなくなります。**

### `public/.assetsignore` がなぜ必要か

`_worker.js`（サーバーコード）を静的アセットから除外するためのファイルです。これがないと、サーバーコードが公開アセットとして配信され、`_worker.js as an asset` エラーが発生します。

---

## Astro 固有の注意点

Cloudflare Workers 上の Astro では、**サーバーサイドで `import.meta.env` を使えません**。ビルド時に値が固定されてしまうため、リクエスト時のランタイム環境変数（ダッシュボード設定値や Secrets）を読めないからです。

サーバーサイドで環境変数を読むときは `Astro.locals.runtime.env` を使います。

```astro
---
// NG: サーバーサイドでは値が取れない / ビルド時固定
const apiKey = import.meta.env.API_KEY;

// OK: ランタイム環境変数を参照する
const apiKey = Astro.locals.runtime.env.API_KEY;
---
```

ビルドは通るのに本番で 500 エラーになる場合、ほぼこの移行漏れが原因です。

---

## よくあるトラブルと対処

| こんなとき | やること |
|-----------|---------|
| `wrangler: command not found` | `npm install -g wrangler` でインストール |
| 認証エラーが出る | `wrangler login` で再ログイン |
| デプロイ後にサイトが動かない（環境変数消失） | `wrangler.jsonc` に `"keep_vars": true` があるか確認 |
| `_worker.js as an asset` エラー | `public/.assetsignore` に `_worker.js` があるか確認 |
| ビルドは通るが本番で 500 エラー | サーバーコードで `import.meta.env` を使っていないか確認（`Astro.locals.runtime.env` に変更） |
| Workers Builds が失敗する | Cloudflare ダッシュボードでビルドログを確認 |
| `git push` が失敗する | リモートとの差分を確認。`git pull --rebase` を検討 |

---

## deploy-nextjs-cloudflare との使い分け

同じリポジトリに、Cloudflare Workers へデプロイするスキルが 2 つあります。対象フレームワーク・ビルド成果物が異なるため、構成に合わせて選びます。

| | deploy-astro-cloudflare（本スキル） | deploy-nextjs-cloudflare |
|---|---|---|
| 対象 | Astro | Next.js |
| アダプター / ビルダ | `@astrojs/cloudflare` | `@opennextjs/cloudflare`（OpenNext） |
| ビルドコマンド | `astro build && wrangler deploy` | OpenNext ビルド + `wrangler deploy` |
| こういうとき | `astro.config.*` に Astro 設定があり `@astrojs/cloudflare` を使っている | `next.config.*` があり OpenNext で Cloudflare 化している |

「デプロイして」のような曖昧な指示ではトリガー語が衝突しうるので、Astro 構成では本スキルを、Next.js 構成では `deploy-nextjs-cloudflare` を明示的に選んでください。

---

## 詳細

実行フロー（各モードのステップ詳細）・エラー対応表・重要設定の根拠は、スキル本体の `SKILL.md` を参照してください。

## 外部リファレンス

- [Cloudflare Adapter（Astro）](https://docs.astro.build/en/guides/integrations-guide/cloudflare/)
- [Workers Builds](https://developers.cloudflare.com/workers/ci-cd/builds/)
- [wrangler deploy](https://developers.cloudflare.com/workers/wrangler/commands/#deploy)
