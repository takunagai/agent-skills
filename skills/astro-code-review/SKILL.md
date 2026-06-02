---
name: astro-code-review
version: "2.0.0"
astro: "^6.0.0-beta"
cloudflare: "@astrojs/cloudflare ^13.0.0"
description: "Astro 6.0+ コードレビュースキル。Astroプロジェクト（Cloudflareデプロイ対応）のコードを体系的にレビューし、ベストプラクティス違反・パフォーマンス問題・アクセシビリティ欠陥・型安全性の欠如・Astro 6.0移行問題を検出して改善提案を行う。『Astroのコードをレビューして』『このAstroコンポーネントをチェックして』『Astroプロジェクトの品質を確認して』『Astro review』などのリクエストで発動。"
---

# Astro Code Review Skill

**Astro 6.0+ (ベータ版) 専用** のコードレビュースキル。Cloudflare Workers / Pages をメインデプロイ先として想定。

> **注意**: このスキルは Astro 6.0 以降を対象としています。Astro 5.x 以前のプロジェクトでは移行ガイダンスを提供します。

## 対応環境

| 項目 | バージョン |
|------|-----------|
| Astro | 6.0.0-beta 以上 |
| Node.js | 22.12.0 以上 |
| デプロイ先 | Cloudflare Workers / Pages (推奨) |
| アダプター | @astrojs/cloudflare v13+ |
| Zod | 4.x |

## 目的

- Astro固有のベストプラクティス違反を検出
- パフォーマンス問題の早期発見
- アクセシビリティ・SEOの品質確保
- 型安全性の向上
- **Astro 6.0 移行問題の検出と修正ガイダンス**
- **Cloudflare デプロイの最適化**

## 発動条件（優先順位順）

1. **明示的呼び出し**: `/astro-code-review` コマンド
2. **Astroキーワード + レビュー意図**: 「Astroのコードをチェック」「Astroコンポーネントをレビュー」
3. **`.astro`ファイル指定 + レビュー意図**: 「src/pages/index.astro をレビュー」
4. **プロジェクト判定**: `astro.config.mjs` 存在 + 「コードレビューして」

## 使用方法

```bash
/astro-code-review                              # カレントディレクトリの全.astroファイル
/astro-code-review src/pages/                   # 指定ディレクトリ配下
/astro-code-review src/components/Header.astro  # 特定ファイル
/astro-code-review --severity=critical          # Criticalのみ検出
/astro-code-review --fix                        # 安全な自動修正を適用
```

## レビュー観点（9カテゴリ）

### 1. Islandアーキテクチャ検証

**検出対象:**
- `client:*` ディレクティブの不適切な選択
- 不要なJavaScriptハイドレーション
- `server:defer` の未活用

**ルール:**
| ディレクティブ | 適切な使用場面 | 不適切な例 |
|---------------|---------------|-----------|
| `client:load` | 即時必要なインタラクション（ナビゲーション、認証UI） | 重いチャートコンポーネント |
| `client:visible` | ビューポート外のコンポーネント | Above-the-foldのCTA |
| `client:idle` | 低優先度（ニュースレター、フィードバック） | 重要な入力フォーム |
| `client:only` | SSR不要・クライアント専用 | SEO重要なコンテンツ |

**修正例:**
```astro
// Before: 不適切
<HeavyChart client:load />

// After: 適切
<HeavyChart client:visible />
```

詳細 → `references/island-architecture.md`

---

### 2. TypeScript型安全性

**検出対象:**
- `interface Props` / `type Props` の未定義
- `HTMLAttributes<"element">` 型の未活用
- Content Collections のスキーマ型定義欠如
- `astro/types` からの型インポート欠如

**修正例:**
```astro
// Before: 型定義なし
---
const { title, description } = Astro.props;
---

// After: 型定義あり
---
interface Props {
  title: string;
  description?: string;
}
const { title, description } = Astro.props;
---
```

詳細 → `references/typescript-patterns.md`

---

### 3. 画像・アセット最適化

**検出対象:**
- `<img>` タグの直接使用（`<Image />` 未使用）
- `alt` 属性の欠如
- `loading="lazy"` / `decoding="async"` の欠如
- 最適化されていない画像フォーマット

**修正例:**
```astro
// Before: 最適化なし
<img src="/hero.png">

// After: 最適化あり
---
import { Image } from 'astro:assets';
import heroImage from '../assets/hero.png';
---
<Image src={heroImage} alt="Hero section background" />
```

詳細 → `references/image-optimization.md`

---

### 4. コンポーネント設計

**検出対象:**
- レイアウトコンポーネントの不適切な構造
- `<slot />` の非効率な使用
- 単一責任原則違反
- 名前付きスロットの未活用

**ベストプラクティス:**
```astro
// Layout コンポーネント
---
interface Props {
  title: string;
  description?: string;
}
const { title, description } = Astro.props;
---
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width" />
    <meta name="description" content={description} />
    <title>{title}</title>
    <slot name="head" />
  </head>
  <body>
    <header><slot name="header" /></header>
    <main><slot /></main>
    <footer><slot name="footer" /></footer>
  </body>
</html>
```

---

### 5. データ取得パターン

**検出対象:**
- `getCollection()` / `getEntry()` の不適切な使用
- エラーハンドリングの欠如
- SSR/SSG モードの不整合
- 404リダイレクト処理の欠如

**修正例:**
```astro
// Before: エラーハンドリングなし
---
import { getEntry, render } from 'astro:content';
const post = await getEntry('blog', Astro.params.slug);
const { Content } = await render(post);
---

// After: 適切なエラーハンドリング
---
import { getEntry, render } from 'astro:content';

const { slug } = Astro.params;
if (!slug) {
  return Astro.redirect('/404');
}

const post = await getEntry('blog', slug);
if (!post) {
  return Astro.redirect('/404');
}

const { Content } = await render(post);
---
```

詳細 → `references/data-fetching.md`

---

### 6. SEO・メタデータ

**検出対象:**
- `<title>` の欠如
- `<meta name="description">` の欠如
- Open Graph タグの欠如
- canonical URL の未設定
- 構造化データ（JSON-LD）の欠如

**推奨構成:**
```astro
<head>
  <title>{title} | サイト名</title>
  <meta name="description" content={description} />
  <link rel="canonical" href={canonicalURL} />

  <!-- Open Graph -->
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:type" content="website" />
  <meta property="og:url" content={canonicalURL} />
  <meta property="og:image" content={ogImage} />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />

  <!-- JSON-LD -->
  <script type="application/ld+json" set:html={JSON.stringify(structuredData)} />
</head>
```

---

### 7. アクセシビリティ（a11y）

**検出対象:**
- セマンティックHTML要素の未使用
- `<html lang="...">` の欠如
- ARIA属性の誤用
- キーボードナビゲーション非対応
- フォームラベルの欠如

**チェックリスト:**
- [ ] `<html lang="ja">` が設定されている
- [ ] 見出し階層（h1→h2→h3）が適切
- [ ] `<main>`, `<nav>`, `<article>`, `<aside>` を使用
- [ ] 画像に意味のある `alt` テキスト
- [ ] フォーム要素に `<label>` が関連付け
- [ ] インタラクティブ要素がキーボードアクセス可能

---

### 8. セキュリティ

**検出対象:**
- `set:html` の安全でない使用
- 外部データの未サニタイズ
- 環境変数の不適切な使用
- クライアントへの機密情報漏洩

**危険パターン:**
```astro
// DANGER: 未サニタイズの外部データ
<div set:html={userInput} />

// DANGER: クライアント露出
<script>
  const apiKey = "{import.meta.env.SECRET_API_KEY}";
</script>
```

**安全パターン:**
```astro
// サーバーサイドのみで使用
---
const secretKey = import.meta.env.SECRET_API_KEY;
const data = await fetchWithAuth(secretKey);
---
<div>{data.safeContent}</div>

// クライアント公開用は PUBLIC_ プレフィックス
<script>
  const publicKey = "{import.meta.env.PUBLIC_ANALYTICS_ID}";
</script>
```

詳細 → `references/seo-a11y-security.md`

---

### 9. パフォーマンス

**検出対象:**
- 不要なクライアントサイドJS
- Content Collections の非効率なクエリ
- 大きなバンドルサイズ
- レンダリングブロッキングリソース

**最適化ポイント:**
- 可能な限り静的レンダリング（SSG）を優先
- `client:*` は必要最小限に
- 画像は `astro:assets` で自動最適化
- CSS は `<style>` タグでスコープ化

---

### 10. Astro 6.0 移行チェック

Astro 5.x 以前のコードパターンを検出し、Astro 6.0 への移行を支援。

**検出対象 (Critical):**
- `Astro.glob()` の使用 → `import.meta.glob()` へ移行必須
- `<ViewTransitions />` → `<ClientRouter />` へ移行必須
- `src/content/config.ts` → `src/content.config.ts` へ移行必須

**検出対象 (Warning):**
- `type: 'content'` / `type: 'data'` → loader API へ移行
- `entry.slug` → `entry.id` へ移行
- `entry.render()` → `render(entry)` へ移行
- `import { z } from 'astro:content'` → `import { z } from 'astro/zod'`
- `getEntryBySlug()` → `getEntry()` へ移行

**修正例:**
```astro
// Before: Astro 5.x (非推奨)
---
import { ViewTransitions } from 'astro:transitions';
const posts = await Astro.glob('./posts/*.md');
---
<ViewTransitions />

// After: Astro 6.0+
---
import { ClientRouter } from 'astro:transitions';
const posts = Object.values(import.meta.glob('./posts/*.md', { eager: true }));
---
<ClientRouter />
```

**Zod 4 移行 (Warning):**
```typescript
// Before: Zod 3
z.string().email()
{ message: "エラー" }

// After: Zod 4
z.email()
{ error: "エラー" }
```

詳細 → [Astro 6 Upgrade Guide](https://v6.docs.astro.build/en/guides/upgrade-to/v6/)

---

### 11. Cloudflare デプロイ検証

Cloudflare Workers / Pages へのデプロイにおける問題を検出。

**検出対象 (Critical):**
- `Astro.locals.runtime` の使用 → `cloudflare:workers` モジュールへ移行必須
- `Astro.locals.runtime.env` → `import { env } from 'cloudflare:workers'`
- Node.js 専用API（`fs`, `path`, `crypto` 等）の使用 → Cloudflare Workers 非互換

**検出対象 (Warning):**
- `@astrojs/cloudflare` アダプター未設定
- `wrangler.toml` / `wrangler.json` の不整合
- 静的ページで `prerender: false` が設定されている

**修正例:**
```astro
// Before: Astro 5.x Cloudflare (非推奨)
---
const runtime = Astro.locals.runtime;
const kv = runtime.env.MY_KV;
---

// After: Astro 6.0+ Cloudflare
---
import { env } from 'cloudflare:workers';
const kv = env.MY_KV;
await kv.put('key', 'value');
const value = await kv.get('key');
---
```

**ベストプラクティス (Info):**
- KV / R2 / D1 / Durable Objects の適切な使用
- 静的ページには `export const prerender = true` を設定
- Edge Runtime の制限事項を考慮したコード設計

詳細 → `references/cloudflare-deployment.md`

---

## 重要度分類

| レベル | 説明 | 対応 |
|--------|------|------|
| **Critical** | セキュリティ脆弱性、必須a11y違反 | 即時修正必須 |
| **Warning** | パフォーマンス問題、推奨パターン逸脱 | 優先的に修正 |
| **Info** | ベストプラクティス提案、最適化機会 | 検討推奨 |

### Critical（即時対応必須）
- `set:html` での未サニタイズデータ使用
- `alt` 属性の欠如
- `<html lang>` の欠如
- `getEntry()` / `getCollection()` の null チェック欠如
- クライアントへの機密情報漏洩
- **[Astro 6.0]** `Astro.glob()` の使用
- **[Astro 6.0]** `<ViewTransitions />` の使用
- **[Cloudflare]** `Astro.locals.runtime` の使用
- **[Cloudflare]** Node.js 専用API の使用

### Warning（改善推奨）
- 不適切な `client:*` ディレクティブ選択
- Props 型定義の欠如
- `<Image />` コンポーネント未使用
- `<title>` / `<meta description>` の欠如
- エラーハンドリングの不足
- **[Astro 6.0]** legacy Content Collections API の使用
- **[Astro 6.0]** `import { z } from 'astro:content'`
- **[Cloudflare]** `prerender` 設定の最適化不足

### Info（ベストプラクティス提案）
- セマンティックHTML要素の活用
- Open Graph タグの追加
- 構造化データの追加
- コンポーネント分割の提案
- パフォーマンス最適化の機会
- **[Astro 6.0]** CSP (Content Security Policy) 設定の推奨
- **[Astro 6.0]** Live Collections の活用機会
- **[Cloudflare]** KV / R2 / D1 の活用機会

---

## 実行フロー【必須遵守】

### Step 1: 対象ファイル特定

**ツール使用: Glob**

```
パターン: **/*.astro
パス: 指定されたディレクトリ、または カレントディレクトリ
```

**判断ロジック:**
- 引数がファイルパス（`.astro`で終わる）→ そのファイルのみ対象
- 引数がディレクトリ → そのディレクトリ配下の全`.astro`ファイル
- 引数なし → カレントディレクトリから再帰検索

**ファイル数による分岐:**
- 0件 → エラー処理へ（Step 5参照）
- 1-20件 → 全ファイルを解析
- 21件以上 → ユーザーに確認（「{N}件のファイルが見つかりました。全て解析しますか？ディレクトリを絞り込むことも可能です。」）

---

### Step 2: 静的解析【並列実行可】

**ツール使用: Read（各ファイルに対して）**

各`.astro`ファイルに対し、以下のチェック項目を検査:

#### Critical チェック（必須）
- [ ] `set:html` に未サニタイズのユーザー入力がないか
- [ ] `<img>` タグに `alt` 属性があるか
- [ ] `<html>` タグに `lang` 属性があるか
- [ ] `getEntry()` / `getCollection()` の戻り値に null チェックがあるか
- [ ] `SECRET_*` 環境変数がクライアントスクリプト内で使用されていないか
- [ ] **[Astro 6.0]** `Astro.glob()` が使用されていないか
- [ ] **[Astro 6.0]** `<ViewTransitions />` が使用されていないか
- [ ] **[Cloudflare]** `Astro.locals.runtime` が使用されていないか
- [ ] **[Cloudflare]** `fs`, `path`, `crypto` 等の Node.js 専用API が使用されていないか

#### Warning チェック
- [ ] `client:load` が不適切に使用されていないか（重いコンポーネント、Below-the-fold）
- [ ] `interface Props` または `type Props` が定義されているか
- [ ] `<img>` の代わりに `<Image />` コンポーネントを使用しているか
- [ ] `<title>` と `<meta name="description">` が存在するか（ページファイルのみ）
- [ ] `getEntry()` の結果に対する 404 リダイレクト処理があるか
- [ ] **[Astro 6.0]** `src/content/config.ts` ではなく `src/content.config.ts` を使用しているか
- [ ] **[Astro 6.0]** `type: 'content'` / `type: 'data'` が使用されていないか
- [ ] **[Astro 6.0]** `entry.slug` ではなく `entry.id` を使用しているか
- [ ] **[Astro 6.0]** `entry.render()` ではなく `render(entry)` を使用しているか
- [ ] **[Astro 6.0]** `import { z } from 'astro/zod'` を使用しているか

#### Info チェック
- [ ] セマンティックHTML要素（`<main>`, `<nav>`, `<article>`）を使用しているか
- [ ] Open Graph タグが設定されているか
- [ ] 構造化データ（JSON-LD）が含まれているか
- [ ] 名前付きスロット `<slot name="...">` を活用しているか
- [ ] **[Astro 6.0]** CSP 設定が `astro.config.mjs` で有効化されているか
- [ ] **[Cloudflare]** 静的ページに `export const prerender = true` が設定されているか

---

### Step 3: レポート生成【必須フォーマット】

検出した問題を以下の形式で整理。**このフォーマットを厳守すること。**

```markdown
# Astro Code Review Report

## 📁 対象ファイル
- `src/pages/index.astro`
- `src/components/Header.astro`
（実際の対象ファイルを列挙）

---

## 🚨 Critical Issues (即時対応必須)

### [C-001] alt属性の欠如
- **ファイル**: `src/components/Hero.astro:15`
- **カテゴリ**: Image Optimization / Accessibility
- **問題**: `<img>` タグに alt 属性がありません。スクリーンリーダーユーザーが画像の内容を理解できません。
- **修正前**:
  ```astro
  <img src={heroImage} />
  ```
- **修正後**:
  ```astro
  <img src={heroImage} alt="メインビジュアル: 製品の特徴を示す図解" />
  ```
- **参照**: [Astro Image Guide](https://docs.astro.build/en/guides/images/)

（問題がない場合は「Critical Issues はありません ✅」と明記）

---

## ⚠️ Warnings (改善推奨)

### [W-001] Props型定義の欠如
- **ファイル**: `src/components/Card.astro:1-5`
- **カテゴリ**: TypeScript
- **問題**: Props の型定義がありません。型安全性が低下し、IDE の補完も効きません。
- **推奨**: `interface Props` を frontmatter 内で定義してください。
- **修正例**:
  ```astro
  ---
  interface Props {
    title: string;
    description?: string;
  }
  const { title, description } = Astro.props;
  ---
  ```
- **参照**: [Astro TypeScript Guide](https://docs.astro.build/en/guides/typescript/)

（問題がない場合は「Warnings はありません ✅」と明記）

---

## 💡 Info (ベストプラクティス提案)

### [I-001] Open Graphタグの追加推奨
- **ファイル**: `src/pages/index.astro`
- **カテゴリ**: SEO
- **提案**: SNSでシェアされた際の表示を改善するため、OGPタグの追加を推奨します。
- **メリット**: Twitter/Facebook等でのシェア時にリッチなプレビューが表示されます。
- **実装例**:
  ```astro
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:image" content={ogImage} />
  ```
- **参照**: [Astro SEO Guide](https://docs.astro.build/en/guides/seo/)

（提案がない場合は「追加の提案はありません」と明記）

---

## ✅ Good Practices Found

以下の良い実装パターンが確認されました：

- **TypeScript活用**: `src/components/Button.astro` で Props インターフェースが適切に定義されています
- **画像最適化**: `src/components/Gallery.astro` で `<Image />` コンポーネントが使用されています
- **アクセシビリティ**: `src/layouts/Base.astro` で `<html lang="ja">` が設定されています

（良い実装がない場合もこのセクションは省略せず、「特筆すべき Good Practices は見つかりませんでした」と記載）

---

## 📊 サマリー

### 問題数集計

| カテゴリ | Critical | Warning | Info |
|----------|----------|---------|------|
| Island Architecture | 0 | 1 | 0 |
| TypeScript | 0 | 2 | 0 |
| Image Optimization | 1 | 1 | 0 |
| Component Design | 0 | 0 | 1 |
| Data Fetching | 1 | 0 | 0 |
| SEO | 0 | 1 | 1 |
| Accessibility | 1 | 0 | 0 |
| Security | 0 | 0 | 0 |
| Performance | 0 | 0 | 1 |
| **Astro 6.0 Migration** | 0 | 0 | 0 |
| **Cloudflare** | 0 | 0 | 0 |
| **合計** | **3** | **5** | **3** |

### 総合評価

| 評価項目 | 状態 |
|----------|------|
| セキュリティ | ✅ 良好 |
| アクセシビリティ | 🚨 要対応（Critical 1件） |
| パフォーマンス | ⚠️ 要改善 |
| 型安全性 | ⚠️ 要改善 |
| SEO | ⚠️ 要改善 |
| Astro 6.0 対応 | ✅ 良好 |
| Cloudflare 対応 | ✅ 良好 |

---

## 📚 参考資料

### Astro 6.0
- [Astro 6.0 公式ドキュメント](https://v6.docs.astro.build/)
- [Astro 6 Upgrade Guide](https://v6.docs.astro.build/en/guides/upgrade-to/v6/)
- [Island Architecture](https://v6.docs.astro.build/en/concepts/islands/)
- [TypeScript Guide](https://v6.docs.astro.build/en/guides/typescript/)
- [Image Guide](https://v6.docs.astro.build/en/guides/images/)
- [Content Collections](https://v6.docs.astro.build/en/guides/content-collections/)
- [CSP Configuration](https://v6.docs.astro.build/en/reference/configuration-reference/#securitycsp)

### Cloudflare
- [Cloudflare Adapter](https://v6.docs.astro.build/en/guides/integrations-guide/cloudflare/)
- [Cloudflare Workers](https://developers.cloudflare.com/workers/)
- [Wrangler Configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)

---

*Generated by astro-code-review skill*
```

---

### Step 4: サマリー出力

レポート末尾のサマリーで以下を必ず含める:
- カテゴリ別の問題数集計テーブル
- 総合評価（✅良好 / ⚠️要改善 / 🚨要対応）
- 優先的に対応すべき項目のハイライト

---

### Step 5: エラー処理

| 状況 | 対応 |
|------|------|
| `.astro` ファイルが見つからない | 「指定されたパスに .astro ファイルが見つかりませんでした。パスを確認してください。」と通知 |
| ファイル読み取り権限エラー | Warning として報告し、該当ファイルをスキップして続行 |
| 構文解析不能なファイル | Warning として「{ファイル名} は解析できませんでした（構文エラーの可能性）」と報告し、続行 |
| Astroプロジェクトでない | 「このディレクトリは Astro プロジェクトではないようです。astro.config.mjs が見つかりません。続行しますか？」と確認

---

## 自動修正モード（--fix）

`--fix` オプション指定時、以下の安全な修正を自動適用:

### 自動修正対象（確認なしで適用）
| 問題 | 修正内容 |
|------|----------|
| `alt` 属性の欠如 | `alt="TODO: 画像の説明を追加"` を挿入 |
| `<html lang>` の欠如 | `<html lang="ja">` に変更 |
| `loading` 属性の欠如 | `loading="lazy"` を追加（Above-the-fold以外） |

### 確認後に適用
| 問題 | 修正内容 |
|------|----------|
| Props 型定義の欠如 | スケルトンの `interface Props {}` を生成（ユーザー確認後） |
| `<img>` → `<Image>` 変換 | import文追加と置換（ユーザー確認後） |

### 自動修正しない
- `set:html` のサニタイズ（ロジック変更が必要）
- `client:*` ディレクティブの変更（意図の確認が必要）
- null チェックの追加（ロジック変更が必要）

**注意**: 自動修正後は必ず `git diff` で変更内容を確認するよう促すこと

---

## 参考資料

### 内部リファレンス（詳細ガイド）
- `references/island-architecture.md` - Islandアーキテクチャ詳細・選択フローチャート
- `references/typescript-patterns.md` - TypeScript型パターン・Props定義
- `references/image-optimization.md` - 画像最適化・`<Image />`コンポーネント
- `references/data-fetching.md` - データ取得・エラーハンドリング
- `references/seo-a11y-security.md` - SEO/アクセシビリティ/セキュリティ

### 外部リファレンス
- [Astro公式ドキュメント](https://docs.astro.build/)
- [Astro Island Architecture](https://docs.astro.build/en/concepts/islands/)
- [Astro TypeScript Guide](https://docs.astro.build/en/guides/typescript/)
- [Astro Image Guide](https://docs.astro.build/en/guides/images/)
- [Content Collections](https://docs.astro.build/en/guides/content-collections/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

## CI/CD 統合ガイド

### GitHub Actions での使用例

```yaml
# .github/workflows/astro-review.yml
name: Astro Code Review

on:
  pull_request:
    paths:
      - 'src/**/*.astro'

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Astro Code Review
        # Claude Code CLI または MCP を使用
        run: |
          echo "Changed .astro files:"
          git diff --name-only ${{ github.event.pull_request.base.sha }} | grep '\.astro$' || true
```

### Pre-commit フック

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 変更された .astro ファイルを検出
ASTRO_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.astro$')

if [ -n "$ASTRO_FILES" ]; then
  echo "🔍 Astro files changed, consider running: /astro-code-review"
  echo "$ASTRO_FILES"
fi
```

---

## バージョン履歴

| バージョン | 日付 | 変更内容 |
|------------|------|----------|
| 2.0.0 | 2026-01-18 | **Astro 6.0+ 専用版**: Cloudflare メインデプロイ対応、新カテゴリ（Astro 6.0 Migration, Cloudflare）追加、削除API検出ルール追加、参照ドキュメントを v6.docs.astro.build に更新 |
| 1.1.0 | 2026-01-17 | 実行フロー詳細化、自動修正モード追加、CI/CD統合ガイド追加 |
| 1.0.0 | 2026-01-17 | 初版リリース |
