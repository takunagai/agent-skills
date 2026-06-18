# print-card-comp — 印刷物カードカンプ生成

依頼内容から、印刷物（名刺・しおり型カード・ポストカード・DL カード・フライヤー等）の
**表裏デザインカンプ（PNG）**と**入稿用デザイン指示書**を一括生成するスキル。

## いつ使うか

- 「カンプ作って」「印刷物を作りたい」「名刺デザイン」「しおり型カード」「ハガキ／ポストカードのデザイン」「DL カード」「表裏のデザイン」
- 参考画像や依頼メールがあり、そこからカンプまで一気に持っていきたいとき

入稿データ（Illustrator/Figma でのベクター化・トンボ・色校正）の作成は対象外。本スキルが出すのは**カンプ + 指示書**まで。

## 仕組み（役割分担）

| 担当 | 内容 |
|------|------|
| AI（対話） | 依頼分析・掲載要素の整理・サイズ確定・コンセプト 2〜3 案の提案と確認 |
| スクリプト | QR 生成（`scripts/gen_qr.py`）・PIL 合成ヘルパ（`scripts/card_compose.py`） |
| 委譲 | 背景画像生成（`gen-nanobanana-images` / `gpt-image-2` スキル） |

**肝**: 画像内の日本語テキスト（コピー・会社情報・URL）は生成モデルに描かせると化ける。
背景だけを生成し、文字・ロゴ・QR は PIL 合成で正確に乗せる。

## セットアップ

```bash
# 依存（segno + Pillow）
pip install -r ~/.claude/skills/print-card-comp/requirements.txt
# SSL エラー時:
# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org segno Pillow
```

- 背景生成に使う `gen-nanobanana-images`（要 `GEMINI_API_KEY`）か `gpt-image-2`（要 `codex login`）のどちらかを用意。
- フォントは既定で macOS のヒラギノ（明朝 ProN / 角ゴシック W3・W6）。別 OS では
  環境変数 `PRINT_CARD_FONT_MINCHO` / `_GOTHIC_W3` / `_GOTHIC_W6` で上書きするか、
  `scripts/card_compose.py` の `FONTS` を差し替える。

## ワークフロー（Phase 1–6）

1. **依頼分析**: 掲載要素を洗い出し、サイズを確定（既定はしおり型 60×180mm = 827×2480px @350dpi）、コンセプトを 2〜3 案提案して選んでもらう。
2. **QR 生成**: `gen_qr.py --url <URL> --out <dir>` で PNG + SVG（誤り訂正 既定 Q）。
3. **背景生成**: 各コンセプトの背景のみを生成（文字なし）。比較のため両エンジンで出すと採用率が上がる。
4–5. **PIL 合成**: `card_compose.py` のヘルパ（`cover`/`tc`/`pc`/`panel`/`badge`/`load_fonts`）を import し、`references/composition-recipe.md` のレシピで表裏を組む。
6. **出力**: `~/Downloads/<project>/` に `card-final-front/back.png`・QR・デザイン指示書 .md。

## 使用例（Claude への発話）

- 「この依頼メールを見て、しおり型カードのカンプを表裏で作って」
- 「名刺デザインのカンプを 2 案。ロゴと QR は手元のデータを使って」
- 「ポストカードの表裏、背景は nanobanana と gpt-image-2 で出し比べて」

## スクリプト単体の使い方

```bash
# QR（印刷向け・PNG + SVG）
python3 ~/.claude/skills/print-card-comp/scripts/gen_qr.py \
  --url "https://example.com/" --out ~/Downloads/proj --name QR --error q

# 合成ヘルパの動作確認（デモカード書き出し）
python3 ~/.claude/skills/print-card-comp/scripts/card_compose.py --demo-out /tmp/demo.png
```

## 注意・制限

- **入稿は範囲外**: トンボ・塗り足し・アウトライン化・色校正は別工程。指示書に申し送りを残す。
- **ロゴは支給ベクター（VI）を使う**。カンプ用の仮ロゴは入稿不可。
- **QR は実機スキャン確認**。クワイエットゾーン確保・15mm 角以上で配置。
- 成果物はスキルディレクトリ内に保存しない（既定の出力先は `~/Downloads/<project>/`）。

## リファレンス

- `references/card-specs.md` — サイズ早見表・解像度・入稿チェックリスト・用紙候補
- `references/composition-recipe.md` — 表裏の PIL 合成レシピ（白下地・半透明パネル・赤ライン・CTA バッジ・QR 配置）

## 由来

アキツ トレーディング案件（Haflinger ブランドのしおり型カード制作, 2026-06-04）で確立した
「依頼分析 → 差別化 → 両エンジン比較生成 → PIL 合成 → 採用確定」のワークフローを汎用スキル化したもの。
