# obsidian-vault-create

新しい Obsidian Vault を、ディスク上に標準レイアウトで作成するスキルです。`YYYY-MM-DD-Project` 命名・数値プレフィックス付きの標準フォルダ構成・README/Home ノート・Daily テンプレートを生成し、任意でベース Vault から `.obsidian` 設定をコピーします。作成は `scripts/create_vault.py` で決定論的に行います。

---

## インストール

このリポジトリを clone し、スキル本体（`skills/obsidian-vault-create`）を各エージェントのスキルディレクトリへ **symlink** します。

```bash
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets

# ハブ（~/.agents）から実体へ絶対 symlink
ln -s /Users/$USER/Projects/agent-assets/skills/obsidian-vault-create ~/.agents/skills/obsidian-vault-create

# Claude Code 用に ~/.agents への相対 symlink
ln -s ../../.agents/skills/obsidian-vault-create ~/.claude/skills/obsidian-vault-create
```

スキル本体の構成（人間用マニュアルである本ファイルは `docs/` に置いています）:

```
skills/obsidian-vault-create/
├── SKILL.md                       # スキル定義（実行時に読む）
├── scripts/
│   └── create_vault.py            # Vault を標準レイアウトで作成
└── references/
    └── obsidian-basics.md         # Vault 保存・設定・コアプラグインの公式ドキュメント要約
```

> 既定の作成先は `~/Documents`（実行ユーザーのホーム配下に解決）です。`--base-dir` で任意の場所に変更できます。

---

## クイックスタート

自然言語で発動します。「新しい Obsidian Vault を作って」「Vault を初期化して」など。スクリプトを直接叩くこともできます。

```bash
python3 scripts/create_vault.py \
  --project "Project Name" \
  --date 2026-06-02 \
  --base-dir ~/Documents \
  --config-source "/path/to/vanilla-vault-or-.obsidian"
```

| オプション | 説明 |
|-----------|------|
| `--project` | プロジェクト名（必須） |
| `--date` | Vault の日付（`YYYY-MM-DD`。省略時は今日） |
| `--base-dir` | 作成先のベースディレクトリ（既定: `~/Documents`） |
| `--config-source` | 設定コピー元の Vault ルート or `.obsidian` ディレクトリ |
| `--skip-daily` | Daily フォルダと Daily テンプレートを作らない |
| `--dry-run` | 実際に作成せず、作成予定の内容だけ表示 |

---

## 作成される標準レイアウト

数値プレフィックスで並び順を固定したフォルダ構成:

```
00-Inbox / 01-Notes / 02-Projects / 03-Resources /
04-Templates / 05-Assets / 06-Daily / 99-Archive
```

加えて Vault ルートに `README.md`（必須）と `Home.md`（ランディングノート）を作成し、Daily を有効にする場合は `04-Templates/Daily.md` テンプレートを生成します。

## 設定コピーの方針

- 「正統な/デフォルト設定」を求められたら、ユーザーの現在の Obsidian バージョンで作った素の Vault から `.obsidian` をコピーするのが推奨。
- ベースがなければ `.obsidian` はスキップし、初回起動時に Obsidian にデフォルトを生成させる。
- コミュニティプラグインは明示要求がない限り追加せず、コアプラグインに留める。

## 注意点

- Vault を別の Vault の中に入れ子にしない（`--base-dir` の指定に注意）。
- Daily Notes / Templates を使う場合は、Obsidian 側でコアプラグインを有効化し、テンプレートフォルダを `04-Templates`、Daily ノートフォルダを `06-Daily` に設定する。

## 詳細

ワークフロー・設定コピーの詳細・Obsidian の基礎は、スキル本体の `SKILL.md` および `references/obsidian-basics.md` を参照してください。
