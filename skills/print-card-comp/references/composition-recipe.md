# PIL 合成レシピ（表面・裏面）

`scripts/card_compose.py` のヘルパを使った表裏組み立ての定石。**レイアウトは案件ごとに変わる**ので、
ここはあくまで「写真主役カード」の典型形。座標は塗り足し込みサイズ基準（例: しおり型 827×2480px）。

共通の読み込み:

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import new_canvas, cover, tc, pc, panel, badge, load_fonts, save

W, H = 827, 2480  # 形状に応じて references/card-specs.md から
fonts = load_fonts({
    "copy":  ("mincho", 72),     # コピー（明朝）
    "catch": ("mincho", 40),     # キャッチ・ブランド短文
    "name":  ("gothic_w6", 44),  # 会社名（太ゴシック）
    "info":  ("gothic_w3", 36),  # TEL / URL（細ゴシック）
    "cta":   ("gothic_w6", 40),  # CTA バッジ文字
})
INK = (40, 38, 36, 255)          # ダークウォームグレー（真っ黒を避ける）
RED = (196, 24, 36, 255)         # アクセント（実製品色に色校正前提）
```

## 表面 — 写真主役

1. **背景**: 生成画像をカバーフィットしてキャンバスに。
2. **白下地 + コピー**: コピー背後に薄い白下地（可読性確保）を敷き、明朝でコピーを置く。
3. **ロゴ**: 支給データを `pc` で正確配置（小さめ）。

```python
bg = Image.open("bg/bg-front.png")
base = cover(bg, W, H, ax=0.5, ay=0.45)          # 主役が下 1/3 なら ay を下げる
d = ImageDraw.Draw(base)

panel(base, (70, 1980, W-70, 2230), radius=24, fill=(252, 250, 246, 125))  # 薄い白下地
tc(d, W/2, 2010, "<メインコピー（明朝・1 行）>", fonts["copy"], INK)
tc(d, W/2, 2120, "<キャッチ（商品・補足の短文）>", fonts["catch"], INK)

logo = Image.open("assets/logo.png")
pc(base, logo, W/2, 2330, w=360)                  # ロゴは VI データに後で差し替え
save(base, "~/Downloads/<project>/card-final-front.png")
```

ポイント:
- 白下地の alpha は背景の明暗で調整（125〜200）。明るい背景なら濃く、暗い背景なら薄く or 白抜き文字。
- スポットカラー演出をするなら、背景生成側でモノトーン化し、被写体の一部だけ彩度を残す指示を出す。

## 裏面 — 情報・余白主役

1. **背景**: 無地（生成り or 白）または無地フェルトの生成画像。
2. **半透明パネル**: 情報を載せる角丸パネル。
3. 上から: ロゴ → 赤の区切り線 → ブランド短文（明朝）→ 会社名（太ゴシック）→ TEL/URL（細ゴシック）→ CTA バッジ → QR。

```python
base = new_canvas(W, H, (245, 241, 233, 255))     # 生成り地（無地なら生成画像不要）
d = ImageDraw.Draw(base)

panel(base, (70, 250, W-70, H-180), radius=28, fill=(252, 250, 245, 214))

logo = Image.open("assets/logo.png"); pc(base, logo, W/2, 420, w=420)
d.line((150, 560, W-150, 560), fill=RED, width=4)  # 赤の区切り

tc(d, W/2, 640,  "<ブランド短文 1 行目>", fonts["catch"], INK)
tc(d, W/2, 700,  "<ブランド短文 2 行目>", fonts["catch"], INK)

tc(d, W/2, 900,  "○○株式会社", fonts["name"], INK)
tc(d, W/2, 980,  "TEL 000-0000-0000", fonts["info"], INK)
tc(d, W/2, 1040, "https://example.com/", fonts["info"], INK)

badge(base, (W/2-210, 1180, W/2+210, 1300), radius=44, fill=RED,
      text="詳しくはこちら", font=fonts["cta"])

qr = Image.open("QR.png"); pc(base, qr, W/2, 1620, w=330)   # 15mm 角以上 = 約 207px@350dpi 以上
save(base, "~/Downloads/<project>/card-final-back.png")
```

ポイント:
- パネル fill の alpha（214 程度）で「下地の質感を残しつつ文字が読める」バランスを取る。
- アクセント（赤等）は **2 箇所まで**に絞ると効く（例: 区切り線 + CTA バッジ）。増やすと効果が死ぬ。
- QR は 15mm 角以上（350dpi で約 207px 以上）、周囲のクワイエットゾーンを潰さない。

> [!warning] 文字化け回避
> 日本語テキストはすべてこの PIL フェーズで乗せる。背景生成モデルに文字を描かせない。
> フォントが見つからない環境では `card_compose` が警告を出してデフォルトに代替する（本番は要フォント）。

> [!note] 上記の会社情報・色はサンプル
> 数値・社名・URL・色はプレースホルダ。実案件の支給情報・ブランドカラーに差し替えること。
