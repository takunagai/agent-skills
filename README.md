# agent-skills

AI エージェント（Claude Code / Codex / Gemini CLI / Cursor など）で使える自作スキルの公開モノレポです。

## 設計方針

- **スキル本体は `skills/<name>/`** に置き、AI が実行時に使う資産（`SKILL.md` / `scripts` / `references` / `assets`）だけを入れます。
- **人間向けマニュアルは `docs/<name>.md`** に置きます（スキル本体の外）。スキル本体に README 等の人間向け文書を混ぜない、という方針です。
- **実体は 1 つ（single source of truth）**。各エージェントのスキルディレクトリへ **symlink** して使います。

```
agent-skills/
├── README.md            # このファイル（カタログ）
├── docs/                # 人間向けマニュアル
│   └── cc-fork-delete.md
└── skills/              # スキル本体（AI 実行資産のみ）
    └── cc-fork-delete/
        ├── SKILL.md
        ├── delete-fork.sh
        └── tests/
```

## インストール

スキル本体を、使うエージェントのスキルディレクトリへ symlink します。

```bash
git clone git@github.com:takunagai/agent-skills.git ~/Projects/agent-skills

# Claude Code 用
ln -s ~/Projects/agent-skills/skills/<name> ~/.claude/skills/<name>

# Codex など他エージェント用（任意）
ln -s ~/Projects/agent-skills/skills/<name> ~/.agents/skills/<name>
```

## スキル一覧

| スキル | 概要 | ドキュメント |
|--------|------|-------------|
| cc-fork-delete | Claude Code のフォークセッションを sid 指定で安全削除（dry-run → 確認 → 実行、既定はゴミ箱退避） | [docs/cc-fork-delete.md](docs/cc-fork-delete.md) |
| astro-code-review | Astro 6.0+ プロジェクト（Cloudflare デプロイ対応）のコードを体系的にレビュー。ベストプラクティス違反・パフォーマンス・a11y・型安全性・Astro 6.0 移行問題を検出 | [docs/astro-code-review.md](docs/astro-code-review.md) |
| gen-nanobanana-images | Google Gemini の画像生成モデル Nano Banana シリーズ（Flash / Flash2 / Pro）で、テキストからの画像生成・画像編集・スタイルリファレンス・マルチターン反復修正を行う。要 `GEMINI_API_KEY` | [docs/gen-nanobanana-images.md](docs/gen-nanobanana-images.md) |
| gen-infographic | 日本語の文章・メモ・PDF・スクショなどを 1 枚の読みやすい図解画像へ変換。構造（流れ図・対比・循環・一覧）とスタイル（手描き／ミニマル／水彩／設計図風）を独立に組合せ | [docs/gen-infographic.md](docs/gen-infographic.md) |
| gen-lifestyle-images | 商品のライフスタイル写真を一括生成。ブランド・商品カタログ・シーンをプリセット管理し、セミオート（プラン提示→承認→生成）で量産。要 `GEMINI_API_KEY` | [docs/gen-lifestyle-images.md](docs/gen-lifestyle-images.md) |
| image2-mobile-lp-builder | 確定済み LP 構成と参考デザインから、スマホ LP の画像スライス＋ローカル静的 HTML を生成。CTA／動画／フォームを透明ホットスポットで機能化する画像＋HTML ハイブリッド方式 | [docs/image2-mobile-lp-builder.md](docs/image2-mobile-lp-builder.md) |
| git-workflow | Git ワークフロー支援。Conventional Commits（日本語 subject）でのメッセージ生成・コミット前チェック（機密情報/デバッグコード等）・ブランチ命名規則・マージ戦略ガイド | [docs/git-workflow.md](docs/git-workflow.md) |
| obsidian-vault-create | 新しい Obsidian Vault を標準レイアウトで作成。`YYYY-MM-DD-Project` 命名・数値プレフィックスのフォルダ・README/Home・任意で `.obsidian` 設定コピー。`~/Documents` 既定 | [docs/obsidian-vault-create.md](docs/obsidian-vault-create.md) |
| refund-request | 返金・キャンセル請求メールを、相手企業のポリシー調査の上で交渉力のある文面に。英語・日本語対応、送信前チェックリスト＋4 段階フォローアップ戦略つき | [docs/refund-request.md](docs/refund-request.md) |
