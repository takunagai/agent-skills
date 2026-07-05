# 環境変数・secrets 管理（deploy-astro-cloudflare / Astro 7 + adapter v14）

Cloudflare Workers 上の Astro での環境変数・シークレットの扱い。値の「置き場所」と「読み取り方」を分けて整理する。

## 値の 4 層（置き場所）

| 層 | 置き場所 | コミット | 用途 |
|---|---|---|---|
| 公開値 | `wrangler.jsonc` の `vars` | 可 | 公開してよい設定値（フラグ・公開エンドポイント等） |
| ダッシュボード変数 | Cloudflare ダッシュボードの Variables | 対象外 | 環境ごとに変えたい非機密値 |
| secrets（本番） | `wrangler secret put <KEY>` / `wrangler secret bulk` | 不可 | API キー・トークン等の機密値 |
| ローカル開発値 | `.dev.vars` | **不可（gitignore 必須）** | ローカルの `astro dev` / `wrangler dev` 用 |

- `.dev.vars` は必ず `.gitignore` に入れる。機密値をリポジトリに含めない。
- 機密値は出力本文・コミットメッセージ・PR 本文に載せない。参照（`ファイル名:行番号`）かマスク表示で代替する。

## `keep_vars: true`（重要）

`wrangler deploy` はデフォルトで、Cloudflare ダッシュボードに設定した環境変数を**上書き・削除**する。ダッシュボードで vars を管理する運用では、`wrangler.jsonc` に次を設定する。

```jsonc
{
  "keep_vars": true
}
```

- これがないと、デプロイのたびにダッシュボードの環境変数が消え、本番が動かなくなる。
- すべての vars を `wrangler.jsonc` で管理する運用なら `keep_vars` は不要（設定ファイルが正）。

## 読み取り方（ランタイム）

サーバーコードでランタイム値（ダッシュボード vars / secrets / バインディング）を読むには、次の 2 通りを使う。

### 1. `cloudflare:workers`（直接アクセス）

```ts
import { env } from 'cloudflare:workers';

const apiKey = env.API_KEY;      // 変数・secret
const kv = env.MY_KV;            // バインディング
```

### 2. `astro:env/server`（型安全）

`astro.config` でスキーマを定義した場合に使う。型付きでアクセスできる。

```ts
import { API_KEY } from 'astro:env/server';
```

```js
// astro.config.mjs（スキーマ定義の例）
import { defineConfig, envField } from 'astro/config';

export default defineConfig({
  env: {
    schema: {
      API_KEY: envField.string({ context: 'server', access: 'secret' }),
    },
  },
});
```

### 使い分け

- バインディング（KV / D1 / R2 / Images 等）へアクセスする → `cloudflare:workers` の `env`
- 単純な文字列・数値の変数/secret を型安全に扱う → `astro:env/server`

## `import.meta.env` の罠

`import.meta.env` は**ビルド時にインライン化**される。ランタイムのダッシュボード vars / secrets は読めない。

```astro
---
// NG: ビルド時に値が固定。ランタイム値は取れない
const apiKey = import.meta.env.API_KEY;

// OK: ランタイム値を参照
import { env } from 'cloudflare:workers';
const apiKey = env.API_KEY;
---
```

- ビルドは通るのに本番で 500 エラーになる場合、ほぼこの移行漏れが原因。
- 旧構成の `Astro.locals.runtime.env` は削除済み API。`cloudflare:workers` の `env` へ移行する。

## 環境別ビルド（`CLOUDFLARE_ENV`）

環境はビルド時に確定する。環境ごとに別ビルドしてデプロイする。

```bash
CLOUDFLARE_ENV=staging astro build && wrangler deploy --env staging
```

## Sessions の KV バインディング

`@astrojs/cloudflare` v14 は Sessions 利用時に KV を自動設定する。デフォルトの KV バインディング名は `SESSION`。変更するには adapter の `sessionKVBindingName` オプションを使う。リージョン間は結果整合（伝播に最大 60 秒）。
