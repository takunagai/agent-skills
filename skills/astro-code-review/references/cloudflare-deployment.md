# Cloudflare デプロイリファレンス

Astro 6.0+ を Cloudflare Workers / Pages にデプロイするためのベストプラクティス。

## 概要

Astro 6.0 では Cloudflare Workers サポートが大幅に強化されました。開発サーバー (`astro dev`) が **workerd** (Cloudflare の本番ランタイム) で直接実行されるようになり、開発と本番の差異が解消されています。

## 基本設定

### astro.config.mjs

```javascript
// astro.config.mjs (Astro 6.0+ / Cloudflare)
import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  output: 'server', // または 'hybrid'
  adapter: cloudflare({
    platformProxy: {
      enabled: true, // workerd での開発を有効化（推奨）
    },
  }),
  // CSP 設定（Astro 6.0 新機能）
  csp: {
    directives: {
      'default-src': ["'self'"],
      'script-src': ["'self'"],
      'style-src': ["'self'", "'unsafe-inline'"],
    }
  }
});
```

### wrangler.toml

```toml
# wrangler.toml
name = "my-astro-site"
compatibility_date = "2025-01-01"
compatibility_flags = ["nodejs_compat"]

# KV Namespace
[[kv_namespaces]]
binding = "MY_KV"
id = "your-kv-namespace-id"

# R2 Storage
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "my-bucket"

# D1 Database
[[d1_databases]]
binding = "MY_DB"
database_name = "my-database"
database_id = "your-database-id"

# Durable Objects
[[durable_objects.bindings]]
name = "MY_DURABLE_OBJECT"
class_name = "MyDurableObject"

# Environment Variables
[vars]
PUBLIC_API_URL = "https://api.example.com"

# Secrets (wrangler secret put で設定)
# SECRET_API_KEY は wrangler secret put SECRET_API_KEY で設定
```

---

## Cloudflare Bindings アクセス

### Astro 6.0+ 推奨パターン

```astro
---
// Astro 6.0+: cloudflare:workers モジュールを使用
import { env } from 'cloudflare:workers';

// KV Namespace
const kv = env.MY_KV;
await kv.put('visits', '100');
const visits = await kv.get('visits');

// R2 Storage
const r2 = env.MY_BUCKET;
const object = await r2.get('my-file.txt');
const content = await object?.text();

// D1 Database
const db = env.MY_DB;
const results = await db.prepare('SELECT * FROM users WHERE id = ?')
  .bind(userId)
  .all();

// Durable Objects
const id = env.MY_DURABLE_OBJECT.idFromName('my-instance');
const stub = env.MY_DURABLE_OBJECT.get(id);
const response = await stub.fetch(request);
---

<p>Visits: {visits}</p>
```

### 非推奨パターン（Astro 5.x 以前）

```astro
---
// ❌ 非推奨: Astro.locals.runtime は使用しない
const runtime = Astro.locals.runtime;
const kv = runtime.env.MY_KV;
---
```

---

## レビューチェックリスト

### Critical（即時対応必須）

| 問題 | 検出パターン | 修正方法 |
|------|-------------|---------|
| 旧 Runtime API | `Astro.locals.runtime` | `import { env } from 'cloudflare:workers'` |
| Node.js 専用API | `require('fs')`, `require('path')` | Cloudflare 互換の代替を使用 |
| crypto モジュール | `require('crypto')` | `crypto.subtle` (Web Crypto API) を使用 |

### Warning（改善推奨）

| 問題 | 検出パターン | 修正方法 |
|------|-------------|---------|
| アダプター未設定 | `adapter` 設定なし | `@astrojs/cloudflare` を追加 |
| platformProxy 無効 | `platformProxy.enabled: false` | `true` に変更（開発時に workerd 使用） |
| prerender 最適化不足 | 静的ページで `prerender: false` | `export const prerender = true` を追加 |

### Info（ベストプラクティス）

| 提案 | 説明 |
|------|------|
| KV キャッシュ活用 | 頻繁にアクセスするデータは KV にキャッシュ |
| R2 画像配信 | 画像は R2 + Cloudflare Images で配信 |
| D1 データベース | SQLite 互換のエッジデータベースを活用 |

---

## Node.js 互換性

### 使用可能な Node.js API

Cloudflare Workers は `nodejs_compat` フラグで一部の Node.js API をサポート:

```javascript
// ✅ 使用可能
import { Buffer } from 'node:buffer';
import { EventEmitter } from 'node:events';
import { createHash } from 'node:crypto'; // 一部機能のみ

// ❌ 使用不可
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
```

### 代替パターン

```javascript
// ファイルシステムの代わりに KV/R2 を使用
// ❌ fs.readFile('/data/config.json')
// ✅
const config = await env.MY_KV.get('config', { type: 'json' });

// path の代わりに URL API を使用
// ❌ path.join(base, 'file.txt')
// ✅
const url = new URL('file.txt', base);

// crypto の代わりに Web Crypto API を使用
// ❌ crypto.createHash('sha256').update(data).digest('hex')
// ✅
const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(data));
const hashArray = Array.from(new Uint8Array(hashBuffer));
const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
```

---

## prerender 最適化

### 静的ページ（SSG）

```astro
---
// src/pages/about.astro
// 静的ページは prerender: true を設定
export const prerender = true;
---

<html>
  <body>
    <h1>About Us</h1>
    <p>This page is statically generated at build time.</p>
  </body>
</html>
```

### 動的ページ（SSR）

```astro
---
// src/pages/dashboard.astro
// ユーザー固有のコンテンツは SSR
export const prerender = false;

import { env } from 'cloudflare:workers';

const session = await env.MY_KV.get(`session:${Astro.cookies.get('sid')?.value}`);
if (!session) {
  return Astro.redirect('/login');
}
---

<html>
  <body>
    <h1>Dashboard</h1>
    <!-- ユーザー固有のコンテンツ -->
  </body>
</html>
```

### ハイブリッドモード設定

```javascript
// astro.config.mjs
export default defineConfig({
  output: 'hybrid', // デフォルトは静的、明示的に SSR を指定
  adapter: cloudflare(),
});
```

---

## 環境変数とシークレット

### 公開変数（クライアントアクセス可能）

```javascript
// astro.config.mjs の vars または wrangler.toml の [vars]
// PUBLIC_ プレフィックスでクライアントに公開
PUBLIC_API_URL = "https://api.example.com"
```

```astro
---
// サーバーサイドでアクセス
const apiUrl = import.meta.env.PUBLIC_API_URL;
---

<script>
  // クライアントサイドでもアクセス可能
  const apiUrl = import.meta.env.PUBLIC_API_URL;
</script>
```

### シークレット（サーバーのみ）

```bash
# wrangler でシークレットを設定
wrangler secret put SECRET_API_KEY
```

```astro
---
// サーバーサイドのみでアクセス可能
import { env } from 'cloudflare:workers';

// Bindings 経由でアクセス
const apiKey = env.SECRET_API_KEY;

// または import.meta.env 経由
const apiKey = import.meta.env.SECRET_API_KEY;
---

<!-- ❌ クライアントに露出させない -->
<script>
  // SECRET_* はクライアントでは undefined
</script>
```

---

## エラーハンドリング

### Bindings エラー

```astro
---
import { env } from 'cloudflare:workers';

try {
  const data = await env.MY_KV.get('key');
  if (!data) {
    // キーが存在しない場合
    return Astro.redirect('/not-found');
  }
} catch (error) {
  // KV アクセスエラー
  console.error('KV access failed:', error);
  return new Response('Service temporarily unavailable', { status: 503 });
}
---
```

### D1 エラー

```astro
---
import { env } from 'cloudflare:workers';

try {
  const { results } = await env.MY_DB
    .prepare('SELECT * FROM posts WHERE slug = ?')
    .bind(slug)
    .all();

  if (results.length === 0) {
    return Astro.redirect('/404');
  }
} catch (error) {
  if (error.message.includes('SQLITE_CONSTRAINT')) {
    // 制約違反
    return new Response('Duplicate entry', { status: 409 });
  }
  throw error;
}
---
```

---

## 参考資料

- [Astro Cloudflare Adapter](https://v6.docs.astro.build/en/guides/integrations-guide/cloudflare/)
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler Configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)
- [Cloudflare KV](https://developers.cloudflare.com/kv/)
- [Cloudflare R2](https://developers.cloudflare.com/r2/)
- [Cloudflare D1](https://developers.cloudflare.com/d1/)
