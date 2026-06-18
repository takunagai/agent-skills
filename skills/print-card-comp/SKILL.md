---
name: print-card-comp
description: "Generate print-ready design comps for cards and small print materials (business cards, bookmarks/shiori, postcards, DL cards, flyers) from a brief to finished front/back PNGs. Covers request analysis, concept proposals, QR code generation (segno), PIL-based composition (copy/logo/info overlay with no text corruption), and a print spec sheet with bleed/safe-margin. 印刷物のデザインカンプ生成。「カンプ作って」「印刷物を作りたい」「名刺デザイン」「しおり型カード」「ハガキデザイン」「ポストカード」「カード制作」「DLカード」「表裏のデザイン」などのリクエストで使う。背景画像生成は gen-nanobanana-images / gpt-image-2 スキルを内部利用する。"
---

# Print Card Comp Generation（印刷物カードカンプ生成）

## Overview

依頼内容（依頼文・参考画像）から、印刷物の**表裏デザインカンプ（PNG）**と**入稿用デザイン指示書**を一括生成するスキル。名刺・しおり型カード・ポストカード・DL カード・フライヤー等に対応する。

役割分担:

- **AI（このスキル）が対話的に行う**: 依頼分析・掲載要素の整理・サイズ確定・コンセプト 2〜3 案の提案と確認・プロンプト組み立て・採用案の確定
- **スクリプトが決定的に行う**: QR コード生成（`scripts/gen_qr.py`）・PIL 合成のヘルパ（`scripts/card_compose.py`）
- **他スキルに委譲する**: 背景画像生成（`gen-nanobanana-images` / `gpt-image-2`）

> [!note] テキストは生成画像に焼かない
> 画像内の日本語コピー・会社情報・URL は生成モデルに描かせると化ける。**背景だけを生成し、文字・ロゴ・QR は PIL 合成フェーズで乗せる**のが本スキルの肝。

### Prerequisites

- **Python deps**: `pip install -r requirements.txt`（`segno` + `Pillow`）
  - pip が SSL エラーを出す環境では `--trusted-host pypi.org --trusted-host files.pythonhosted.org` を付ける
- **背景画像生成スキル**（いずれか or 両方。比較生成すると採用率が上がる）:
  - `gen-nanobanana-images`（Gemini / Nano Banana 系。`GEMINI_API_KEY` 必要）
  - `gpt-image-2`（ChatGPT サブスク経由。`codex login` 済みであること）
- **フォント**: macOS のヒラギノ／Windows の游ゴシック・游明朝／Linux 等の Noto CJK を自動探索する。別フォントにしたい・自動検出に失敗する場合は環境変数 `PRINT_CARD_FONT_MINCHO` / `PRINT_CARD_FONT_GOTHIC_W3` / `PRINT_CARD_FONT_GOTHIC_W6` でパスを指定（リポ本体は編集しない）。

## Workflow

`<SKILL_DIR>` はこのスキルのディレクトリを指す（Claude Code なら `~/.claude/skills/print-card-comp`、その他エージェントなら `~/.agents/skills/print-card-comp` 等、設置先に読み替える）。

### Phase 1: 依頼分析（AI が対話）

1. 依頼文・参考画像を読み取り、**掲載要素**を洗い出す: ロゴ / URL / キャッチコピー / 本文 / 電話番号 / 会社名 / QR の要否。
2. **サイズを確定**する（`references/card-specs.md` の表から選ぶ。既定はしおり型 W60×H180mm = 塗り足し込み 827×2480px @350dpi）。
3. 参考画像がある場合は「何を効かせているか（技法・狙い）」を分解し、**模倣ではなく昇華**の方向を探る。
4. **コンセプト方向を 2〜3 案**提案し、`AskUserQuestion` でユーザーに選んでもらう。
5. 確定要素（サイズ・採用コンセプト・コピー・配色・掲載情報）を箇条書きで合意する。

> [!tip] 解析の自由度
> Phase 1 はスクリプト化せず AI が対話で行う。依頼の形（メール / 口頭 / 既存資料）が多様なため、固定パーサより対話のほうが頑健。判断に迷う設計事項（情報の取捨・優先順位）はユーザーに確認する。

### Phase 2: QR 生成（URL がある場合）

```bash
python3 <SKILL_DIR>/scripts/gen_qr.py \
  --url "https://example.com/" \
  --out ~/Downloads/<project>/ \
  --name QR
```

- 誤り訂正は印刷向けに既定 `Q`（`--error h` で最高位）。PNG + SVG を出力する。
- 入稿用にベクター（SVG）を必ず添える。詳細は `scripts/gen_qr.py --help`。

### Phase 3: 背景画像生成（他スキルに委譲）

各コンセプトの**背景のみ**を生成する（画像内テキストなし）。アスペクト比はカード比率に合わせる（しおり型なら 9:16）。比較のため両エンジンで出すとよい。

背景生成は **`gen-nanobanana-images` / `gpt-image-2` スキルに依頼する**（自前で画像生成しない）。スクリプトを直接叩く場合の `<skills>` は設置先（Claude Code は `~/.claude/skills`、その他エージェントは `~/.agents/skills`）に読み替える。

```bash
# gen-nanobanana-images（要 GEMINI_API_KEY）
python3 <skills>/gen-nanobanana-images/scripts/generate_image.py \
  -p "<背景の英語プロンプト。文字は入れない>" -m pro -a 9:16 -s 2K -o ~/Downloads/<project>/bg

# gpt-image-2（要 codex login）
<skills>/gpt-image-2/scripts/gen.sh \
  --prompt "<背景プロンプト>" --out ~/Downloads/<project>/bg/bg-gpt.png
```

### Phase 4-5: PIL 合成（表面・裏面）

`scripts/card_compose.py` のヘルパ（`cover` / `tc` / `pc` / フォントローダ）を import して、案件ごとの合成スクリプトを書く。レイアウトは案件ごとに変わるため、**ヘルパは共通・配置は都度記述**する。

表裏それぞれの組み立てレシピ（白下地・半透明パネル・赤ライン・CTA バッジ・QR 配置等）は `references/composition-recipe.md` を参照。

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from card_compose import cover, tc, pc, load_fonts, new_canvas
# 以降、references/composition-recipe.md のレシピに沿って表裏を組む
```

### Phase 6: 成果物出力

出力先は `~/Downloads/<project>/`（ユーザー指定があればそれを優先）。スキルディレクトリ内には保存しない。

- `card-final-front.png` / `card-final-back.png`
- QR の PNG / SVG
- デザイン指示書 `.md`（サイズ・用紙・配色・入稿チェックリスト。`references/card-specs.md` のチェックリストを土台にする）

## Constraints / 注意

- **画像内に焼く日本語テキストは PIL 合成で乗せる**（生成モデルに描かせない）。
- ロゴは支給ベクター（VI）データを `alpha_composite` で正確配置。**新規作成しない**。
- 入稿は本スキルの範囲外（Illustrator/Figma でのベクター化・トンボ・色校正は別工程）。本スキルが出すのは**カンプ + 指示書**まで。
- QR は実機スキャン確認を前提に、クワイエットゾーン確保・15mm 角以上で配置。

## 関連ファイル

- `references/card-specs.md` — サイズ・解像度・入稿チェックリスト
- `references/composition-recipe.md` — 表裏の PIL 合成レシピ
- `scripts/gen_qr.py` — QR 生成（segno）
- `scripts/card_compose.py` — PIL 合成ヘルパ
