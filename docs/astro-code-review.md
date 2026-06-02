# astro-code-review

**Astro 6.0+（ベータ版）専用**のコードレビュースキルです。Cloudflare Workers / Pages をメインのデプロイ先として想定し、Astro プロジェクトのコードを体系的にレビューして、ベストプラクティス違反・パフォーマンス問題・アクセシビリティ欠陥・型安全性の欠如・Astro 6.0 移行問題を検出します。

---

## 対応環境

| 項目 | バージョン |
|------|-----------|
| Astro | 6.0.0-beta+ |
| Node.js | 22.12.0+ |
| デプロイ先 | Cloudflare Workers / Pages（推奨） |
| アダプター | @astrojs/cloudflare v13+ |
| Zod | 4.x |

> **注意**: Astro 5.x 以前のプロジェクトでは移行ガイダンスを提供します。

---

## インストール

このリポジトリを clone し、スキル本体（`skills/astro-code-review`）を各エージェントのスキルディレクトリへ **symlink** します。実体は 1 つ、参照を複数張る方式です。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
# 1) リポジトリを取得
git clone git@github.com:takunagai/agent-skills.git ~/Projects/agent-skills

# 2) ハブ（~/.agents）から実体へ絶対 symlink
ln -s /Users/$USER/Projects/agent-skills/skills/astro-code-review ~/.agents/skills/astro-code-review

# 3) Claude Code 用に ~/.agents への相対 symlink
ln -s ../../.agents/skills/astro-code-review ~/.claude/skills/astro-code-review
```

> Codex など他のエージェントは `~/.agents/skills/astro-code-review` を直接読みます。Claude Code は `~/.claude/skills/` を経由して同じ実体を参照します。

スキル本体の構成は次の通りです（人間用マニュアルである本ファイルは、スキル本体の外＝`docs/` に置いています）。

```
skills/astro-code-review/
├── SKILL.md          # スキル定義（Claude がトリガー時に読む）
├── references/       # 観点別の詳細リファレンス（progressive disclosure）
│   ├── island-architecture.md
│   ├── typescript-patterns.md
│   ├── image-optimization.md
│   ├── data-fetching.md
│   ├── seo-a11y-security.md
│   └── cloudflare-deployment.md
├── assets/
│   └── review-report-template.md   # レビューレポートの出力テンプレート
└── tests/            # レビュー検証用の .astro フィクスチャ
```

---

## クイックスタート

```bash
# カレントディレクトリの全 .astro ファイルをレビュー
/astro-code-review

# 特定ディレクトリをレビュー
/astro-code-review src/pages/

# 特定ファイルをレビュー
/astro-code-review src/components/Header.astro
```

自然言語でも発動します。「Astro のコードをレビューして」「この Astro コンポーネントをチェックして」「Astro プロジェクトの品質を確認して」など。

---

## 主な機能

- **11 カテゴリ**のレビュー観点（Island、TypeScript、画像、SEO、a11y、セキュリティ、**Astro 6.0 Migration**、**Cloudflare** 等）
- **3 段階の重要度分類**（Critical / Warning / Info）
- **具体的な修正例**付きのレポート出力
- **自動修正モード**（`--fix`）で安全な修正を適用
- **Astro 6.0 移行チェック**: 削除 API（`Astro.glob()`、`<ViewTransitions />` 等）の検出
- **Cloudflare 最適化**: `cloudflare:workers` パターン、Node.js 非互換 API の検出

---

## オプション

| オプション | 説明 |
|------------|------|
| `--severity=critical` | Critical のみ検出 |
| `--fix` | 安全な修正を自動適用 |

---

## レビュー観点

| カテゴリ | 検出例 |
|----------|--------|
| Island Architecture | 不適切な `client:*` 選択 |
| TypeScript | Props 型定義の欠如 |
| Image Optimization | `alt` 属性の欠如、`<img>` 直接使用 |
| Data Fetching | `getEntry()` の null チェック欠如 |
| SEO | `<title>`、OGP タグの欠如 |
| Accessibility | `<html lang>` 欠如、見出し階層 |
| Security | `set:html` の未サニタイズ使用 |
| **Astro 6.0 Migration** | `Astro.glob()`、`<ViewTransitions />`、legacy Content Collections |
| **Cloudflare** | `Astro.locals.runtime`、Node.js 専用 API |

---

## 詳細

詳細な仕様・実行フロー・観点別リファレンスは、スキル本体の `SKILL.md` および `references/*.md` を参照してください。

## 外部リファレンス

- [Astro 6 Upgrade Guide](https://v6.docs.astro.build/en/guides/upgrade-to/v6/)
- [Cloudflare Adapter](https://v6.docs.astro.build/en/guides/integrations-guide/cloudflare/)
