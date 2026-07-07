# print-card-comp — 印刷物カードカンプ生成

依頼内容から、印刷物（名刺・しおり型カード・ポストカード・DL カード・ショップ/スタンプカード・二つ折り・フライヤー等）の
**表裏デザインカンプ（PNG）**と**入稿用デザイン指示書**を一括生成するスキル。

## いつ使うか

- 「カンプ作って」「印刷物を作りたい」「名刺デザイン」「しおり型カード」「ハガキ／ポストカードのデザイン」「ショップカード」「二つ折り」「DL カード」「表裏のデザイン」「2 色刷り」「モノクロ印刷」「縦書きの印刷物」
- 参考画像や依頼メールがあり、そこからカンプまで一気に持っていきたいとき

入稿データ（Illustrator/Figma でのベクター化・トンボ・分版・色校正）の作成は対象外。本スキルが出すのは**カンプ + 指示書**まで。

## 仕組み（役割分担）

| 担当 | 内容 |
|------|------|
| AI（対話） | 依頼分析・掲載要素の整理・サイズと色数の確定・コンセプト 2〜3 案（異なるパターンから）の提案・合成後のセルフレビュー |
| スクリプト | QR 生成（`scripts/gen_qr.py`）・PIL 合成ヘルパ（`scripts/card_compose.py`） |
| 委譲 | 背景画像生成（`gen-nanobanana-images` / `gpt-image-2` スキル） |

**肝**: 画像内の日本語テキスト（コピー・会社情報・URL）は生成モデルに描かせると化ける。
背景だけを生成し、文字・ロゴ・QR は PIL 合成で正確に乗せる（横書き・縦書きとも PIL 側）。

## できること（今回の刷新で強化）

- **色数対応** ─ 4C/4C（フルカラー）・4C/1C・1C/1C（モノクロ）・2C（特色 2 色）を Phase 1 で確定し、背景生成・合成・指示書まで一貫反映。`to_mono()`（1C 化）・`duotone()`（2C 化）を装備。
- **レイアウトパターン 8 種** ─ 写真主役・白抜きタイポ・上下分割・名刺グリッド・タイポ主体・**縦書き和風**・帯バンド・ミニマル罫線。コンセプト提案は必ず異なるパターンから選ぶ。
- **組版の質** ─ 字間（tracking）・複数行・左右揃え・自動縮小（`tx`/`fit_font`）、**縦書き**（`tate()`。長音符・括弧の回転、句読点の位置調整）、丸ゴシック対応。
- **セルフレビュー** ─ 合成後に検版ガイド版（`guides()`）を AI が目視し、文字切れ・かぶり・マージン・コントラストをチェックして最大 2 周で修正。
- **装飾文字パーツ**（例外運用）─ 筆文字・カリグラフィ等「絵としての文字」は生成モデルで作り、`ink_alpha()` で透過 + 単色インク化してロゴ同様に合成（特色単版として扱えるので 1C・2C でも可）。社名・TEL・URL 等の情報テキストは従来どおり PIL 側で、生成には任せない。

## セットアップ

```bash
# 依存（segno + Pillow）
pip install -r ~/.claude/skills/print-card-comp/requirements.txt
# SSL エラー時:
# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org segno Pillow
# PEP 668（externally-managed）時: pip install --user ... か venv（--system-site-packages）で
```

- 背景生成に使う `gen-nanobanana-images`（要 `GEMINI_API_KEY`）か `gpt-image-2`（要 `codex login`）のどちらかを用意。
- フォントは既定で macOS のヒラギノ（明朝 ProN / 角ゴ W3・W6 / 丸ゴ ProN W4）。丸ゴが無い環境は角ゴにフォールバック。別 OS では
  環境変数 `PRINT_CARD_FONT_MINCHO` / `_GOTHIC_W3` / `_GOTHIC_W6` / `_MARU` で上書きする。

## ワークフロー（Phase 1–6）

1. **依頼分析**: 掲載要素を洗い出し、確認マトリクスでサイズ・**色数**・組方向を確定。コンセプトを 2〜3 案（**必ず異なるレイアウトパターン**から、「パターン × 背景スタイル × 配色 × タイポ × 狙い」の組で）提案して選んでもらう。
2. **QR 生成**: `gen_qr.py --url <URL> --out <dir>` で PNG + SVG（誤り訂正 既定 Q）。1C・2C はインク色単色。
3. **背景生成**: 各コンセプトの背景のみを生成（文字なし）。プロンプトは `bg-prompt-library.md` から。2C はグレースケール生成 → `duotone()` で色付け。
4–5. **PIL 合成**: `card_compose.py` のヘルパを import し、`layout-patterns.md`（型）/ `composition-recipe.md`（組み方）/ `design-principles.md`（判断基準）を使って表裏を組む。合成スクリプトは成果物フォルダに `compose.py` として残す。
5.5. **セルフレビュー**: `guides()` の検版版を AI が目視し、チェックリスト判定 → 座標修正 → 再合成（最大 2 周）。
6. **出力**: `~/Downloads/<project>/` に `concept-a/front.png`・`back.png`・`*-trim.png`・`compose.py`・`bg/`、`QR.png/svg`、`spec-sheet.md`、（複数案なら）`proposal-sheet.png`。

## 使用例（Claude への発話）

- 「この依頼メールを見て、しおり型カードのカンプを表裏で作って」
- 「名刺デザインのカンプを 2 案。ロゴと QR は手元のデータを使って」
- 「和菓子屋のショップカード、縦書きで和風に。2 色刷り想定で」
- 「ポストカードの表裏、背景は nanobanana と gpt-image-2 で出し比べて」

## スクリプト単体の使い方

```bash
# QR（印刷向け・PNG + SVG）
python3 ~/.claude/skills/print-card-comp/scripts/gen_qr.py \
  --url "https://example.com/" --out ~/Downloads/proj --name QR --error q

# 合成ヘルパの動作確認（デモ 3 枚: 名刺グリッド・縦書き・2 色刷り + 検版線）
python3 ~/.claude/skills/print-card-comp/scripts/card_compose.py --demo-out /tmp/pcc-demo
```

## 注意・制限

- **色数を守る**: 1C に色を混ぜない・2C はインク 2 色 + 紙色 + 網 % のみ。特色は DIC/PANTONE 番号を指示書に明記。
- **入稿は範囲外**: トンボ・塗り足し・分版・アウトライン化・色校正は別工程。指示書に申し送りを残す。
- **黒文字は K 単色**（リッチブラック不使用）。
- **ロゴは支給ベクター（VI）を使う**。カンプ用の仮ロゴは入稿不可。
- **QR は実機スキャン確認**。クワイエットゾーン確保・15mm 角以上で配置。
- 成果物はスキルディレクトリ内に保存しない（既定の出力先は `~/Downloads/<project>/`）。

## リファレンス

- `references/card-specs.md` — サイズ早見表・解像度・色数の読み方・入稿チェックリスト・用紙 × 色数
- `references/design-principles.md` — 余白・タイポ・配色・情報階層の判断基準
- `references/layout-patterns.md` — レイアウトの型 8 種（ASCII 図・コードスケッチ付き）
- `references/composition-recipe.md` — PIL 合成のヘルパ逆引き・組み方の定石
- `references/bg-prompt-library.md` — 背景生成スタイル 8 種・色数分岐・エンジン別実行例
- `references/spec-sheet-template.md` — デザイン指示書の穴埋めテンプレート

## 由来

アキツ トレーディング案件（Haflinger ブランドのしおり型カード制作, 2026-06-04）で確立した
「依頼分析 → 差別化 → 両エンジン比較生成 → PIL 合成 → 採用確定」のワークフローを汎用スキル化し、
その後（2026-07-07）に色数対応・レイアウトパターン 8 種・縦書きと組版ヘルパ・セルフレビューを加えて拡張したもの。
