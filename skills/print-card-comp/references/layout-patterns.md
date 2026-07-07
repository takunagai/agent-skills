# レイアウトパターン・カタログ

印刷物カンプの骨格を決める 8 つのレイアウトパターン集。AI がコンセプトを提案するとき、
このカタログから型を選んで案を組み立てる。**バリエーションの核**となるリファレンス。

## 原則

- **コンセプト提案 2〜3 案は、必ず異なるパターンから選ぶ**。同じ型の色違い・写真違いを複数案にしない。型そのものを変えることで、依頼主が「方向性」を選べるようにする。
- **1 案 = パターン × 背景スタイル × 配色 × タイポ設定 × 狙い の組**で構成する。この 5 要素を各案で明示する（例: 「パターン2 × 暗部グラデーション背景 × モノトーン + 金 × 明朝大級数・字間広め × 高級感で選ばせる」）。
- 背景スタイルの具体指定は `bg-prompt-library.md`、ジャンプ率・字間・余白などの判断基準は `design-principles.md` を参照する。本ファイルは「どの構造に、どのヘルパで、何を置くか」の型を提供する。
- 座標はすべて**塗り足し込みサイズ @350dpi** 基準（`card-specs.md` のサイズ早見表と一致）。安全ラインは端から 8mm ≒ `mmpx(8)` = 110px、スミ文字は RGB(40,38,36)。

---

## パターン1: 写真主役・センター軸

1. **適性** ─ 縦長（しおり・DL）や 3:2（ポストカード）で映える。カフェ・雑貨・写真館などエモーショナル系。写真ありきなので 4C 前提。
2. **レイアウト図**

```
┌──────────┐
│░░░░░░░░░░│  ← 全面写真（cover, ay=0.42 で主役やや上）
│░░░░░░░░░░│
│░░░░░░░░░░│
│░░░░░░░░░░│
│┌────────┐│
││ コピー  ││  ← 下部白パネル（panel・半透明）
││ キャッチ ││     すべて中央揃え（tc）
││  logo   ││
│└────────┘│
└──────────┘
```

3. **構成要素と使用ヘルパ** ─ 背景 = `cover`、可読性のための白下地 = `panel`（alpha 125〜200）、コピー/キャッチ = `tc`（中央 1 行）、ロゴ = `pc`。
4. **背景プロンプトの方向** ─ 実写フォト系（自然光・被写界深度）。パネルを敷く下部は情報量を抑えた素材にすると文字が沈まない。
5. **注意点** ─ パネルの alpha は背景の明暗で調整（明るい背景ほど濃く）。アクセントは区切り線 + ロゴ程度に留める。`composition-recipe.md` の「写真主役カード」がこの型の詳細版。
6. **コードスケッチ**（しおり 909×2563）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import cover, panel, tc, pc, load_fonts, save
W, H = 909, 2563
f = load_fonts({"copy": ("mincho", 66), "catch": ("gothic_w3", 34)})
INK = (40, 38, 36, 255)
base = cover(Image.open("bg/front.png"), W, H, ax=0.5, ay=0.42)  # 主役を上へ寄せる
d = ImageDraw.Draw(base)
panel(base, (90, 1980, W-90, 2360), radius=28, fill=(252, 250, 246, 150))
tc(d, W/2, 2030, "こころに、しおりを。", f["copy"], INK)
tc(d, W/2, 2140, "季節をひらく一冊と。", f["catch"], INK)
pc(base, Image.open("assets/logo.png"), W/2, 2280, w=300)
save(base, "~/Downloads/proj/p1-front.png")
```

---

## パターン2: 全面写真・白抜きタイポ

1. **適性** ─ 横長ポストカード・A6 で高級感を出す型。アパレル・美容・ホテルなどファッション寄り。パネルを使わず暗部に白文字を直接乗せる。4C 専用。
2. **レイアウト図**

```
┌───────────────────────┐
│░░░░░░░░░░░░░░░░░░░░░░░░░│  明部（写真の主役）
│░░░░░░░░░░░░░░░░░░░░░░░░░│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  ← 暗部を下 1/3 に集める
│ SUMMER                │     白抜きタイポ（tx / 白）
│ COLLECTION   2026 新作 │     左下・左揃えが定番
└───────────────────────┘
```

3. **構成要素と使用ヘルパ** ─ 背景 = `cover`（`ay` を下げ暗部を下へ）、コピー = `tx(align="left", fill=白)`、小見出し = `tx`。パネルは使わない。
4. **背景プロンプトの方向** ─ 暗部グラデーション系。**背景生成側で「下 1/3 に暗い領域（影・陰影・暗い背景）を作る」指示を必ず入れる**。白文字が乗る土台を写真自体に用意させるのがこの型の肝。
5. **注意点** ─ 暗部が薄いと白文字が読めない。生成後に文字位置のコントラストを目視確認する。文字は仕上がり短辺の 8% 以上内側（安全 8mm）に収める。白抜きは 1C・クラフト紙では成立しないので 4C 限定。
6. **コードスケッチ**（ポストカード 2122×1461）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import cover, load_font, tx, save
W, H = 2122, 1461
h = load_font("mincho", 120); sub = load_font("gothic_w3", 44)
WHITE = (252, 250, 246, 255)
base = cover(Image.open("bg/hero.png"), W, H, ax=0.5, ay=0.30)  # 暗部を下へ寄せる
d = ImageDraw.Draw(base)
tx(d, (150, 1030), "SUMMER\nCOLLECTION", h, WHITE, align="left",
   tracking=h.size * 0.04, line_height=1.15)
tx(d, (156, 1320), "2026 / 新作フェア開催", sub, WHITE, align="left",
   tracking=sub.size * 0.02)
save(base, "~/Downloads/proj/p2-front.png")
```

---

## パターン3: 上下分割

1. **適性** ─ 写真 2/3 + 情報ベタ帯 1/3 の安定構成。ショップカード・DM で情報量が多いとき。写真と情報を物理的に分けるので破綻しにくい。4C／4C・4C/1C 相性良。
2. **レイアウト図**

```
┌───────────────┐
│░░░░░░░░░░░░░░░░│
│░░░ 写真 2/3 ░░░│  cover（上 2/3）
│░░░░░░░░░░░░░░░░│
├───────────────┤  ← 分割ライン
│   Shop Name    │  情報ベタ帯 1/3
│  住所 / 時間    │  panel(radius=0) で無地帯
│  [ CTA バッジ ] │
└───────────────┘
```

3. **構成要素と使用ヘルパ** ─ 写真 = `cover` してキャンバス上部に `alpha_composite`、帯 = `panel(radius=0)`（不透明ベタ）、店名 = `tc`、区切り = `ImageDraw.line`、住所等 = `tx(align="center")`、CTA = `badge`。
4. **背景プロンプトの方向** ─ 実写フォト系（上部専用に生成）。帯は生成せず PIL のベタ地で作るため、背景プロンプトは写真部分だけを想定すればよい。
5. **注意点** ─ 分割位置は仕上がりの 2/3 前後で固定すると安定。帯の地色と文字色のコントラストを確保。折り加工がある場合は分割線を折り目に重ねない。
6. **コードスケッチ**（A6 1530×2122）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import new_canvas, cover, load_font, panel, tc, tx, badge, save
W, H = 1530, 2122
shop = load_font("mincho", 56); info = load_font("gothic_w3", 34); cta = load_font("gothic_w6", 38)
INK = (40, 38, 36, 255); ACC = (176, 96, 60, 255)
base = new_canvas(W, H, (252, 250, 246, 255))
base.alpha_composite(cover(Image.open("bg/shop.png"), W, 1415, ay=0.5), (0, 0))  # 上 2/3
d = ImageDraw.Draw(base)
panel(base, (0, 1415, W, H), radius=0, fill=(245, 241, 233, 255))  # 情報ベタ帯
tc(d, W/2, 1520, "Bakery Kinoha", shop, INK)
d.line((260, 1620, W-260, 1620), fill=ACC, width=4)
tx(d, (W/2, 1680), "川西市栄町 0-0-0\n火〜日 8:00–18:00", info, INK, align="center", line_height=1.7)
badge(base, (W/2-230, 1900, W/2+230, 2010), radius=44, fill=ACC, text="オンライン注文", font=cta)
save(base, "~/Downloads/proj/p3-front.png")
```

---

## パターン4: 左寄せグリッド

1. **適性** ─ 名刺横型 1337×841 の定石。士業・IT・コーポレート。写真に頼らず組版で品を出すので 1C・2C 適性が高い。
2. **レイアウト図**

```
┌──────────────────────┐
│                       │
│ 会社名（fit_font）      │  ← 揃え軸 AXIS を 1 本立て
│ ──                    │     すべて左揃え（tx left）
│ 氏名                   │
│ 肩書き                 │
│                       │
│ TEL / mail / URL       │
└──────────────────────┘
   ↑ 左余白を広く・右を空ける非対称
```

3. **構成要素と使用ヘルパ** ─ 揃え軸 `AXIS`（X 座標を 1 本に統一）、社名 = `fit_font`（長さでサイズ自動調整）+ `tx(align="left")`、氏名/肩書き/連絡先 = `tx(align="left")`、短い下線 = `ImageDraw.line`。
4. **背景プロンプトの方向** ─ 無地または微テクスチャ系（紙目・薄い箔押し風）。写真背景は使わないのが基本。地はベタか `new_canvas` の生成り。
5. **注意点** ─ 揃え軸は 1 本に絞る（複数軸は雑然とする）。左余白を右より広く取り非対称にするとモダン。社名が長い案件は `fit_font` で必ず収める。連絡先の行間は 1.9 前後で開ける。
6. **コードスケッチ**（名刺横 1337×841）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import new_canvas, load_font, fit_font, tx, save
W, H = 1337, 841
INK = (40, 38, 36, 255); AXIS = 150  # 左の揃え軸
base = new_canvas(W, H, (252, 250, 246, 255))
d = ImageDraw.Draw(base)
company = fit_font("ナガイ商店デザイン合同会社", "gothic_w6", 58, max_w=W-AXIS-150)
tx(d, (AXIS, 200), "ナガイ商店デザイン合同会社", company, INK, align="left", tracking=company.size*0.03)
d.line((AXIS, 320, AXIS+120, 320), fill=INK, width=3)  # 短い軸下線
tx(d, (AXIS, 380), "ながたく", load_font("mincho", 44), INK, align="left")
tx(d, (AXIS, 450), "Web Designer / AI Consultant", load_font("gothic_w3", 26), INK, align="left")
tx(d, (AXIS, 590), "TEL 000-0000-0000\ninfo@example.com\nhttps://example.com/",
   load_font("gothic_w3", 26), INK, align="left", line_height=1.9)
save(base, "~/Downloads/proj/p4-front.png")
```

---

## パターン5: タイポグラフィ主体

1. **適性** ─ 写真なし。ベタ地または微テクスチャに大級数のコピーを主役化する。告知カード・イベント・引っ越し案内。特色 2 色（濃色 + 差し色）で映える 2C 向き。
2. **レイアウト図**

```
┌─────────────┐
│             │
│    夜の      │  ベタ地
│   読書会     │  大級数コピー（tx center）
│  ─────      │  字間を広めに取る
│ 毎月第3金曜   │
│             │
└─────────────┘
```

3. **構成要素と使用ヘルパ** ─ 地 = `new_canvas`（濃色ベタ）、主コピー = `tx(align="center", tracking 広め)`、区切り = `ImageDraw.line`、日時等 = `tx`。写真・パネルは使わない。
4. **背景プロンプトの方向** ─ 無地・微テクスチャ系のみ（紙目・かすれ・箔風）。基本は生成画像を使わず PIL のベタ地でよい。テクスチャを足すなら極薄で文字を邪魔しないもの。
5. **注意点** ─ 主役はタイポなので、ジャンプ率をメリハリ側（2.5〜4:1）に振り、字間は見出しで size×0.04〜0.08 と広めに。色数を絞るほど級数と余白で語らせる。2C なら濃色 = 文字、特色 = 差し色に役割を分ける。
6. **コードスケッチ**（正方形 1337×1337）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import ImageDraw
from card_compose import new_canvas, load_font, tx, save
W, H = 1337, 1337
BASE_C = (30, 42, 54, 255)   # 濃紺ベタ（2C の濃色インク側）
ACC = (208, 168, 92, 255)    # 特色アクセント（金）
PAPER = (245, 241, 233, 255)
base = new_canvas(W, H, BASE_C)
d = ImageDraw.Draw(base)
h = load_font("gothic_w6", 150)
tx(d, (W/2, 430), "夜の\n読書会", h, PAPER, align="center", tracking=h.size*0.06, line_height=1.25)
d.line((W/2-160, 870, W/2+160, 870), fill=ACC, width=4)
tx(d, (W/2, 930), "毎月第 3 金曜 19:00–", load_font("gothic_w3", 40), ACC,
   align="center", tracking=40*0.08)
save(base, "~/Downloads/proj/p5-front.png")
```

---

## パターン6: 縦書き和風

1. **適性** ─ 明朝の縦組みに朱系の差し色と広い余白。和菓子・書店・旅館・伝統工芸。DL・しおりなど縦長で映える。1C・2C とも好相性。
2. **レイアウト図**

```
┌───────────┐
│  列2  列1  │  ← 列は右→左に読む
│   ｜ 花 和 │
│   ｜ ご 菓 │  tate() で 1 列ずつ
│   ｜ よ 子 │  朱の縦罫（｜）を添える
│   ｜ み    │
│           │
│  [家紋]    │  ロゴ・家紋は pc で下部に
└───────────┘
```

3. **構成要素と使用ヘルパ** ─ 縦書き = `tate(base, cx, top_y, ...)`（1 列 1 呼び出し。複数列は `cx` を右→左にずらす）、縦罫 = `ImageDraw.line`、家紋/ロゴ = `pc`。地は `new_canvas` の生成り。
4. **背景プロンプトの方向** ─ 和紙・微テクスチャ系（生成り・かすれ・墨のにじみ）。写真を使うなら余白の多い静物・和素材を薄く。文字域には何も置かない。
5. **注意点** ─ 列は必ず右→左。主題を大きい明朝、副題を小さい明朝にしてジャンプ率をつける。長音符・括弧は `tate` が自動回転、句読点は右上に寄る。余白を広く取り「間」で品を出す。朱は 2 箇所まで。
6. **コードスケッチ**（DL 1447×2976）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import new_canvas, load_font, tate, pc, save
W, H = 1447, 2976
INK = (40, 38, 36, 255); SHU = (183, 62, 46, 255)  # 朱
base = new_canvas(W, H, (250, 247, 240, 255))
mincho_l = load_font("mincho", 96); mincho_s = load_font("mincho", 48)
top = 380
tate(base, W-360, top, "和菓子 花ごよみ", mincho_l, INK, tracking=18)       # 1 列目（右）
tate(base, W-360-150, top+120, "季節をいただく", mincho_s, INK, tracking=10)  # 2 列目（左へ）
d = ImageDraw.Draw(base)
d.line((W-560, top, W-560, top+900), fill=SHU, width=4)  # 朱の縦罫
pc(base, Image.open("assets/kamon.png"), 360, 2500, w=240)
save(base, "~/Downloads/proj/p6-front.png")
```

---

## パターン7: 帯・バンド

1. **適性** ─ 写真の上を色帯が横断し、帯にコピー/ロゴを乗せる。フライヤー・DL カード・オープン告知。訴求点を 1 本の帯に集約できる。4C。
2. **レイアウト図**

```
┌───────────────────────┐
│░░░░░░░░░░░░░░░░░░░░░░░░░│  写真
│███████████████████████│  ← 横断色帯（panel・半透明）
│█   OPEN 7.20 SAT     █│     コピーを白抜き（tc）
│███████████████████████│
│░░░░░░░░░░░  [ QR バッジ ]│  CTA は帯外に badge
└───────────────────────┘
```

3. **構成要素と使用ヘルパ** ─ 背景 = `cover`、帯 = `panel(radius=0, alpha 220 前後)`、帯上コピー = `tc`、補足 = `tx(align="center")`、CTA = `badge`。
4. **背景プロンプトの方向** ─ 実写フォト系。帯が乗る中央帯域は情報量を抑えた素材にすると帯が浮かない。帯の色はブランドカラー・特色前提で色校正する。
5. **注意点** ─ 帯の高さは仕上がり短辺の 1/5〜1/4。帯 alpha を上げすぎると写真が死に、下げすぎると文字が読めない（220 前後が目安）。アクセントは帯 + CTA バッジの 2 箇所まで。
6. **コードスケッチ**（ポストカード 2122×1461）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import Image, ImageDraw
from card_compose import cover, panel, tc, tx, badge, load_font, save
W, H = 2122, 1461
ACC = (196, 60, 52, 255); PAPER = (252, 250, 246, 255)
base = cover(Image.open("bg/flyer.png"), W, H, ax=0.5, ay=0.40)
d = ImageDraw.Draw(base)
panel(base, (0, 560, W, 900), radius=0, fill=(196, 60, 52, 235))  # 横断色帯
tc(d, W/2, 620, "OPEN 7.20 SAT", load_font("gothic_w6", 120), PAPER)
tx(d, (W/2, 790), "リニューアルオープン記念フェア", load_font("gothic_w3", 46), PAPER,
   align="center", tracking=46*0.04)
badge(base, (W-620, 1200, W-140, 1320), radius=44, fill=ACC, text="詳しくは QR へ",
      font=load_font("gothic_w6", 40))
save(base, "~/Downloads/proj/p7-front.png")
```

---

## パターン8: ミニマル罫線

1. **適性** ─ 細罫（0.3〜0.5mm ≒ `mmpx` で 4〜7px）と小さめ組版・広い余白で構成。ラグジュアリー・ギャラリー・建築事務所。色を使わず「余白と線」で語るので 1C でも成立する。
2. **レイアウト図**

```
┌───────────────────────┐
│ ┌───────────────────┐ │  ← 細罫の内枠
│ │                   │ │     広い余白（端から 14mm 等）
│ │   GALLERY KURA     │ │
│ │   ───              │ │     小さめ組版・中央
│ │   現代美術 蔵       │ │
│ └───────────────────┘ │
└───────────────────────┘
```

3. **構成要素と使用ヘルパ** ─ 内枠罫 = `ImageDraw.rectangle(outline, width=mmpx(0.4))`、罫幅 = `mmpx`、名称 = `tc`、区切り = `ImageDraw.line`、補足 = `tx(align="center", tracking 広め)`。地は `new_canvas`。
4. **背景プロンプトの方向** ─ 無地または極薄の微テクスチャ系。写真は使わない。生成画像なしで PIL のベタ地 + 罫線だけで完結するのが基本形。
5. **注意点** ─ 罫は細く（0.3〜0.5mm）。太いと途端に安っぽくなる。余白を大きく取り（端から 12〜16mm）、文字は小さめ・字間広めで密度を落とす。ジャンプ率は上品側（1.5〜2:1）。1C の場合 QR・罫はスミ K 単色。
6. **コードスケッチ**（名刺横 1337×841）

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from PIL import ImageDraw
from card_compose import new_canvas, load_font, mmpx, tc, tx, save
W, H = 1337, 841
INK = (40, 38, 36, 255)
base = new_canvas(W, H, (250, 248, 244, 255))
d = ImageDraw.Draw(base)
rule = mmpx(0.4)   # 細罫 ≒ 6px
m = mmpx(14)       # 広い余白（端から 14mm ≒ 193px）
d.rectangle((m, m, W-m, H-m), outline=INK, width=rule)  # 内枠の細罫
tc(d, W/2, 300, "G A L L E R Y   K U R A", load_font("mincho", 40), INK)
d.line((W/2-120, 400, W/2+120, 400), fill=INK, width=rule)
tx(d, (W/2, 470), "現代美術 蔵", load_font("mincho", 30), INK, align="center", tracking=30*0.10)
tx(d, (W/2, 560), "OPEN  THU–SUN  12–19", load_font("gothic_w3", 24), INK,
   align="center", tracking=24*0.06)
save(base, "~/Downloads/proj/p8-front.png")
```

---

## パターン選択の早見

| ジャンル | 第一候補パターン |
|---|---|
| カフェ・雑貨・写真館（エモーショナル） | パターン1 写真主役・センター軸 |
| アパレル・美容・ホテル（高級・ファッション） | パターン2 全面写真・白抜きタイポ |
| 飲食店・ショップカード（情報多め） | パターン3 上下分割 |
| 士業・IT・コーポレート名刺 | パターン4 左寄せグリッド |
| イベント・引っ越し・告知カード | パターン5 タイポグラフィ主体 |
| 和菓子・書店・旅館・伝統工芸 | パターン6 縦書き和風 |
| フェア・オープン告知（フライヤー・DL） | パターン7 帯・バンド |
| ギャラリー・ラグジュアリー・1C 名刺 | パターン8 ミニマル罫線 |

複数案は「第一候補 + 毛色の違う 1〜2 型」を組み合わせる（例: 飲食店なら パターン3 + パターン1 + パターン7）。同ジャンルでも型を変えることで比較検討の幅が生まれる。

関連: `design-principles.md` / `bg-prompt-library.md` / `composition-recipe.md` / `card-specs.md`
