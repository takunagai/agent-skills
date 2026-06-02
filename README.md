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
