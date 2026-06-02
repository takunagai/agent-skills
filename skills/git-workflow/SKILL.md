---
name: git-workflow
description: "Git ワークフローを管理・実行するスキル。コミット作成、ブランチ操作、PR 作成時に使用する。Conventional Commits 形式（日本語）でのコミットメッセージ生成、コミット前チェック、ブランチ命名規則の適用をサポート。『コミットして』『ブランチ作って』『PR 用意して』『Git の操作』などのリクエストで発動。"
---

# Git ワークフロー Skill

## 厳守事項

コミットでは既存の Git ユーザー設定のみを使用する。

**禁止事項：**
- 共著者または Claude の署名を追加
- "Generated with Claude Code" などのメッセージ
- Git 設定やユーザー資格情報の変更
- AI/アシスタントの属性をコミットに追加
- 絵文字の使用（コミット、PR、Git 関連全般）

## ワークフロー

```
1. ブランチ作成 → references/branch-strategy.md 参照
2. 変更を加える
3. コミット前チェック → scripts/commit_check.sh 実行
4. コミット作成 → 下記の形式に従う
5. PR 作成 → assets/pr-template.md を使用
```

## コミットメッセージ生成

Conventional Commits 形式で日本語の subject を書く。

**形式：** `<type>(<scope>): <日本語の説明>`

**生成例：**

| 変更内容 | コミットメッセージ |
|----------|-------------------|
| ログイン機能を新規実装 | `feat(auth): ログイン機能を実装` |
| API のバグを修正 | `fix(api): レート制限のカウント処理を修正` |
| README を更新 | `docs(readme): インストール手順を更新` |
| 破壊的変更を含む | `feat(api)!: レスポンス形式を変更` |

**Type:** feat / fix / docs / style / refactor / perf / test / build / ci / chore

詳細・body・footer の書き方 → `references/conventional-commits.md`

## コミット粒度

1コミット = 1つの論理的変更。以下は別コミットにする：
- 機能追加 / バグ修正 / リファクタリング
- 設定変更 / ドキュメント更新 / 依存関係更新

## ブランチ命名

**形式：** `<type>/<issue-number>-<short-description>`

```
feature/123-user-authentication
fix/456-login-error
hotfix/789-security-patch
```

詳細 → `references/branch-strategy.md`

## マージ戦略

| マージ方向 | 戦略 |
|-----------|------|
| feature/fix → develop | Squash merge |
| hotfix/release → main | Merge commit |

## リソース

| ファイル | 用途 |
|---------|------|
| `scripts/commit_check.sh` | コミット前チェック（ビルド/テスト/Lint/機密情報/デバッグコード） |
| `scripts/validate_commit_msg.sh` | コミットメッセージ検証 |
| `references/conventional-commits.md` | Conventional Commits 詳細ガイド |
| `references/branch-strategy.md` | ブランチ戦略詳細ガイド |
| `assets/pr-template.md` | PR テンプレート |
| `assets/commit-template.txt` | コミットメッセージテンプレート |
