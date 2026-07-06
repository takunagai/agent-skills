# cloudflare-lesson-tutor

Cloudflare 学習カリキュラムの**授業を運営する**スキルです。進捗ダッシュボード（Dashboard.md）で現在地を把握し、カリキュラム設計正本（CURRICULUM.md）の到達目標に沿って、最新の一次情報で裏を取りながら 1 セクションを対話形式で教えます。

ノートの保存・進捗の記録は [cloudflare-lesson-note](cloudflare-lesson-note.md) が担います。**本スキルは学習 Vault へは読み取りのみ**で、進捗の書き込みは一切行いません（単一ライター原則）。

---

## 概要

「Cloudflare のレッスンを続きから」と言うだけで、次の流れを追加指示なしに進めます。

1. **現在地の特定**: `Dashboard.md` で現在地・次セクションを読み、`CURRICULUM.md` で到達目標と参照先を確認する
2. **鮮度検証（授業前の裏取り）**: 扱うプロダクトの現状を一次情報で確認する。pre-training の知識で断定せず retrieval を優先。価格・上限値・API 署名・GA/ベータ状態は必ず一次情報で確認し、検証日を控える
3. **授業の実施**: 導入 → 概念（既知から入る）→ 図解（ASCII 図）→ コード実演（完全版）→ 演習・確認 → まとめ
4. **クロージング**: 「ノートを保存して」で cloudflare-lesson-note に引き継ぐ

教授法は共有リソース `_lesson-methods/explain-hard-concepts.md`（保存スキルと共通）のメソッドに従います。

### フレームワーク情報はフレームワーク公式を正とする

鮮度検証には一般則があります。Cloudflare docs のフレームワークガイドは滞留しうるため、フレームワークのバージョン・API は**フレームワーク公式**を正とします（例: Astro は `docs.astro.build`、Next.js/OpenNext は `opennext.js.org`、Hono は `hono.dev`、Drizzle は `orm.drizzle.team`）。両者が食い違ったらフレームワーク公式を信じます。

---

## インストール

このリポジトリを clone し、スキル本体（`skills/cloudflare-lesson-tutor`）を各エージェントのスキルディレクトリへ symlink します。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
git clone git@github.com:takunagai/agent-assets.git ~/Projects/agent-assets
ln -s /Users/$USER/Projects/agent-assets/skills/cloudflare-lesson-tutor ~/.agents/skills/cloudflare-lesson-tutor
ln -s ../../.agents/skills/cloudflare-lesson-tutor ~/.claude/skills/cloudflare-lesson-tutor
```

> Codex など他のエージェントは `~/.agents/skills/cloudflare-lesson-tutor` を直接読みます。Claude Code は `~/.claude/skills/` を経由して同じ実体を参照します。

スキル本体の構成は次の通りです。

```
skills/cloudflare-lesson-tutor/
├── SKILL.md                          # スキル定義（Claude がトリガー時に読む）
└── references/
    └── explain-hard-concepts.md      # → ../../_lesson-methods/explain-hard-concepts.md（相対 symlink）
```

教授法ガイド `explain-hard-concepts.md` は保存スキル（cloudflare-lesson-note）と共有するため、共有リソース `skills/_lesson-methods/` に実体を置き、両スキルの `references/` から相対 symlink で参照します。スキル本体の symlink を張れば依存はリポ内相対リンクで解決するため、`_lesson-methods` 自体を個別に symlink 登録する必要はありません。

---

## 設定

学習 Vault のパスは環境変数 `$LESSON_VAULT_PATH` で指定します（保存スキルと共通）。

```bash
# 例: ~/.zshrc などに追記
export LESSON_VAULT_PATH="$HOME/Documents/your-cloudflare-vault"
```

- 未設定の場合、スキルは Vault パスをユーザーに確認します
- Vault 直下に `CURRICULUM.md`（設計正本）と `Dashboard.md`（進捗正本）があることを前提とします

---

## クイックスタート（標準セッションの流れ）

授業運営スキル（本スキル）と保存スキル（cloudflare-lesson-note）は 2 つで 1 つの学習ワークフローです。1 セッションの基本形は次の通りです。

1. **起動**: `claude --model opus` で起動する（モデルの根拠は後述）。対話のテンポを上げたいなら起動後に `/fast` を実行する
2. **現在地確認（任意）**: 「カリキュラムの進捗を見せて」で、いま何 Phase の何セクションまで進んでいるかを確認する
3. **授業開始**: 「Cloudflare のレッスンを続きから ultrathink」と入力する。Dashboard の次の未完了セクションから、鮮度検証つきで 1 セクションを対話形式で教わる
4. **対話で学ぶ**: 疑問はその場で質問する（「もう少し噛み砕いて」「手を動かしたいので演習を出して」など自由に）。この往復は思考キーワード無指定でよい
5. **保存**: セクションが一区切りしたら「ノートを保存して」と入力する。会話が技術ブログ品質のノートになり、`Dashboard.md` の進捗が更新される（同名ノートがある場合は差分の要約が出るので承認/却下を返す）
6. **継続 or 終了**: 続けるなら 3 に戻る。終えるならそのまま終了する

初めて導入する場合は、先に上の「インストール」「設定」と下の「導入チェックリスト」を済ませ、Vault 直下に `CURRICULUM.md`（学ぶ内容の設計）と `Dashboard.md`（進捗）があることを確認してください。

---

## 推奨モデルと推論レベル

### モデル: 両スキルとも Opus を推奨

授業側は「何を一次情報で裏取りするか」「情報源が食い違ったとき（例: Cloudflare docs は旧バージョン vs フレームワーク公式は最新）にどちらを正とするか」という判断と、教授法の質が価値の中心です。保存側もノート本文の凝縮・AI 臭排除という文章生成の質が中心です。いずれも設計・判断・生成の質が効くため Opus を推奨します。Sonnet でも動作しますが、古い事実を自信ありげに教えてしまう/ノートが凡庸になるリスクが上がります。Haiku は教授・執筆の質が要るため非推奨です。

授業は対話が主体なので、体感速度を上げたいときは `/fast`（Opus のまま出力が速くなり、品質は落ちない）を併用できます。

### 推論レベル（思考キーワード）: 要所で上げる

Claude Code では、メッセージに思考キーワードを含めて推論の深さを指定します（弱 `think` < 中 `think hard`／megathink < 強 `ultrathink`）。全ターンで `ultrathink` を固定すると応答が遅くなり `/fast` の快適さも相殺するため、要所で上げる運用を推奨します。

| 場面 | 推奨レベル | 理由 |
|---|---|---|
| 授業のセクション冒頭（現在地把握 → 鮮度検証 → 授業設計） | `ultrathink` | そのセクションの土台を決める最重要ターン。古い事実を混ぜない規律が最も効く |
| 授業中の対話・質問・演習 | 無指定〜`think` | テンポ優先。往復のたびに重い思考は要らない |
| 込み入った概念、料金・上限値の裏取りで情報が食い違うとき | `ultrathink` | 難所だけ都度上げる |
| ノート保存（「ノートを保存して」） | `think hard`（megathink） | 本文の凝縮と Dashboard の再計算が主。冒頭 1 回効かせれば十分。上書き差分の判断が絡むときは `ultrathink` |

---

## プロンプト集（チートシート）

そのまま入力できる代表的なフレーズです。カリキュラムの内容（Phase 構成・セクション名）はスキルに固定されておらず、常に Vault の `CURRICULUM.md` から読まれるため、下記のフレーズはカリキュラムを改訂しても変わりません。

| やりたいこと | 入力例 | 発動スキル |
|---|---|---|
| 進捗を確認する | `カリキュラムの進捗を見せて` | tutor |
| 続きから授業を始める | `Cloudflare のレッスンを続きから ultrathink` | tutor |
| 今日の分を始める（別表現） | `今日のレッスン` ／ `次のセクション` ／ `Cloudflare 学習を再開` | tutor |
| 特定セクションを指定する | `2-3 ミドルウェアパターンを教えて` | tutor |
| 授業中に深掘りする | `もう少し噛み砕いて` ／ `手を動かしたいので演習を出して` | tutor（対話） |
| 成果をノート化・進捗更新する | `ノートを保存して` | note |
| 保存の別表現 | `レッスンを保存` ／ `今の内容を保存` ／ `ドキュメントにして` | note |

保存フレーズの詳細と生成物は [cloudflare-lesson-note](cloudflare-lesson-note.md) を参照してください。

---

## 導入チェックリスト

私以外の人が新規に導入する場合の最短手順です。

1. リポジトリを clone し、2 スキル（cloudflare-lesson-tutor / cloudflare-lesson-note）を symlink 登録する（上の「インストール」）
2. `$LESSON_VAULT_PATH` を設定し、新しいシェルで `echo $LESSON_VAULT_PATH` が通ることを確認する（上の「設定」）
3. Vault 直下に次の 2 ファイルを用意する
   - `CURRICULUM.md` ─ 何を・どの順で・何を参照して学ぶかの**設計正本**（進捗は書かない）
   - `Dashboard.md` ─ 進捗の正本（現在地・完了状況・進捗バー）
   - これらはスキルが自動生成するものではなく、学習者が用意するコンテンツです。ゼロから始めるなら、まずカリキュラムを設計して `CURRICULUM.md` に落とし、対応する `Dashboard.md`（全セクション未完了 = 0/N）を作ります
4. 動作確認: `claude --model opus` で起動し「カリキュラムの進捗を見せて」と入力 → 現在地が返れば導入完了

---

## 生成物

このスキル自体はファイルを生成・保存しません（授業は対話で進みます）。授業の成果をノート化・進捗記録するのは cloudflare-lesson-note です。セクション終了時に「ノートを保存して」と言うと、その会話内容が技術ブログ品質のノートとして保存され、Dashboard.md の進捗が更新されます。

---

## 注意点

- **読み取り専用**: 本スキルは学習 Vault へ書き込みません。進捗更新・ノート保存は cloudflare-lesson-note の責務です
- **retrieval 優先**: 価格・上限値・API 署名・GA/ベータ状態は pre-training の知識で断定せず、必ず一次情報で確認します。確認日はノート保存時の `verified` に反映されます
- **フレームワーク公式優先**: フレームワークのバージョン・API はフレームワーク公式を正とします（Cloudflare docs のフレームワークガイドは滞留しうる）
- **ベータ／プレビュー製品**: CURRICULUM.md の「状態」欄がベータ／プレビューの製品は、API が数ヶ月で変わりうる前提で実行時に現行版を再確認し、「変化前提の学び方」も伝えます
- **カリキュラム非ハードコード**: Phase 構成・セクション名は SKILL.md に固定せず、常に CURRICULUM.md から読みます。カリキュラム改訂時にスキルの変更は不要です

---

## 詳細

詳細な仕様・ワークフローは、スキル本体の `SKILL.md` を参照してください。保存側は [cloudflare-lesson-note](cloudflare-lesson-note.md) を参照してください。
