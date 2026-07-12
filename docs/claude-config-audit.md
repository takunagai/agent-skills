# claude-config-audit

`~/.claude` グローバル設定の健全性検査スキルです。手作業でやっていた掃除（symlink 切れ確認・未使用プラグイン整理・重複登録検出）を機械化します。

**レポートのみ・自動削除は絶対にしません。** 検査と提案までを行い、実際の削除・unlink・設定変更はユーザー自身が承認した上で行います。ユーザーの明示起動（「設定を点検」「config 監査」「.claude 掃除」等）で発動します。

---

## インストール

このリポジトリを clone し、スキル本体（`skills/claude-config-audit`）を各エージェントのスキルディレクトリへ **symlink** します。

```bash
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets

# ハブ（~/.agents）から実体へ絶対 symlink
ln -s /Users/$USER/Projects/agent-assets/skills/claude-config-audit ~/.agents/skills/claude-config-audit

# Claude Code 用に ~/.agents への相対 symlink
ln -s ../../.agents/skills/claude-config-audit ~/.claude/skills/claude-config-audit
```

スキル本体の構成（人間用マニュアルである本ファイルは `docs/` に置いています）:

```
skills/claude-config-audit/
├── SKILL.md          # スキル定義（実行時に読む）
└── scripts/
    └── audit.sh       # 検査本体（監査 / pre-add の 2 モード）
```

---

## 検査項目

`scripts/audit.sh` が次の 4 項目を検査します。

1. **死 symlink** — `~/.claude/skills`、`~/.claude/agents`、`~/.agents/skills` 配下のリンク切れ
2. **disabled なのにキャッシュ残存の plugin** — `settings.json` の `enabledPlugins` で false または未記載なのに、`plugins/installed_plugins.json` にキャッシュが残っているプラグイン
3. **MCP 重複登録（chrome-devtools）** — 直接登録とプラグイン版の二重登録
4. **orphan commands** — `~/.claude/commands/*.md` の一覧（用途判定はユーザーに委ね、列挙のみ）

> **重要な制約**: `--autoConnect` 付きの chrome-devtools 直接登録は正です。重複を検出しても直接登録側の削除は提案せず、重複解消は常にプラグイン版（`chrome-devtools-mcp@claude-plugins-official`）の無効化を提案します。

---

## クイックスタート

```bash
bash scripts/audit.sh
```

自然言語でも発動します。「設定を点検して」「.claude を掃除したい」など。

## pre-add モード（統合追加前チェック）

新しい MCP / プラグインを追加する前に、重複と既存導入路を確認します。

```bash
bash scripts/audit.sh pre-add <名前>
```

`~/.claude.json` の直接登録・導入済みプラグイン・`settings.json` の有効化状態・`known_marketplaces.json` の marketplace 登録を検索語で照合し、ヒットがあれば種別ごとに列挙して統合の推奨を返します。marketplace 登録済みの製品は公式プラグイン導入を手動 `claude mcp add` より優先します。

---

## 禁止事項

- 自動削除・自動 unlink
- `settings.json` の自動書き換え
- ユーザー承認前の実行系操作全般

## 詳細

検査ロジックの詳細は、スキル本体の `SKILL.md` および `scripts/audit.sh` を参照してください。
