# git-workflow

Git ワークフロー（ブランチ作成・コミット・PR 作成）を管理・実行するスキルです。Conventional Commits 形式（**日本語 subject**）でのコミットメッセージ生成、コミット前チェック（ビルド/テスト/Lint/機密情報/デバッグコード）、ブランチ命名規則の適用をサポートします。

> **方針**: コミットには既存の Git ユーザー設定のみを使い、AI 署名・共著者・"Generated with" メッセージ・絵文字は一切追加しません。配布物としてクリーンに使えるよう設計しています。

---

## インストール

このリポジトリを clone し、スキル本体（`skills/git-workflow`）を各エージェントのスキルディレクトリへ **symlink** します。実体は 1 つ、参照を複数張る方式です。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
# 1) リポジトリを取得
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets

# 2) ハブ（~/.agents）から実体へ絶対 symlink
ln -s /Users/$USER/Projects/agent-assets/skills/git-workflow ~/.agents/skills/git-workflow

# 3) Claude Code 用に ~/.agents への相対 symlink
ln -s ../../.agents/skills/git-workflow ~/.claude/skills/git-workflow
```

スキル本体の構成は次の通りです（人間用マニュアルである本ファイルは、スキル本体の外＝`docs/` に置いています）。

```
skills/git-workflow/
├── SKILL.md                       # スキル定義（Claude がトリガー時に読む）
├── references/
│   ├── conventional-commits.md    # Conventional Commits 詳細ガイド
│   └── branch-strategy.md         # ブランチ戦略詳細ガイド
├── assets/
│   ├── commit-template.txt        # コミットメッセージテンプレート
│   └── pr-template.md             # PR テンプレート
└── scripts/
    ├── commit_check.sh            # コミット前チェック
    └── validate_commit_msg.sh     # コミットメッセージ検証
```

---

## クイックスタート

自然言語で発動します。「コミットして」「ブランチ作って」「PR 用意して」「Git の操作」など。

```
このバグ修正をコミットして
新機能用のブランチを作成して
この変更を PR にまとめて
```

---

## 主な機能

- **コミットメッセージ生成**: Conventional Commits 形式（`<type>(<scope>): <日本語の説明>`）で日本語 subject を生成
- **コミット前チェック**（`scripts/commit_check.sh`）: ビルド / テスト / Lint / 機密情報混入 / デバッグコード残存を検査
- **コミットメッセージ検証**（`scripts/validate_commit_msg.sh`）: 形式の妥当性をチェック
- **ブランチ命名規則**: `<type>/<issue-number>-<short-description>`（例: `feature/123-user-authentication`）
- **マージ戦略ガイド**: feature/fix → develop は Squash merge、hotfix/release → main は Merge commit

### Type 一覧

`feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `build` / `ci` / `chore`

### コミットメッセージ例

| 変更内容 | コミットメッセージ |
|----------|-------------------|
| ログイン機能を新規実装 | `feat(auth): ログイン機能を実装` |
| API のバグを修正 | `fix(api): レート制限のカウント処理を修正` |
| README を更新 | `docs(readme): インストール手順を更新` |
| 破壊的変更を含む | `feat(api)!: レスポンス形式を変更` |

---

## 注意点

- **日本語 subject が前提**です。英語圏のプロジェクトで使う場合は SKILL.md / references の例を読み替えてください（仕組み自体は言語非依存）。
- **AI 署名・絵文字は付けません**。Co-Authored-By や "Generated with Claude Code" を付ける運用とは方針が逆です。必要な環境では SKILL.md の「厳守事項」を調整してください。
- コミット粒度は「1 コミット = 1 つの論理的変更」を原則とします。

## 詳細

実行フロー・Conventional Commits の body/footer・ブランチ戦略の詳細は、スキル本体の `SKILL.md` および `references/*.md` を参照してください。
