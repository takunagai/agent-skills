# 背景プロンプト・ライブラリ（印刷物カンプ専用）

Phase 3（背景画像生成）で使う、印刷物**背景専用**のスタイル・プロンプト集。
このスキルで自己完結する（共有ライブラリには依存しない）。

> [!important] テキスト・ロゴ・QR は背景に焼かない
> 画像内に描かせた日本語・URL・ロゴは化ける。**背景だけを生成し、文字・ロゴ・QR はすべて PIL 合成フェーズ（`card_compose.py`）で乗せる**のがこのスキルの肝。
> したがって全プロンプトに **no-text ボイラープレート**を必ず付け、生成後にコピー・ロゴを乗せる**余白（ネガティブスペース）を残すよう指示するのが要**。

## 1. 共通ボイラープレート

全スタイルのプロンプト**末尾に必ず付ける**定型文。ここで 1 箇所定義し、各テンプレートでは `{{…}}` を埋めた本文の後ろにこれを連結する。

**no-text ボイラープレート**（文字・ロゴ・透かしを排除）:

```
no text, no letters, no words, no typography, no logos, no watermark, no signage
```

**印刷向け汎用サフィックス**（高解像度・余白確保）:

```
high resolution, clean composition, ample negative space for text overlay, print-quality
```

連結例（スタイル本文 + サフィックス + no-text の順で 1 本のプロンプトにする）:

```
<スタイル本文>, high resolution, clean composition, ample negative space for text overlay, print-quality, no text, no letters, no words, no typography, no logos, no watermark, no signage
```

- **ネガティブスペースは明示で稼ぐ** ─ モデルは放っておくと画面を埋める。`ample negative space` / `empty area in the upper third` のように**どこを空けるか**まで書くと、後でコピーやロゴを載せる余地が残る。
- 余白位置はカードのレイアウトパターン（`layout-patterns.md`）に合わせて `upper third` / `left half` / `center` 等を差し替える。

## 2. スタイル 8 種

各スタイルは「向くジャンル / 合うレイアウトパターン番号（`layout-patterns.md` のパターン1〜8）／ 英語プロンプトテンプレート（末尾に共通ボイラープレートを連結する前提）／ 注意点」で構成する。

### スタイル1: 写真調ライフスタイル

- **向くジャンル**: 人・暮らしのシーン。飲食・サロン・教室・観光・採用。**パターン1・2 向き**。
- **英語プロンプトテンプレート**:

```
Lifestyle photograph of {{シーン: a warm morning cafe scene}}, {{被写体: hands holding a coffee cup}}, natural soft window light, shallow depth of field, candid documentary mood, muted warm color grading, generous empty area in the {{余白位置: upper third}} for text overlay
```

- **注意点**: 主役を画面の片側／下寄せにして反対側を空ける。人物の顔・手元にコピーを被せない構図で指示する。

### スタイル2: 商品ブツ撮り調

- **向くジャンル**: 単一プロダクトを主役に。EC・物販・ギフト・メニュー。**パターン1・3 向き**。
- **英語プロンプトテンプレート**:

```
Studio product photograph of {{主役: a ceramic mug}} on a {{地: seamless off-white}} background, soft diffused lighting, subtle gradient backdrop, gentle soft shadow, centered subject with wide clean margins, minimalist commercial still life
```

- **注意点**: 背景は無地〜微グラデに寄せて主役を独立させる。影が強すぎると合成の白下地と喧嘩するので `gentle soft shadow` で抑える。

### スタイル3: 紙・ファブリック質感

- **向くジャンル**: 和・ナチュラル・上質路線の地。ショップカード・しおり・案内状。**パターン5・6・8 向き**。
- **英語プロンプトテンプレート**:

```
Flat top-down texture of {{素材: natural washi paper}}, soft even lighting, fine fiber detail, subtle organic irregularities, matte surface, {{色: warm ivory}} tone, uniform seamless full-frame background
```

- **注意点**: 主役のない「地」として全面テクスチャで出す。質感が強すぎると文字が沈むので `subtle` を効かせ、合成側の白下地で可読性を確保する。

### スタイル4: 抽象グラデーション

- **向くジャンル**: 世界観・ブランドカラー主役。抽象・モダン・IT・美容。**パターン2・5・7 向き。2C の素地に最適**。
- **英語プロンプトテンプレート**:

```
Smooth abstract gradient background, {{配色: soft sand to warm terracotta}}, seamless color transition, no hard edges, matte finish, calm minimal mood, large even color fields ideal for text overlay
```

- **注意点**: 色面が広く文字を最も置きやすい。2C 運用ではここを**グレースケールで出し duotone で色付け**する（色数分岐を参照）。バンディング（縞）が出たら `-s 2K` 以上で再生成。

### スタイル5: 幾何・流体

- **向くジャンル**: シェイプ・曲線のモダン装飾。IT・コンサル・イベント。**パターン5・7 向き**。
- **英語プロンプトテンプレート**:

```
Abstract {{形: fluid organic shapes}} composition, {{配色: pale blue and cream}}, smooth flowing curves, layered translucent shapes, clean modern flat design, balanced asymmetric negative space
```

- **注意点**: 要素を画面の隅・一辺に寄せて中央〜反対側を空ける。色数・形数を絞らないと騒がしくなる（`layered` は 2〜3 層まで想定で指示）。

### スタイル6: 和風文様

- **向くジャンル**: さりげない地紋。和菓子・呉服・旅館・年賀。**パターン6 向き**。
- **英語プロンプトテンプレート**:

```
Subtle traditional Japanese pattern background, {{文様: seigaiha wave pattern}}, very low contrast tone-on-tone, {{色: soft indigo on ivory}}, delicate evenly repeating motif, refined understated elegance, calm quiet empty areas
```

- **注意点**: 文様名は英語で明示（seigaiha 青海波 / asanoha 麻の葉 / kikko 亀甲 / shippo 七宝）。`tone-on-tone`・`low contrast` で「うるさくない地紋」に留め、文字が乗る前提の弱さにする。

### スタイル7: 水彩にじみ

- **向くジャンル**: 柔らかいウォッシュ。招待状・サロン・ハンドメイド。**パターン1・5 向き**。
- **英語プロンプトテンプレート**:

```
Soft watercolor wash background, {{配色: pale blush and sage}}, gentle bleeding pigments, wet-on-wet texture, hand-painted feel, light airy tone, large pale open areas for text overlay
```

- **注意点**: にじみを画面の一辺・隅に寄せ、中央を淡く空ける。彩度を上げすぎると文字が沈む＆ CMYK で沈む鮮色（後述）に触れやすいので淡色で指示する。

### スタイル8: ボタニカル

- **向くジャンル**: 植物モチーフ。ナチュラル・コスメ・フラワー・カフェ。**パターン1・3 向き**。
- **英語プロンプトテンプレート**:

```
Botanical {{表現: delicate line art}} of {{植物: eucalyptus branches}}, {{配色: sage green on cream}}, arranged along {{配置: the bottom edge}}, soft neutral background, natural elegant composition, plenty of empty space in the center
```

- **注意点**: `line art`（線画）と `realistic photograph`（写実）で質感が大きく変わるので用途で選ぶ。モチーフを一辺に寄せ、コピー・ロゴ用の中央余白を必ず残す。

## 3. 色数分岐（生成方針を色数で変える）

色数は `references/card-specs.md` で確定する。**背景生成の作り方が色数で変わる**ので、Phase 1 の確定色数に従って以下を選ぶ。

### 1C（モノクロ）

次のどちらでもよい。**仕上がりを見て選ぶ**。

1. **プロンプトで直接モノクロ生成** ─ スタイル本文に次を足す:

   ```
   monochrome, grayscale, black and white
   ```

2. **フルカラーで生成後にモノクロ化** ─ PIL 側で `to_mono()` を適用（`autocontrast=True` で印刷時の眠さを防ぐ）:

   ```python
   from card_compose import to_mono
   base = to_mono(bg, autocontrast=True)   # RGBA で返る
   ```

### 2C（特色 2 色）─ グレースケール生成 → duotone が正

**背景はグレースケールで生成し、PIL 側で `duotone()` で色付けするのが正**。
プロンプトで 2 色を直接指定すると**インク色がブレて特色再現にならない**（モデルが勝手に中間色を混ぜる）。特色はグレースケール階調に対して後段でマッピングする。

```python
from card_compose import duotone
# ink = 濃色インク（DIC/PANTONE を CMYK/RGB 近似）, paper = 地（用紙色）
base = duotone(bg, ink=(30, 40, 90), paper=(245, 242, 235))   # RGBA で返る
```

- グレースケール生成には 1C と同じく `monochrome, grayscale` をプロンプトに足すか `to_mono()` を通す。
- 特色番号（DIC / PANTONE）は指示書に明記し、実物は色校正する（`card-specs.md` の入稿ルール準拠）。抽象グラデーション（スタイル4）が 2C の素地に最も向く。

### 4C（フルカラー）

スタイルのプロンプトのまま生成する（追加の色制約なし）。ただし蛍光・ネオン等 **CMYK で沈む鮮色**は避けるか指示書に申し送る（`card-specs.md`「CMYK で沈む色」参照）。

## 4. エンジン別の実行例

背景生成は `gen-nanobanana-images` / `gpt-image-2` スキルに委譲する（自前で画像生成しない）。
`<skills>` はスキルの設置先に読み替える（**Claude Code は `~/.claude/skills`**、その他エージェントは `~/.agents/skills` 等）。

**gen-nanobanana-images**（Gemini / Nano Banana 系。要 `GEMINI_API_KEY`）:

```bash
python3 <skills>/gen-nanobanana-images/scripts/generate_image.py \
  -p "<英語プロンプト（本文 + 汎用サフィックス + no-text）>" \
  -m pro -a <カード比率> -s 2K -o ~/Downloads/<project>/bg
```

`-a`（アスペクト比）は `card-specs.md` の背景アスペクト比表に合わせる:

| 形状 | `-a` の値 |
|------|-----------|
| しおり型 / DL | `9:16` |
| 名刺 | `3:2` |
| ポストカード | `3:2` |
| 正方形カード | `1:1` |
| A6 フライヤー | `3:4` |

**gpt-image-2**（ChatGPT サブスク経由。要 `codex login`）:

```bash
<skills>/gpt-image-2/scripts/gen.sh \
  --prompt "<英語プロンプト（本文 + 汎用サフィックス + no-text）>" \
  --out ~/Downloads/<project>/bg/bg-gpt.png
```

- **比較のため両エンジンで出すと採用率が上がる** ─ 同じプロンプトで Nano Banana と GPT Image 2 の両方を生成し、質感・余白・破綻の少なさで選ぶ。
- カバーフィット（`card_compose.cover`）で塗り足し込みサイズへトリミングするので、生成比率は表の近似で可。

---

関連: `layout-patterns.md`（どの型にどのスタイルを合わせるか）/ `card-specs.md`（アスペクト比・色数・入稿仕様）
