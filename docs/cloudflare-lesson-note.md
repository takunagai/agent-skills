# cloudflare-lesson-note

Cloudflare 学習カリキュラムの**セッション内容を技術ブログ品質の Obsidian ノートに整形・保存する**スキルです。会話中で進めた授業（概念説明・図解・コード例・Q&A）を、他人が読んでも理解できるレベルに凝縮し、frontmatter 付きの Markdown として保存先 Vault に書き出します。

特定の学習用 Vault に密結合せず、**保存先は環境変数で設定可能**です。

---

## 概要

学習セッションの会話履歴から、セクション番号・授業本文・Q&A を抽出し、技術ブログとして公開できる品質の Obsidian ノートに整形します。

- ASCII 図やテーブルなど授業中の図解は保持する
- コード例は実行可能な完全版で残す
- Q&A は質問の要旨と回答の核心だけに凝縮する
- 「〜と言えるでしょう」「様々な」「〜することができます」等の AI 臭表現を排除する

---

## インストール

このリポジトリを clone し、スキル本体（`skills/cloudflare-lesson-note`）を各エージェントのスキルディレクトリへ symlink します。実体は 1 つ、参照を複数張る方式です。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets
ln -s /Users/$USER/Projects/agent-assets/skills/cloudflare-lesson-note ~/.agents/skills/cloudflare-lesson-note
ln -s ../../.agents/skills/cloudflare-lesson-note ~/.claude/skills/cloudflare-lesson-note
```

> Codex など他のエージェントは `~/.agents/skills/cloudflare-lesson-note` を直接読みます。Claude Code は `~/.claude/skills/` を経由して同じ実体を参照します。

スキル本体の構成は次の通りです（人間用マニュアルである本ファイルは、スキル本体の外＝`docs/` に置いています）。

```
skills/cloudflare-lesson-note/
└── SKILL.md          # スキル定義（Claude がトリガー時に読む）
```

---

## 設定

保存先 Vault のパスは環境変数 `$LESSON_VAULT_PATH` で指定します。

```bash
# 例: ~/.zshrc などに追記
export LESSON_VAULT_PATH="$HOME/Documents/your-cloudflare-vault"
```

- `$LESSON_VAULT_PATH` が未設定の場合、スキルは保存先をユーザーに確認します
- ノートは `<VAULT>/Phase N/` 形式で保存されます（`<VAULT>` = `$LESSON_VAULT_PATH`、`N` はフェーズ番号）

---

## 使い方

Cloudflare 学習セッションの途中・終了時に、保存を依頼するだけで発動します。

```
ノートを保存して
```

自然言語でも発動します。「レッスンを保存」「今の内容を保存」「ドキュメントにして」「メモを残して」など。

事前に `$LESSON_VAULT_PATH` を設定しておくと、毎回の保存先確認を省けます。

---

## 生成物

| 項目 | 内容 |
|------|------|
| ファイル形式 | frontmatter 付き Markdown |
| ファイル名 | `<セクション番号> <タイトル>.md`（例: `1-1 エッジコンピューティングとは何か.md`） |
| 保存先 | `<VAULT>/Phase N/`（`<VAULT>` = `$LESSON_VAULT_PATH`） |
| 本文構成 | リード文 → 見出しごとの本文 → まとめ → Q&A 要約 |

frontmatter には `tags` / `phase` / `section` / `title` / `date` / `status` を含みます。Q&A は質問の要旨と回答の核心（3〜5 行）に凝縮されます。

---

## 注意点

- **保存先ディレクトリの事前作成**: `<VAULT>/Phase N/` が存在しない場合は、事前に作成しておくか、保存時にユーザーへ確認させてください
- **`$LESSON_VAULT_PATH` の設定**: 未設定だと毎回保存先を尋ねられます。実運用前に環境変数を設定してください
- **AI 臭排除は最終手動確認**: スキルは AI っぽい表現の排除を試みますが、完全ではありません。公開・共有前の目視確認を前提としてください
- **特定 Vault に非依存**: 保存先は設定で差し替え可能です。複数の学習 Vault を使い分ける場合も `$LESSON_VAULT_PATH` を切り替えるだけで対応できます

---

## 詳細

詳細な仕様・ワークフロー・文体ガイドラインは、スキル本体の `SKILL.md` を参照してください。
