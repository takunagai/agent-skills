# PIL 合成ハウツー（組み方の定石）

`scripts/card_compose.py` のヘルパを使った合成の共通テクニック集。
**レイアウトの型（写真主役・縦書き和風・名刺グリッド等）は `layout-patterns.md` に移設**した。
ここは型に依らない「組み方の道具と定石」を扱う（型 × ここの定石 × `design-principles.md` の判断基準で 1 枚を組む）。

座標はすべて**塗り足し込みサイズ**基準（`card-specs.md` の画素数列。例: しおり型 909×2563px）。

## 共通セットアップ

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import (
    new_canvas, cover, tc, tx, fit_font, tate, pc, panel, badge,
    to_mono, duotone, ink_alpha, guides, trim, sheet, load_fonts, mmpx, save,
)

W, H = 909, 2563  # 形状に応じて card-specs.md の画素数列から
fonts = load_fonts({
    "copy":  ("mincho", 88),     # コピー（明朝）
    "catch": ("mincho", 48),     # キャッチ・ブランド短文
    "name":  ("gothic_w6", 44),  # 会社名（太ゴシック）
    "info":  ("gothic_w3", 36),  # TEL / URL（細ゴシック）
    "pop":   ("maru", 40),       # ポップ・食品系のラベル（丸ゴシック）
    "cta":   ("gothic_w6", 40),  # CTA バッジ文字
})
INK = (40, 38, 36, 255)          # ダークウォームグレー（真っ黒 #000 を避ける）
RED = (196, 24, 36, 255)         # アクセント（実製品色に色校正前提）
```

## ヘルパ逆引き（何をしたい → どれを使う）

| やりたいこと | ヘルパ | メモ |
|---|---|---|
| mm を px に換算 | `mmpx(mm)` | 3mm=41px, 15mm=207px @350dpi。散在計算を一元化 |
| 背景をカードに敷く | `cover(img, W, H, ax, ay)` | 短辺基準で拡大トリミング。`ay` 小=上寄せ（主役が下なら下げる） |
| 無地の地を作る | `new_canvas(W, H, color)` | 生成り・白・ベタ地 |
| 中央 1 行（既存互換） | `tc(d, cx, y, text, font, fill)` | y は上端 |
| 複数行・字間・左右揃え | `tx(d, (x,y), text, font, fill, align, tracking, line_height)` | `\n` で改行。`align="left"/"center"/"right"`。戻り値 (w,h) |
| 長い社名・URL を枠内に収める | `fit_font(text, role, size, max_w)` | はみ出す手前までサイズ自動縮小 |
| 縦書き | `tate(base, cx, top_y, text, font, fill, tracking)` | 1 列 1 呼び出し。複数列は `cx` を右→左にずらす。長音符・括弧は自動回転、句読点は右上へ |
| 画像・ロゴ・QR を置く | `pc(base, im, cx, cy, w=/h=)` | 中心配置。`w` か `h` でリサイズ |
| 白下地・情報パネル | `panel(base, box, radius, fill)` | 半透明角丸。`fill` の alpha で下地の透け具合を調整 |
| CTA ボタン | `badge(base, box, radius, fill, text, font)` | 角丸 + 中央テキスト |
| モノクロ（1C）化 | `to_mono(img)` | `autocontrast` 既定 ON で眠さ回避 |
| 2 色刷り（2C）化 | `duotone(img, ink, paper)` | 暗部→ink・明部→paper。特色を正確に統一 |
| 生成した飾り文字を透過パーツ化 | `ink_alpha(img, ink)` | 白地→透明・墨→ink 単色。ロゴ同様 `pc` で配置（`bg-prompt-library.md` 節 5） |
| 検版（塗り足し・安全線） | `guides(img)` | マゼンタ=仕上がり線 / シアン=安全マージン。Phase 5.5 用 |
| 仕上がりプレビュー | `trim(img)` | 塗り足しを落として仕上がり見当を確認 |
| 複数案を並べる | `sheet([a, b], labels=[...])` | 提案シート |
| 350dpi 付き保存 | `save(base, path)` | pHYs に 350dpi を書き込む |

## 表裏共通の定石

### 白下地・パネルの alpha

コピーや情報を背景の上に置くときは半透明の角丸下地で可読性を確保する。alpha の目安:

- 明るい背景・情報量多い → alpha を濃く（`fill=(252,250,245,200)` 付近）
- 暗い背景 → 下地を薄く or 白抜き文字（下地なしで白 `tx`）
- 質感を残したい → alpha 125〜180 で下地を透かす

```python
panel(base, (70, H-560, W-70, H-330), radius=24, fill=(252, 250, 246, 170))
tx(d, (W/2, H-540), "足もとから、しずかに。", fonts["copy"], INK, align="center")
```

### アクセントは 2 箇所まで

赤・朱・特色などのアクセントは **2 箇所まで**に絞ると効く（例: 区切り線 + CTA バッジ）。増やすと効果が死ぬ（`design-principles.md` の配色を参照）。

### 揃え軸を 1 本決める

裏面（情報面）は中央軸なら全要素中央、左軸なら全要素左に揃える。`tx` の `align` を混在させない。

### QR の配置

```python
qr = Image.open("QR.png")
pc(base, qr, W/2, H-620, w=mmpx(18))   # 15mm 角以上 = mmpx(15)=207px。余裕をみて 18mm
```

- **15mm 角以上**（`mmpx(15)` = 207px@350dpi）。小さいとスキャン率が落ちる
- 周囲のクワイエットゾーン（余白）を他要素で潰さない
- 1C・2C ではインク濃色の単色にする（`gen_qr.py --dark <インク色>`）

### 色数を適用する（背景生成後）

```python
bg = Image.open("bg/bg-front.png")
base = cover(bg, W, H, ay=0.45)
# 1C 案件: base = cover(to_mono(bg), W, H)
# 2C 案件: base = cover(duotone(bg, ink=(28,52,96), paper=(250,248,242)), W, H)
```

背景はグレースケールで生成し、2C は `duotone()` で色付けするのが正（`bg-prompt-library.md` の色数分岐）。

### セルフレビュー用の検版版を出す（Phase 5.5）

```python
save(guides(base), "~/Downloads/proj/front-guides.png")  # マゼンタ/シアン線入りを目視
save(trim(base),   "~/Downloads/proj/front-trim.png")    # 仕上がり見当
```

> [!warning] 文字化け回避
> 日本語テキストはすべてこの PIL フェーズで乗せる。背景生成モデルに文字を描かせない。
> フォントが見つからない環境では `card_compose` が警告を出してデフォルトに代替する（本番は要フォント）。

> [!note] 色・社名・URL はプレースホルダ
> 上のコードの数値・社名・URL・色はサンプル。実案件の支給情報・ブランドカラー（特色は DIC/PANTONE 番号）に差し替えること。

## 関連

- `layout-patterns.md` — レイアウトの型 8 種（写真主役・縦書き和風・名刺グリッド等）
- `design-principles.md` — 余白・タイポ・配色・情報階層の判断基準
- `bg-prompt-library.md` — 背景生成スタイルと色数分岐
- `card-specs.md` — サイズ・色数・入稿仕様
