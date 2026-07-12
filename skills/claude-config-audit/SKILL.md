---
name: claude-config-audit
description: ユーザーの ~/.claude グローバル設定を機械的に監査する（死 symlink・disabled なのにキャッシュ残存の plugin・MCP 重複登録・orphan commands を検出）。「設定を点検」「config 監査」「.claude 掃除」等のユーザー明示起動で発動。
disable-model-invocation: true
---

# claude-config-audit

`~/.claude` グローバル設定の健全性検査スキル。手作業でやっていた掃除（symlink 切れ確認・未使用プラグイン整理・重複登録検出）を機械化する。

**レポートのみ・自動削除は絶対にしない。** このスキルは検査と提案までを行い、実際の削除・unlink・設定変更はユーザー自身が承認した上で行う。

## 検査項目

`scripts/audit.sh` が次の 4 項目を検査する。

1. **死 symlink** — `~/.claude/skills`、`~/.claude/agents`、`~/.agents/skills` 配下のリンク切れ
2. **disabled なのにキャッシュ残存の plugin** — `settings.json` の `enabledPlugins` で false または未記載なのに、`plugins/installed_plugins.json` にキャッシュが残っているプラグイン
3. **MCP 重複登録（chrome-devtools）** — 直接登録とプラグイン版の二重登録
4. **orphan commands** — `~/.claude/commands/*.md` の一覧（用途判定はユーザーに委ねる、列挙のみ）

### 重要な制約（絶対に外さない）

`--autoConnect` 付きの chrome-devtools 直接登録は**正**である。重複を検出しても直接登録側の削除を提案してはならない。重複解消は**常にプラグイン版（`chrome-devtools-mcp@claude-plugins-official`）の無効化**を提案する。

## ワークフロー

1. `bash scripts/audit.sh` を実行する
2. 出力をユーザー向けに要約する（問題ゼロのセクションは 1 行「問題なし」で済ませ、冗長にしない）
3. 対処はすべて提案止まりとし、実行（symlink 削除・plugin 無効化・commands 整理等）はユーザー承認後に行う

## pre-add モード（統合追加前チェック）

新しい MCP / プラグインを追加する前に `/claude-config-audit` で `scripts/audit.sh pre-add <名前>` を実行し、重複と既存導入路を確認する。`~/.claude.json` の直接登録・導入済みプラグイン・`settings.json` の有効化状態・`known_marketplaces.json` の marketplace 登録を検索語で照合し、ヒットがあれば種別ごとに列挙して統合の推奨を返す。

背景: marketplace 登録済みの製品は公式プラグイン導入を手動 `claude mcp add` より優先する（2026-07-12 の Cloudflare 重複導入の再発防止）。

## 禁止事項

- 自動削除・自動 unlink
- `settings.json` の自動書き換え
- ユーザー承認前の実行系操作全般
