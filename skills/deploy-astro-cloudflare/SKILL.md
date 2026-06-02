---
name: deploy-astro-cloudflare
description: "Astro + Cloudflare Workers デプロイスキル。Workers Builds（GitHub連携）またはローカル wrangler deploy に対応。未コミット変更の処理、ビルド確認、デプロイを自動実行。『デプロイして』『本番に反映』『Cloudflareにデプロイ』などのリクエストで発動。"
---

# Astro + Cloudflare Workers デプロイ Skill

## 概要

Astro アプリケーションを `@astrojs/cloudflare` アダプタ + wrangler 経由で Cloudflare Workers にデプロイする。
Workers Builds（GitHub連携による自動デプロイ）とローカルデプロイの2モードに対応。

> [!note] 適用範囲
> **このスキルは Astro + `@astrojs/cloudflare` 構成専用**。`astro build && wrangler deploy` を前提とする。
> Next.js + OpenNext 構成のデプロイは別スキル `deploy-cloudflare` を使うこと（こちらは `@opennextjs/cloudflare` を前提とし、設定・ビルド成果物が異なる）。

## 技術スタック

- **フレームワーク**: Astro + `@astrojs/cloudflare`
- **デプロイツール**: wrangler（`wrangler.jsonc` で設定）
- **CI/CD**: Workers Builds（Cloudflare の GitHub 連携）

## 使い方

- `/deploy-astro-cloudflare` → Workers Builds 経由でデプロイ（デフォルト）
- `/deploy-astro-cloudflare --local` → ローカルから wrangler deploy を実行
- `/deploy-astro-cloudflare --skip-build` → ビルドチェックを省略（緊急時のみ）

## 本番 URL

プロジェクトに応じて以下のプレースホルダを実際の値に置き換えて扱う。

| 状態 | URL |
|------|-----|
| 現在（workers.dev） | `https://<your-worker>.workers.dev` |
| カスタムドメイン設定後 | `https://<your-domain>` |

---

## モード A: Workers Builds 経由（デフォルト）

GitHub 連携が設定済みの場合、`git push` で自動ビルド・デプロイが走る。

### ワークフロー

```
1. 状態確認    → git status, 未コミット変更・未プッシュコミット確認
2. コミット    → 未コミット変更があれば /commit スキルで処理
3. プッシュ    → git push origin main → Workers Builds が自動でビルド・デプロイ
4. 確認       → デプロイ完了を報告、本番 URL を表示
```

### 各ステップの詳細

#### Step 1: 状態確認

```bash
git status                          # 未コミットの変更を確認
git log --oneline origin/main..HEAD # 未プッシュのコミット数を確認
```

#### Step 2: コミット

未コミットの変更がある場合、`/commit` スキルを呼び出してコミットする。
変更がなければスキップ。

#### Step 3: プッシュ

```bash
git push origin main
```

プッシュ完了後、Workers Builds が自動でビルド・デプロイを実行する。

#### Step 4: 確認

- Workers Builds のデプロイは Cloudflare ダッシュボードで確認可能
- ユーザーに本番 URL でのの動作確認を依頼

### Workers Builds 未設定の場合

Workers Builds がまだ設定されていない場合は、以下を案内:

1. Cloudflare ダッシュボードで GitHub 連携と Workers Builds をセットアップ（プロジェクト固有のデプロイ引き継ぎ書・セットアップ手順ノートがあればそれを参照する）
2. セットアップ完了まではモード B（ローカルデプロイ）を使用

---

## モード B: ローカルデプロイ（`--local`）

Workers Builds 未設定時、または明示的に `--local` を指定した場合。

### ワークフロー

```
1. 状態確認    → git status 確認
2. コミット    → 未コミット変更があれば /commit スキルで処理
3. ビルド確認  → npm run build（事前チェック）
4. デプロイ    → npm run deploy（astro build && wrangler deploy）タイムアウト10分
5. プッシュ    → git push origin main（未プッシュがあれば）
6. 確認       → デプロイログの成功確認 + URL 表示
```

### 各ステップの詳細

#### Step 1: 状態確認

```bash
git status                          # 未コミットの変更を確認
git log --oneline origin/main..HEAD # 未プッシュのコミット数を確認
```

#### Step 2: コミット

未コミットの変更がある場合、`/commit` スキルを呼び出してコミットする。
変更がなければスキップ。

#### Step 3: ビルド確認

```bash
npm run build
```

ビルドが失敗した場合はデプロイを中止し、エラーを報告する。
`--skip-build` オプションが指定されている場合はスキップ。

#### Step 4: デプロイ実行

```bash
npm run deploy
# → astro build && wrangler deploy
```

**タイムアウト: 600000ms（10分）** に設定すること。

#### Step 5: プッシュ

```bash
git push origin main
```

未プッシュコミットがない場合はスキップ。

#### Step 6: 確認

- デプロイログで成功メッセージを確認
- 本番 URL を表示してユーザーに動作確認を依頼

---

## 重要な設定

### `wrangler.jsonc` の `keep_vars: true`

`wrangler deploy` はデフォルトで Cloudflare ダッシュボードに設定した環境変数を上書き・削除する。
`keep_vars: true` を設定することで、ダッシュボードの環境変数が保持される。

**これが設定されていないと、デプロイ後にサイトが動作しなくなる（環境変数消失）。**

### `public/.assetsignore`

`_worker.js` を静的アセットから除外するためのファイル。
これがないとサーバーコードが公開アセットとして配信されるエラーが発生する。

---

## エラー対応

| エラー | 対応 |
|--------|------|
| ビルド失敗 | エラー内容を確認し修正。`/error-diagnostic` を活用 |
| wrangler 認証切れ | `wrangler login` で再認証 |
| 環境変数が消えた | `wrangler.jsonc` の `keep_vars: true` を確認 |
| Workers Builds 失敗 | Cloudflare ダッシュボードでログ確認 |
| アセットアップロード遅延 | タイムアウト延長して再試行 |
| `_worker.js as an asset` エラー | `public/.assetsignore` に `_worker.js` があるか確認 |
| SSR ページが 500 エラー | `import.meta.env` → `Astro.locals.runtime.env` への移行漏れがないか確認 |
| プッシュ失敗 | リモートとの差分を確認。`git pull --rebase` を検討 |

---

## 参照ドキュメント

- プロジェクト固有のデプロイ引き継ぎ書・知見ノート（Workers Builds セットアップ手順、環境変数設定、過去のエラー事例集など）があれば参照する

## 注意事項

- `npm run deploy` は内部で `astro build` を実行するため、Step 3 のビルドは事前チェック目的
- デプロイのタイムアウトは 10 分（600000ms）に設定すること
- Cloudflare Workers では `import.meta.env` はサーバーサイドで使えない。`Astro.locals.runtime.env` を使用すること
