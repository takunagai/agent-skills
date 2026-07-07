---
name: print-card-comp
description: "Generate print-ready design comps for cards and small print materials (business cards, bookmarks/shiori, postcards, DL cards, shop/stamp cards, bi-fold cards, flyers) from a brief to finished front/back PNGs. Covers request analysis with color-count selection (4C/4C full-color, 4C/1C, 1C/1C mono, 2C spot-color), a library of 8 layout patterns for varied output, QR code generation (segno), PIL-based composition (copy/logo/info overlay with no text corruption, horizontal + vertical/tategaki text, tracking, duotone, registration guides), a post-composition self-review loop, and a print spec sheet with bleed/safe-margin. 印刷物のデザインカンプ生成。「カンプ作って」「印刷物を作りたい」「名刺デザイン」「しおり型カード」「ハガキデザイン」「ポストカード」「ショップカード」「スタンプカード」「二つ折り」「DLカード」「表裏のデザイン」「2色刷り」「モノクロ印刷」「縦書きの印刷物」などのリクエストで使う。背景画像生成は gen-nanobanana-images / gpt-image-2 スキルを内部利用する。"
---

# Print Card Comp Generation（印刷物カードカンプ生成）

## Overview

依頼内容（依頼文・参考画像）から、印刷物の**表裏デザインカンプ（PNG）**と**入稿用デザイン指示書**を一括生成するスキル。名刺・しおり型カード・ポストカード・DL カード・ショップ/スタンプカード・二つ折り・フライヤー等に対応する。

役割分担:

- **AI（このスキル）が対話的に行う**: 依頼分析・掲載要素の整理・サイズと色数の確定・コンセプト 2〜3 案の提案（異なるレイアウトパターンから）・プロンプト組み立て・採用案の確定・合成後のセルフレビュー
- **スクリプトが決定的に行う**: QR コード生成（`scripts/gen_qr.py`）・PIL 合成のヘルパ（`scripts/card_compose.py`）
- **他スキルに委譲する**: 背景画像生成（`gen-nanobanana-images` / `gpt-image-2`）

> [!note] テキストは生成画像に焼かない
> 画像内の日本語コピー・会社情報・URL は生成モデルに描かせると化ける。**背景だけを生成し、文字・ロゴ・QR は PIL 合成フェーズで乗せる**のが本スキルの肝。横書きも縦書きもすべて PIL 側で組む。

### Prerequisites

- **Python deps**: `pip install -r requirements.txt`（`segno` + `Pillow`）
  - pip が SSL エラーを出す環境では `--trusted-host pypi.org --trusted-host files.pythonhosted.org` を付ける
  - PEP 668（externally-managed）環境では `pip install --user` か、システムを汚さないなら `python3 -m venv --system-site-packages` の仮想環境に入れる
- **背景画像生成スキル**（いずれか or 両方。比較生成すると採用率が上がる）:
  - `gen-nanobanana-images`（Gemini / Nano Banana 系。`GEMINI_API_KEY` 必要）
  - `gpt-image-2`（ChatGPT サブスク経由。`codex login` 済みであること）
- **フォント**: macOS のヒラギノ（明朝 ProN / 角ゴ W3・W6 / 丸ゴ ProN W4）、Windows の游書体・メイリオ、Linux 等の Noto CJK を自動探索する。丸ゴが無い環境は角ゴにフォールバックする。別フォント指定・自動検出失敗時は環境変数 `PRINT_CARD_FONT_MINCHO` / `_GOTHIC_W3` / `_GOTHIC_W6` / `_MARU` でパス指定（リポ本体は編集しない）。

## Workflow

`<SKILL_DIR>` はこのスキルのディレクトリを指す（Claude Code なら `~/.claude/skills/print-card-comp`、その他エージェントなら `~/.agents/skills/print-card-comp` 等、設置先に読み替える）。

### Phase 1: 依頼分析（AI が対話）

1. 依頼文・参考画像を読み取り、**掲載要素**を洗い出す: ロゴ / URL / キャッチコピー / 本文 / 電話番号 / 会社名 / QR の要否 / 支給素材（ロゴ VI・写真）。
2. 下の**確認マトリクス**で不足項目を詰める。**依頼文から確定できる項目は聞かない**（冗長な確認は避ける）。判断に迷う設計事項（情報の取捨・優先順位・色数）だけを `AskUserQuestion` で確認する。

   | 項目 | 既定値 | 確認要否 |
   |---|---|---|
   | サイズ・形状 | しおり型 60×180mm（塗り足し込み 909×2563px） | 依頼で不明なら確認 |
   | 縦横 | 形状に従う | ─ |
   | 片面 / 両面 | 両面 | 依頼で不明なら確認 |
   | **色数** | **4C/4C（両面フルカラー）** | ジャンル・予算感で確認推奨 |
   | 組方向 | 横書き | 和・書店・伝統系なら縦書きを提案 |
   | トーン・ジャンル | 依頼から推定 | 参考画像があれば分解 |
   | 掲載要素 | 洗い出し結果 | 取捨に迷えば確認 |
   | 支給素材 | ロゴ VI・写真の有無 | 必ず確認（カンプ用仮ロゴは入稿不可） |
   | QR 要否 | URL があれば付与 | ─ |
   | 加工 | 角丸 R3〜5mm・マット PP は任意 | 提案 |

   **色数の AskUserQuestion 選択肢**（`card-specs.md` の色数節に準拠）:
   - フルカラー（4C/4C）⭐ ─ 写真主役・標準
   - 表フルカラー・裏モノクロ（4C/1C）─ コスト圧縮
   - モノクロ（1C/1C）─ 上質・端正
   - 2 色刷り（特色指定 2C）─ ブランドカラーを正確に

3. 参考画像がある場合は「何を効かせているか（技法・狙い）」を分解し、**模倣ではなく昇華**の方向を探る。
4. **コンセプト方向を 2〜3 案**提案する。各案は必ず `references/layout-patterns.md` の**異なるパターン**から選び、**「パターン × 背景スタイル × 配色 × タイポ設定 × 狙い」**の組で提示する（例: 案 A =「パターン1 写真主役×スタイル1 ライフスタイル×ナチュラル配色」、案 B =「パターン6 縦書き和風×スタイル3 紙質感×和配色」）。`AskUserQuestion` で選んでもらう。
5. 確定要素（サイズ・色数・採用コンセプト＝パターン・コピー・配色・掲載情報）を箇条書きで合意する。

> [!tip] 解析の自由度
> Phase 1 はスクリプト化せず AI が対話で行う。依頼の形（メール / 口頭 / 既存資料）が多様なため、固定パーサより対話のほうが頑健。設計の判断基準は `references/design-principles.md` を土台にする。

### Phase 2: QR 生成（URL がある場合）

```bash
python3 <SKILL_DIR>/scripts/gen_qr.py \
  --url "https://example.com/" \
  --out ~/Downloads/<project>/ \
  --name QR
```

- 誤り訂正は印刷向けに既定 `Q`（`--error h` で最高位）。PNG + SVG を出力する。
- **1C・2C 案件**は QR を濃色インクの単色にする（`--dark "#1c3460"` のようにインク色を指定）。
- 入稿用にベクター（SVG）を必ず添える。詳細は `scripts/gen_qr.py --help`。

### Phase 3: 背景画像生成（他スキルに委譲）

各コンセプトの**背景のみ**を生成する（画像内テキストなし）。プロンプトとスタイルは `references/bg-prompt-library.md` から選ぶ（no-text 定型文・スタイル 8 種・エンジン別実行例を収録）。アスペクト比はカード比率に合わせる（`card-specs.md` の表）。

色数分岐:

- **1C**: プロンプトにモノクロ指定を入れるか、生成後に `to_mono()` を適用。
- **2C**: **グレースケールで生成し、PIL 側で `duotone(bg, ink, paper)` で色付け**するのが正（プロンプトで 2 色指定するとインク色がブレる）。
- **4C**: スタイルのまま生成。

背景生成は **`gen-nanobanana-images` / `gpt-image-2` スキルに依頼する**（自前で画像生成しない）。比較のため両エンジンで出すと採用率が上がる。

**装飾文字パーツ（例外運用）**: 筆文字・カリグラフィ等の「絵としての文字」（1 語〜 1 フレーズの飾り文字）だけは、背景とは別に生成してよい。真っ白な地に単色で生成し、`ink_alpha()` で透過 + 単色インク化してロゴと同じ扱いで `pc()` 合成する（K 単色・特色単版として扱えるため 1C・2C でも使える）。プロンプトの約束・テンプレート・合成手順は `references/bg-prompt-library.md` の節 5。**社名・TEL・URL 等の情報テキストは対象外**（従来どおり PIL）。誤字は確率で出るため**目視確認必須**。

### Phase 4-5: PIL 合成（表面・裏面）

`scripts/card_compose.py` のヘルパを import して、案件ごとの合成スクリプトを書く。3 つのリファレンスを役割で使い分ける:

- **型** → `references/layout-patterns.md`（採用パターンの ASCII 図・使用ヘルパ・コードスケッチ）
- **組み方** → `references/composition-recipe.md`（ヘルパ逆引き・白下地 alpha・アクセント・QR・色数適用・検版）
- **判断基準** → `references/design-principles.md`（余白・タイポ・配色・情報階層）

案件ごとの合成スクリプトは**成果物フォルダに `compose.py` として保存する**（再現性・後からの座標調整のため）。

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from card_compose import (
    new_canvas, cover, tc, tx, fit_font, tate, pc, panel, badge,
    to_mono, duotone, guides, trim, sheet, load_fonts, mmpx, save,
)
# 採用パターンの layout-patterns.md コードスケッチを出発点に、表裏を組む
```

### Phase 5.5: セルフレビュー（AI が目視して修正）

合成したら **AI が出力 PNG を目視レビューして修正する**。最大 2 周。

1. `guides()` で検版版（マゼンタ=仕上がり線 / シアン=安全マージン）を書き出し、`Read` で目視する。細部は該当領域をクロップして `Read` すると精度が上がる。
2. 次のチェックリストで判定:
   - 文字切れ・はみ出しがない
   - 要素かぶり（QR と文字・パネル端で切れる等）がない
   - 主要要素が安全マージン（シアン線）の内側にある
   - 文字と背景のコントラストが十分（白抜きは特に）
   - 揃え軸がブレていない
   - アクセントが 2 箇所以内
   - QR が 15mm 角以上 + クワイエットゾーン確保
   - 塗り足し領域（マゼンタ線の外）に切れて困る要素がない
3. 問題があれば `compose.py` の座標・サイズを修正して再合成し、再度目視する（最大 2 周）。

### Phase 6: 成果物出力

出力先は `~/Downloads/<project>/`（ユーザー指定があればそれを優先）。スキルディレクトリ内には保存しない。

```
~/Downloads/<project>/
├── QR.png / QR.svg              # QR（PNG + 入稿用 SVG）
├── spec-sheet.md                # デザイン指示書（spec-sheet-template.md を埋める）
├── proposal-sheet.png           # 複数案の比較（sheet() で生成。任意）
├── concept-a/
│   ├── front.png / back.png     # 採用カンプ（塗り足し込み・350dpi）
│   ├── front-trim.png / back-trim.png   # 仕上がりプレビュー（trim()）
│   ├── compose.py               # この案の合成スクリプト（再現用）
│   └── bg/                      # 生成した背景
└── concept-b/ ...
```

- 指示書 `spec-sheet.md` は `references/spec-sheet-template.md` をコピーして埋める（色数・用紙・配色・使用フォント・QR・入稿チェックリスト・申し送り）。

## Constraints / 注意

- **確定した色数を必ず守る**: 1C 案件に色を混ぜない。2C はインク 2 色 + 紙色 + 網 % のみで組む（特色は DIC/PANTONE 番号で指示書に明記）。
- **画像内に焼く日本語テキストは PIL 合成で乗せる**（生成モデルに描かせない）。縦書きも `tate()` で PIL 側。例外は装飾文字パーツのみ（Phase 3 / `bg-prompt-library.md` 節 5。目視確認必須・情報テキスト不可）。
- **黒文字は K 単色**（リッチブラック禁止）。写真の黒はリッチブラック可。
- ロゴは支給ベクター（VI）データを `pc` で正確配置。**新規作成しない**。
- 入稿は本スキルの範囲外（Illustrator/Figma でのベクター化・トンボ・分版・色校正は別工程）。本スキルが出すのは**カンプ + 指示書**まで。
- QR は実機スキャン確認を前提に、クワイエットゾーン確保・15mm 角以上（`mmpx(15)`=207px@350dpi）で配置。

## 関連ファイル

- `references/card-specs.md` — サイズ・色数・入稿チェックリスト・用紙 × 色数の相性
- `references/design-principles.md` — 余白・タイポ・配色・情報階層の判断基準
- `references/layout-patterns.md` — レイアウトの型 8 種（コンセプト提案の核）
- `references/composition-recipe.md` — PIL 合成のヘルパ逆引き・組み方の定石
- `references/bg-prompt-library.md` — 背景生成スタイル 8 種・色数分岐・エンジン別実行例
- `references/spec-sheet-template.md` — デザイン指示書の穴埋めテンプレート
- `scripts/gen_qr.py` — QR 生成（segno）
- `scripts/card_compose.py` — PIL 合成ヘルパ（組版・縦書き・色数・検版）
