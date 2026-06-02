# ブランチ戦略詳細ガイド

## ブランチ構成

```
main (本番)
  └── develop (開発)
        ├── feature/xxx (新機能)
        ├── fix/xxx (バグ修正)
        └── refactor/xxx (リファクタリング)
  └── hotfix/xxx (緊急修正)
  └── release/vX.X.X (リリース)
```

## 命名規則

### 基本形式

```
<type>/<issue-number>-<short-description>
```

- `type`: ブランチの種類
- `issue-number`: 関連する Issue 番号（あれば）
- `short-description`: 短い説明（kebab-case）

### Type 一覧

| Type | 用途 | 派生元 | マージ先 |
|------|------|--------|----------|
| feature | 新機能開発 | develop | develop |
| fix | バグ修正 | develop | develop |
| hotfix | 緊急修正 | main | main + develop |
| release | リリース準備 | develop | main + develop |
| refactor | リファクタリング | develop | develop |
| docs | ドキュメント | develop | develop |
| experiment | 実験的機能 | develop | （削除 or feature へ） |

### 命名例

```bash
# 新機能
feature/123-user-authentication
feature/456-payment-integration
feature/add-dark-mode

# バグ修正
fix/789-login-error
fix/session-timeout

# 緊急修正
hotfix/security-vulnerability
hotfix/1011-critical-data-loss

# リリース
release/v2.0.0
release/v2.1.0-beta

# リファクタリング
refactor/optimize-database-queries
refactor/migrate-to-typescript

# ドキュメント
docs/api-reference
docs/contributing-guide
```

## ワークフロー

### Feature 開発

```bash
# 1. develop から分岐
git checkout develop
git pull origin develop
git checkout -b feature/123-new-feature

# 2. 開発とコミット
git add .
git commit -m "feat(module): 機能を実装"

# 3. develop を取り込み（定期的に）
git fetch origin
git rebase origin/develop

# 4. プッシュと PR
git push origin feature/123-new-feature
# PR: feature/123-new-feature → develop
```

### Hotfix

```bash
# 1. main から分岐
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# 2. 修正とコミット
git add .
git commit -m "fix(security): 脆弱性を修正"

# 3. main へマージ
git checkout main
git merge hotfix/critical-fix
git tag -a v1.2.1 -m "Hotfix release"

# 4. develop へも反映
git checkout develop
git merge hotfix/critical-fix

# 5. ブランチ削除
git branch -d hotfix/critical-fix
```

### Release

```bash
# 1. develop から分岐
git checkout develop
git checkout -b release/v2.0.0

# 2. バージョン更新、バグ修正のみ
# package.json などのバージョンを更新

# 3. main へマージ
git checkout main
git merge release/v2.0.0
git tag -a v2.0.0 -m "Release v2.0.0"

# 4. develop へも反映
git checkout develop
git merge release/v2.0.0

# 5. ブランチ削除
git branch -d release/v2.0.0
```

## マージ戦略詳細

### Squash Merge

複数のコミットを1つにまとめる。

**使用する場面：**
- feature → develop
- fix → develop

**利点：**
- develop の履歴がクリーン
- 1機能 = 1コミット

**コマンド：**
```bash
git merge --squash feature/xxx
git commit -m "feat(module): 機能を追加"
```

### Merge Commit

マージコミットを作成。

**使用する場面：**
- hotfix → main
- release → main
- develop → main

**利点：**
- 履歴が保持される
- いつどのブランチがマージされたか明確

**コマンド：**
```bash
git merge --no-ff release/v2.0.0
```

### Rebase

ベースを最新に更新。

**使用する場面：**
- feature ブランチを最新の develop に追従させる

**コマンド：**
```bash
git checkout feature/xxx
git rebase develop
```

## ブランチ保護ルール（推奨）

### main ブランチ

- 直接プッシュ禁止
- PR 必須
- レビュー承認必須（1名以上）
- ステータスチェック必須
- Force push 禁止

### develop ブランチ

- 直接プッシュ禁止（推奨）
- PR 必須
- ステータスチェック必須

## クリーンアップ

マージ済みブランチの定期的な削除：

```bash
# ローカルのマージ済みブランチを削除
git branch --merged | grep -v "main\|develop" | xargs git branch -d

# リモートのマージ済みブランチを削除（GitHub の設定で自動化推奨）
```
