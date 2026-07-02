# article-fact-checker

記事草稿の**公開直前ファクトチェック**を行う Claude Code サブエージェントです。草稿から検証可能な主張（数値・年号・企業名／製品名／人名・API 仕様・ライブラリのバージョン・引用文）をすべて抽出し、一次情報に照らして主張ごとに「正 / 疑 / 誤 / 検証不能」の判定を、信頼度と出典 URL 付きで返します。

このリポジトリの他の収録物が「スキル（`skills/<name>/`）」なのに対し、これは**サブエージェント（単一の `.md` ファイル）**です。独立したコンテキストで動くため、長い草稿の検証で親セッションのコンテキストを消費しません。管理ルール（実体はリポジトリに 1 つ、使用側へ symlink）はスキルと共通です。

> [!note] 検証専用です
> 草稿ファイルは直接書き換えません。判定表と修正案を返すだけなので、反映は人間（またはメインセッション）が判断します。

---

## 対応／前提

| 項目 | 内容 |
|------|------|
| 対応エージェント | Claude Code 専用（frontmatter の `tools` / `model` / `color` が Claude Code サブエージェント形式） |
| model | sonnet（検証は手順が固定的なため。判定の精度を上げたい場合は `opus` に変更可） |
| tools | Read, Grep, Glob, Bash, WebSearch, WebFetch, Context7 MCP, Skill（書き込み系ツールなし＝最小権限） |
| 必須依存 | なし（WebSearch / WebFetch は Claude Code 組み込み） |
| 推奨依存 | Context7 MCP（ライブラリ・API 仕様の検証を一次情報で行うため、実質必須級） |
| 任意依存 | `obsidian:defuddle` スキル（単一ページのクリーン抽出）、`firecrawl-scrape` / `firecrawl-search` スキル。未導入環境では WebFetch / WebSearch に自動フォールバック |

---

## インストール

このリポジトリを clone し、エージェント本体（`agents/article-fact-checker.md`）を `~/.claude/agents/` へ symlink します。実体は 1 つ、参照を張る方式です（スキルと同じ運用。ただしサブエージェントは Claude Code 固有のため、`~/.agents` を経由せず直接リンクします）。

```bash
git clone git@github.com:takunagai/agent-skills.git ~/Projects/agent-skills
ln -s ~/Projects/agent-skills/agents/article-fact-checker.md ~/.claude/agents/article-fact-checker.md
```

プロジェクト単位で使う場合は `<repo>/.claude/agents/` へ同様に symlink します。

---

## 使い方

### 自動委譲（通常はこちら）

「ファクトチェック」「裏取り」「数字合ってる？」「引用検証」「公開前確認」などの発話で、メインセッションが自動的にこのエージェントへ委譲します。

```
この Zenn 記事、明日公開するから数字とバージョン情報を全部裏取りして
```

```
記事に書いた「Claude API の料金」って今も合ってる？
```

```
半年前の下書きを再利用したい。情報が古くなってないか確認して
```

### 明示指定

```
@article-fact-checker で draft.md を検証して
```

### 検証の優先順位

1. ライブラリ／SDK／API／CLI／クラウドサービスの仕様 → **Context7 MCP を最優先**（Web 検索での代替は禁止）
2. 技術仕様・公式情報 → 公式サイトをクリーン抽出（defuddle / firecrawl-scrape、なければ WebFetch）
3. 動向・統計 → Web 検索（firecrawl-search / WebSearch）
4. 引用文 → 引用元ページを直接確認

一次情報に辿れない主張は推測で判定せず「検証不能」として返します。

---

## 出力

主張ごとの判定表＋全体サマリを Markdown で返します。

- **判定**: 正 / 疑 / 誤 / 検証不能（曖昧な「たぶん正しい」は出しません）
- **信頼度**: 高 / 中 / 低
- **出典**: URL ＋確認日
- **修正案**: 「誤」判定には新しい出典 URL 付きの修正文
- **全体サマリ**: 公開前に必ず直すべき箇所／公開後の追記でも可の箇所／検証不能で削除推奨の箇所

---

## 関連エージェントとの棲み分け

記事執筆ワークフロー用エージェント 4 体のうちの 1 つです（他 3 体は現在このリポジトリ未収録）。

| エージェント | 担当 | このエージェントとの違い |
|--------------|------|--------------------------|
| article-fact-checker | 公開直前の事実検証 | ─ |
| article-researcher | 執筆前の素材収集・出典付け | 「出典をつける」が目的。fact-checker は「正しいか検証する」が目的 |
| article-editor | 構成・論理・冗長性のレビュー | 構造の指摘。事実の真偽は見ない |
| article-critic | 読者視点の辛口採点・AI 臭判定 | 独自性の評価。事実の真偽は見ない |
