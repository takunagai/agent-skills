---
name: deploy-cloudflare
description: "Next.js + OpenNext 構成専用の Cloudflare Workers 本番/プレビューデプロイスキル。未コミット変更の処理、ビルド確認、プッシュ、OpenNext + Wrangler によるデプロイを自動実行。『Next.js をデプロイして』『本番に反映』『Cloudflareにデプロイ』『プレビューにデプロイ』などのリクエストで発動。Astro 構成のデプロイには deploy-astro-cloudflare を使用する。"
---

# Cloudflare デプロイ Skill（Next.js + OpenNext 構成専用）

> **適用範囲**: このスキルは **Next.js + OpenNext（`@opennextjs/cloudflare`）構成専用**です。
> Astro 構成のデプロイには別スキル **deploy-astro-cloudflare** を使用してください。
> 両者ともトリガー語が近いため、対象プロジェクトのフレームワークを必ず確認してから実行します。

## 概要

Next.js アプリケーションを OpenNext 経由で Cloudflare Workers にデプロイする。
本番環境（production）とプレビュー環境（preview）に対応。

## 使い方

- `/deploy-cloudflare` or `/deploy-cloudflare production` → 本番環境にデプロイ（デフォルト）
- `/deploy-cloudflare preview` → プレビュー環境にデプロイ
- `/deploy-cloudflare --skip-build` → ビルドチェックを省略（緊急時のみ）

## ワークフロー

```
1. 状態確認    → 未コミット変更・未プッシュコミットを確認
2. コミット    → 未コミット変更があれば /commit スキルでコミット
3. ビルド確認  → npm run build で事前ビルドチェック（--skip-build で省略可）
4. プッシュ    → git push origin main でリモートに反映
5. デプロイ    → npm run deploy:production or deploy:preview を実行
6. 確認       → ブラウザで本番サイトの動作を目視確認
```

## 各ステップの詳細

### Step 1: 状態確認

```bash
git status                          # 未コミットの変更を確認
git log --oneline origin/main..HEAD # 未プッシュのコミット数を確認
```

### Step 2: コミット

未コミットの変更がある場合、`/commit` スキルを呼び出してコミットする。
変更がなければスキップ。

### Step 3: ビルド確認

```bash
npm run build
```

ビルドが失敗した場合はデプロイを中止し、エラーを報告する。
`--skip-build` オプションが指定されている場合はスキップ。

### Step 4: プッシュ

```bash
git push origin main
```

未プッシュコミットがない場合はスキップ。

### Step 5: デプロイ実行

```bash
# 本番環境
npm run deploy:production
# → opennextjs-cloudflare build && wrangler deploy --env production

# プレビュー環境
npm run deploy:preview
# → opennextjs-cloudflare build && wrangler deploy --env preview
```

### Step 6: 確認

ブラウザツールが利用可能な場合：
- 本番サイト（デプロイログに表示された本番 URL、または `wrangler.toml` の routes で設定したドメイン）にアクセスして変更を確認
- 主要な変更点をページ上で検索・確認

ブラウザツールが利用できない場合：
- デプロイログの成功メッセージを確認
- ユーザーに手動確認を依頼

## 環境設定

| 環境 | コマンド | URL |
|------|---------|-----|
| production | `npm run deploy:production` | `wrangler.toml` の routes で設定したドメイン（デプロイログに表示） |
| preview | `npm run deploy:preview` | プレビューURL（デプロイログに表示） |

### プロジェクトルート・本番 URL の指定（環境変数）

`scripts/deploy.sh` は以下の環境変数で挙動を上書きできる（いずれも未指定で動作する）。

| 環境変数 | 説明 | デフォルト |
|----------|------|-----------|
| `DEPLOY_PROJECT_DIR` | デプロイ対象プロジェクトのルートディレクトリ | 実行時のカレントディレクトリ |
| `PRODUCTION_URL` | 完了時に表示する本番サイト URL（任意） | 空（`wrangler.toml` の routes を参照） |

## エラー対応

| エラー | 対応 |
|--------|------|
| ビルド失敗 | エラー内容を確認し修正。`/error-diagnostic` を活用 |
| プッシュ失敗 | リモートとの差分を確認。`git pull --rebase` を検討 |
| デプロイ失敗 | wrangler のログを確認。認証切れの場合は `wrangler login` |
| アセットアップロード遅延 | タイムアウトを延長して再試行 |
| OpenNext バンドル生成失敗（`server/middleware.js does not exist`） | 下記「OpenNext 互換性」セクション参照 |

## OpenNext 互換性

Next.js のメジャーアップグレード後は、OpenNext との互換性を事前に確認すること。

### proxy.ts 非対応問題（2026-02 時点）

- **状況**: `@opennextjs/cloudflare` は Next.js 16 の `proxy.ts`（旧 `middleware.ts`）を未サポート
- **エラー**: `File server/middleware.js does not exist`（バンドル生成時）
- **原因**: OpenNext が Adapters API 未実装のため、Node.js ランタイムの proxy.ts を処理できない
- **回避策**: `proxy.ts` → `middleware.ts` にリネームし、`export proxy` → `export middleware` に変更
- **追跡**: [opennextjs/opennextjs-cloudflare#1082](https://github.com/opennextjs/opennextjs-cloudflare/issues/1082)
- **解消条件**: OpenNext が Adapters API を実装し次第、`proxy.ts` に再移行可能。解消後はこのセクションを削除

## 注意事項

- デプロイコマンドは内部で再ビルドするため、Step 3 のビルドは事前チェック目的
- `wrangler.toml` の `assets.exclude` 警告は既知の問題（動作に影響なし）
- `duplicate key "options"` 警告は floating-ui のバンドル警告（動作に影響なし）
- デプロイのタイムアウトは 10 分（600000ms）に設定すること
