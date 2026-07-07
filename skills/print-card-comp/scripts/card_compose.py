#!/usr/bin/env python3
"""PIL composition helpers for print card comps.

印刷物カンプの PIL 合成で繰り返し使うヘルパ群。レイアウトは案件ごとに変わるため、
本モジュールは「共通の道具」だけを提供し、配置は呼び出し側で都度記述する。

import して使う:
    import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
    from card_compose import new_canvas, cover, tc, tx, tate, pc, panel, badge, \
        load_fonts, to_mono, duotone, guides, trim, sheet, mmpx, save

ヘルパ逆引き:
    寸法換算            : mmpx(mm)              mm -> px（既定 350dpi）
    テキスト(中央1行)  : tc(d, cx, y, ...)     既存互換
    テキスト(汎用)      : tx(d, xy, ..., align, tracking, line_height)  複数行・字間・左右揃え
    自動縮小フォント    : fit_font(text, role, size, max_w)             はみ出し対策
    縦書き              : tate(base, cx, top_y, text, font, fill)       1 列・長音符回転
    画像配置            : pc(base, im, cx, cy, w= / h=)
    角丸パネル          : panel(base, box, radius, fill)
    CTA バッジ          : badge(base, box, radius, fill, text, font)
    カバーフィット      : cover(img, w, h, ax, ay)
    モノクロ(1C)化      : to_mono(img)
    2 色刷り(2C)化      : duotone(img, ink, paper)
    飾り文字の透過パーツ化: ink_alpha(img, ink)     白地に生成した筆文字等を単色透過に
    検版ガイド          : guides(img)          仕上がり線=マゼンタ / 安全マージン=シアン
    仕上がりプレビュー  : trim(img)            塗り足しを落とす
    提案シート          : sheet([img, ...], labels=[...])
    保存(350dpi 付与)   : save(base, path)

直接実行するとデモカードを 3 枚書き出し、依存とフォント・新ヘルパの動作を確認できる:
    python3 card_compose.py --demo-out /tmp/pcc-demo

フォント: 既定は macOS のヒラギノ。別 OS では FONT_CANDIDATES を差し替えるか、
環境変数 PRINT_CARD_FONT_MINCHO / _GOTHIC_W3 / _GOTHIC_W6 / _MARU で上書きする。
見つからない場合、maru は角ゴシックへ、それ以外は PIL デフォルトへフォールバックする。
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- フォント候補（役割 -> 候補パスの優先リスト）-----------------------------
# 先頭から順に試し、最初に開けたものを使う。CJK グリフを持つフォントを
# macOS / Windows / Noto(Linux 等) 横断でカバーする。env (PRINT_CARD_FONT_*) を
# 指定すると、その役割で最優先に試す。
FONT_CANDIDATES = {
    "mincho": [
        "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",                  # macOS
        "C:/Windows/Fonts/yumin.ttf",                                   # Windows 游明朝
        "C:/Windows/Fonts/msmincho.ttc",                               # Windows MS 明朝
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",      # Noto Serif CJK
        "/usr/share/fonts/noto-cjk/NotoSerifCJKjp-Regular.otf",
    ],
    "gothic_w3": [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",              # macOS
        "C:/Windows/Fonts/YuGothR.ttc",                                # Windows 游ゴシック
        "C:/Windows/Fonts/meiryo.ttc",                                 # Windows メイリオ
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",       # Noto Sans CJK
        "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf",
    ],
    "gothic_w6": [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",              # macOS
        "C:/Windows/Fonts/YuGothB.ttc",                                # Windows 游ゴシック Bold
        "C:/Windows/Fonts/meiryob.ttc",                                # Windows メイリオ Bold
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",          # Noto Sans CJK Bold
        "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Bold.otf",
    ],
    "maru": [
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",              # macOS 丸ゴシック
        "C:/Windows/Fonts/HGRSMP.TTF",                                 # Windows HG丸ｺﾞｼｯｸM-PRO
    ],
}

# 丸ゴが無い環境では角ゴ W3 へ落として豆腐を避ける（フォールバック連結）。
FONT_CANDIDATES["maru"] = FONT_CANDIDATES["maru"] + FONT_CANDIDATES["gothic_w3"]

_ENV_OVERRIDE = {
    "mincho": "PRINT_CARD_FONT_MINCHO",
    "gothic_w3": "PRINT_CARD_FONT_GOTHIC_W3",
    "gothic_w6": "PRINT_CARD_FONT_GOTHIC_W6",
    "maru": "PRINT_CARD_FONT_MARU",
}

_warned = set()

# 縦書きで 90 度回転させる文字（横長グリフ: 長音符・ダッシュ・各種括弧）。
_TATE_ROTATE = set("ー－-–—…‥〜～｜ｰ「」『』（）()［］[]〈〉《》【】〔〕｛｝{}＜＞<>")
# 縦書きで文字セルの右上寄りに置く約物（句読点・コンマ）。
_TATE_PUNCT = set("、。，．")
# 縦書きで右上に軽くオフセットする小書き文字。
_TATE_SMALL = set("っゃゅょぁぃぅぇぉゎゕゖッャュョァィゥェォヮ")


def mmpx(mm: float, dpi: int = 350) -> int:
    """ミリメートルをピクセルへ換算（四捨五入）。3mm 塗り足し = 41px@350dpi。"""
    return int(round(mm / 25.4 * dpi))


def load_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    """役割名（mincho / gothic_w3 / gothic_w6 / maru）とサイズからフォントを得る。

    優先順: env (PRINT_CARD_FONT_*) -> OS 別の候補リスト。role にフォントの
    パスを直接渡してもよい（その場合はそのパスだけを試す）。どの CJK フォントも
    見つからない場合は PIL デフォルトに代替するが、日本語は豆腐（□）になるため
    強く警告する（本番は必ず CJK フォントを用意すること）。
    """
    candidates = []
    env_var = _ENV_OVERRIDE.get(role)
    if env_var and os.environ.get(env_var):
        candidates.append(os.environ[env_var])
    candidates.extend(FONT_CANDIDATES.get(role, [role]))

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    if role not in _warned:
        print(
            f"[card_compose] 警告: 役割 '{role}' の CJK フォントが見つかりません。"
            f"日本語は豆腐（□）になります。env {env_var} でパス指定を。",
            file=sys.stderr,
        )
        _warned.add(role)
    try:
        return ImageFont.load_default(size)
    except TypeError:  # 古い Pillow は size 引数なし
        return ImageFont.load_default()


def load_fonts(sizes: dict) -> dict:
    """役割ごとのサイズ指定をまとめてロードする。

    例: load_fonts({"copy": ("mincho", 64), "info": ("gothic_w3", 36)})
        -> {"copy": <font>, "info": <font>}
    """
    return {key: load_font(role, size) for key, (role, size) in sizes.items()}


def new_canvas(w: int, h: int, color=(252, 250, 246, 255)) -> Image.Image:
    """RGBA キャンバスを作る（既定は生成り地）。"""
    return Image.new("RGBA", (w, h), color)


def cover(img: Image.Image, w: int, h: int, ax: float = 0.5, ay: float = 0.5) -> Image.Image:
    """画像を w×h にカバーフィット（短辺基準で拡大しトリミング）。

    ax/ay は 0..1 のトリミング基準（0.5=中央、0=左/上寄せ）。
    """
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    resized = img.resize((int(iw * scale + 0.5), int(ih * scale + 0.5)), Image.LANCZOS)
    nw, nh = resized.size
    x = int((nw - w) * ax)
    y = int((nh - h) * ay)
    return resized.crop((x, y, x + w, y + h)).convert("RGBA")


def _line_width(text: str, font, tracking: float = 0.0) -> float:
    """1 行のテキスト幅（字間 tracking px を反映）。"""
    if tracking == 0:
        return font.getlength(text)
    if not text:
        return 0.0
    return sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)


def tc(draw: ImageDraw.ImageDraw, cx: float, y: float, text: str, font, fill) -> None:
    """中央揃えテキスト（cx を中心に描画）。既存レシピ互換。y は上端。"""
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def tx(draw: ImageDraw.ImageDraw, xy, text: str, font, fill,
       align: str = "left", tracking: float = 0.0, line_height: float = 1.6):
    """汎用テキスト描画。複数行（\\n 区切り）・字間 tracking（px）・左/中/右揃え。

    xy は align 基準点（left=左端 / center=中心 / right=右端。y は上端）。
    tracking != 0 のときは 1 文字ずつ送りながら描画する。
    描画した実寸 (w, h) を返す。
    """
    x, y = xy
    lines = text.split("\n")
    line_adv = int(font.size * line_height)
    max_w = 0.0
    cur_y = y
    for line in lines:
        lw = _line_width(line, font, tracking)
        max_w = max(max_w, lw)
        if align == "center":
            lx = x - lw / 2
        elif align == "right":
            lx = x - lw
        else:
            lx = x
        if tracking == 0:
            draw.text((lx, cur_y), line, font=font, fill=fill)
        else:
            cx2 = lx
            for ch in line:
                draw.text((cx2, cur_y), ch, font=font, fill=fill)
                cx2 += font.getlength(ch) + tracking
        cur_y += line_adv
    total_h = line_adv * (len(lines) - 1) + int(font.size)
    return int(max_w), int(total_h)


def fit_font(text: str, role: str, size: int, max_w: float,
             tracking: float = 0.0, min_size: int = None) -> ImageFont.FreeTypeFont:
    """max_w に収まるまでフォントサイズを段階的に下げてロードして返す。

    長い社名・URL のはみ出し対策。複数行なら最も広い行で判定する。
    min_size 既定は size の 6 割。
    """
    if min_size is None:
        min_size = max(8, int(size * 0.6))
    s = size
    while s > min_size:
        f = load_font(role, s)
        widest = max(_line_width(ln, f, tracking) for ln in text.split("\n"))
        if widest <= max_w:
            return f
        s -= 2
    return load_font(role, min_size)


def tate(base: Image.Image, cx: float, top_y: float, text: str, font, fill,
         tracking: float = 0.0) -> int:
    """縦書き（1 列）。1 文字ずつ縦に描画し、描画した高さ（px）を返す。

    ・長音符・ダッシュ・各種括弧は 90 度回転（横長グリフを縦向きに）
    ・句読点 、。 は文字セルの右上寄りにオフセット
    ・小書き文字（っゃゅょ 等）は右上へ軽くオフセット
    libraqm には依存しない。複数列は呼び出し側が cx をずらして列ごとに呼ぶ。
    """
    em = int(font.size)
    pad = int(em * 0.18)
    side = em + 2 * pad
    step = em + int(tracking)
    cur_y = top_y
    for ch in text:
        tile = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        gw = font.getlength(ch)
        # タイル内で水平中央・上寄せに描く
        td.text(((side - gw) / 2, pad), ch, font=font, fill=fill)
        if ch in _TATE_ROTATE:
            tile = tile.rotate(-90, expand=True)  # 時計回り 90 度
        xoff = yoff = 0
        if ch in _TATE_PUNCT:
            xoff = int(em * 0.18)
            yoff = -int(em * 0.32)
        elif ch in _TATE_SMALL:
            xoff = int(em * 0.06)
            yoff = -int(em * 0.06)
        base.alpha_composite(
            tile, (int(cx - side / 2 + xoff), int(cur_y + yoff))
        )
        cur_y += step
    return int(cur_y - top_y)


def pc(base: Image.Image, im: Image.Image, cx: float, cy: float,
       w: int = None, h: int = None) -> None:
    """画像を中心 (cx, cy) に alpha_composite で配置。

    w のみ指定=幅基準・h のみ指定=高さ基準・両方指定=そのサイズにリサイズ。
    """
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    if w and h:
        im = im.resize((int(w), int(h)), Image.LANCZOS)
    elif w:
        im = im.resize((int(w), int(im.height * w / im.width)), Image.LANCZOS)
    elif h:
        im = im.resize((int(im.width * h / im.height), int(h)), Image.LANCZOS)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def panel(base: Image.Image, box, radius: int, fill) -> None:
    """半透明の角丸パネル（白下地・情報パネル等）を base に重ねる。

    box = (x0, y0, x1, y1)、fill は RGBA タプル（例: (252,250,245,214)）。
    overlay は box サイズだけ確保し、オフセット合成する（フルキャンバスを作らない）。
    """
    x0, y0, x1, y1 = (int(v) for v in box)
    overlay = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        (0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=radius, fill=fill
    )
    base.alpha_composite(overlay, (x0, y0))


def badge(base: Image.Image, box, radius: int, fill, text: str, font, text_fill="white") -> None:
    """角丸の塗りバッジ + 中央テキスト（CTA「詳しくはこちら」等）。

    テキストは anchor="mm" で矩形中心に置く（ascender ずれを避ける）。
    """
    panel(base, box, radius, fill)
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(base)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font, fill=text_fill, anchor="mm")


def to_mono(img: Image.Image, autocontrast: bool = True) -> Image.Image:
    """モノクロ（1C）用グレースケール化。

    autocontrast で印刷時の眠さ（コントラスト不足）を防ぐ。RGBA で返す。
    元画像がアルファを持つ場合は保持する。
    """
    g = img.convert("L")
    if autocontrast:
        g = ImageOps.autocontrast(g, cutoff=1)
    out = g.convert("RGBA")
    if "A" in img.getbands():
        out.putalpha(img.getchannel("A"))
    return out


def duotone(img: Image.Image, ink, paper=(252, 250, 246), mid=None) -> Image.Image:
    """2 色刷り（2C）シミュレーション。

    グレースケール化して暗部→ink・明部→paper にマップする（ImageOps.colorize）。
    特色インクの色を正確に統一する要（背景はグレースケールで生成し、色付けは
    この関数で行うのが本スキルの 2C の正）。mid で中間調の色も指定できる。RGBA で返す。
    """
    g = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    black = tuple(ink[:3])
    white = tuple(paper[:3])
    if mid is None:
        out = ImageOps.colorize(g, black=black, white=white)
    else:
        out = ImageOps.colorize(g, black=black, white=white, mid=tuple(mid[:3]))
    out = out.convert("RGBA")
    if "A" in img.getbands():
        out.putalpha(img.getchannel("A"))
    return out


def ink_alpha(img: Image.Image, ink=(40, 38, 36)) -> Image.Image:
    """白地に描かれた文字・図版を透過パーツ化する（白→透明・墨→ink 色）。

    生成モデルで作った筆文字・カリグラフィ等の装飾文字パーツを、ロゴと同じように
    pc() で合成できる RGBA に変換する。輝度を alpha に写すため、かすれ・にじみは
    半透明のインクとして保たれる。全画素が ink 単色になるので、K 単色・特色単版と
    して扱え、生成文字の RGB 混色問題（4 色の乗った文字）を回避できる。
    """
    g = ImageOps.autocontrast(img.convert("L"), cutoff=1)  # わずかな地色被りを白へ寄せる
    alpha = ImageOps.invert(g)  # 白=0（透明）, 墨=255（不透明）
    out = Image.new("RGBA", img.size, tuple(ink[:3]) + (0,))
    out.putalpha(alpha)
    return out


def guides(img: Image.Image, dpi: int = 350, bleed_mm: float = 3, safe_mm: float = 5) -> Image.Image:
    """検版ガイド版を返す（コピー。原本は変更しない）。

    仕上がり線＝マゼンタ、安全マージン線＝シアンの矩形を重ねる。
    塗り足し込みサイズのカンプに対して使う（Phase 5.5 セルフレビュー用）。
    """
    out = img.convert("RGBA").copy()
    d = ImageDraw.Draw(out)
    w, h = out.size
    b = mmpx(bleed_mm, dpi)
    s = mmpx(safe_mm, dpi)
    d.rectangle((b, b, w - 1 - b, h - 1 - b), outline=(255, 0, 255, 255), width=2)
    d.rectangle((b + s, b + s, w - 1 - b - s, h - 1 - b - s), outline=(0, 180, 255, 255), width=2)
    return out


def trim(img: Image.Image, dpi: int = 350, bleed_mm: float = 3) -> Image.Image:
    """塗り足しを落とした仕上がりプレビューを返す（コピー）。"""
    b = mmpx(bleed_mm, dpi)
    w, h = img.size
    return img.convert("RGBA").crop((b, b, w - b, h - b))


def sheet(images, labels=None, pad: int = 48, bg=(232, 232, 232, 255)) -> Image.Image:
    """複数カンプを横並びにした提案シートを返す（同形状の案比較向け）。

    labels は各画像の下に小さく描画する。画像は原寸のまま上揃えで並べる。
    """
    imgs = [im.convert("RGBA") for im in images]
    label_h = 60 if labels else 0
    max_h = max(im.height for im in imgs)
    total_w = pad + sum(im.width + pad for im in imgs)
    total_h = pad + max_h + label_h + pad
    canvas = Image.new("RGBA", (total_w, total_h), bg)
    d = ImageDraw.Draw(canvas)
    font = load_font("gothic_w3", 32) if labels else None
    x = pad
    for i, im in enumerate(imgs):
        canvas.alpha_composite(im, (x, pad))
        if labels and i < len(labels):
            tc(d, x + im.width / 2, pad + max_h + 14, str(labels[i]), font, (60, 58, 56, 255))
        x += im.width + pad
    return canvas


def save(base: Image.Image, path: str, dpi=(350, 350)) -> str:
    """RGBA のまま PNG 保存（カンプは透過情報を保つ）。

    dpi を pHYs チャンクに書き込み、Photoshop 等で実寸として開けるようにする。
    パスを返す。
    """
    out = os.path.abspath(os.path.expanduser(path))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    base.save(out, dpi=dpi)
    return out


# --- デモ（依存・フォント・新ヘルパのスモークテスト兼サンプル）-----------------

def _linear_gray(w: int, h: int, top=60, bottom=235) -> Image.Image:
    """デモ用の縦グラデーション（L）。duotone の素地に使う。"""
    grad = Image.new("L", (1, 256))
    for y in range(256):
        grad.putpixel((0, y), int(top + (bottom - top) * y / 255))
    return grad.resize((w, h))


def _demo_meishi(out_dir: str) -> str:
    """横型名刺: 左寄せグリッド・字間見出し・複数行・自動縮小・丸ゴ。"""
    W, H = 1337, 841  # 名刺 91x55mm → 塗り足し込み 97x61mm @350dpi
    INK = (40, 38, 36, 255)
    ACCENT = (176, 88, 64, 255)  # テラコッタ
    base = new_canvas(W, H, (250, 247, 242, 255))
    d = ImageDraw.Draw(base)

    ml = mmpx(10)  # 左マージン
    axis = ml      # 揃え軸
    # 左の縦アクセントバー
    d.rectangle((ml - 24, mmpx(12), ml - 16, H - mmpx(12)), fill=ACCENT)

    fonts = load_fonts({
        "brand": ("gothic_w6", 78),
        "tag":   ("maru", 34),
        "name":  ("mincho", 64),
        "info":  ("gothic_w3", 30),
    })
    # 字間を効かせたブランド見出し
    tx(d, (axis, mmpx(13)), "NAGAI STUDIO", fonts["brand"], INK, align="left", tracking=6)
    tx(d, (axis, mmpx(13) + 96), "Web ・ AI ・ Creative", fonts["tag"], ACCENT, align="left", tracking=2)

    # 自動縮小で長い肩書き + 氏名（右ブロック）を軸内に収める
    name_font = fit_font("ウェブデザイナー / AI活用コンサルタント", "mincho", 64, W - axis - mmpx(10))
    tx(d, (axis, mmpx(30)), "永井 拓", name_font, INK, align="left")
    tx(d, (axis, mmpx(30) + int(name_font.size) + 12),
       "ウェブデザイナー / AI活用コンサルタント",
       load_font("gothic_w3", 30), (90, 86, 82, 255), align="left")

    # 複数行の連絡先（行間広め）
    tx(d, (axis, H - mmpx(20)),
       "info@example.com\nhttps://example.com/\nTEL 000-0000-0000",
       fonts["info"], INK, align="left", line_height=1.5)

    return save(base, os.path.join(out_dir, "demo-meishi.png"))


def _demo_tate(out_dir: str) -> str:
    """しおり型: 縦書きコピー（長音符回転・句読点位置を含む）。"""
    W, H = 909, 2563  # しおり 60x180mm → 塗り足し込み 66x186mm @350dpi
    INK = (38, 34, 30, 255)
    RED = (168, 42, 46, 255)
    base = new_canvas(W, H, (243, 238, 228, 255))
    d = ImageDraw.Draw(base)

    panel(base, (mmpx(8), mmpx(8), W - mmpx(8), H - mmpx(8)), radius=20, fill=(252, 250, 245, 90))

    copy_font = load_font("mincho", 88)
    sub_font = load_font("mincho", 52)
    # 長音符（ー）と句読点（、。）を含む縦書きコピー
    tate(base, W * 0.60, mmpx(16), "コーヒーと本のある、", copy_font, INK, tracking=10)
    tate(base, W * 0.32, mmpx(16), "しずかな休日を。", copy_font, INK, tracking=10)

    d.line((W * 0.5 - 4, H - mmpx(52), W * 0.5 - 4, H - mmpx(28)), fill=RED, width=5)
    tc(d, W * 0.5, H - mmpx(24), "BOOK & COFFEE", load_font("gothic_w6", 34), (80, 76, 72, 255))

    return save(base, os.path.join(out_dir, "demo-tate.png"))


def _demo_duotone(out_dir: str) -> str:
    """ポストカード横: グレースケール地に duotone + 検版ガイド。"""
    W, H = 2122, 1461  # ポストカード 148x100mm → 塗り足し込み 154x106mm @350dpi
    ground = _linear_gray(W, H).convert("RGBA")
    duo = duotone(ground, ink=(28, 52, 96), paper=(250, 248, 242))  # 濃紺 × 生成り
    d = ImageDraw.Draw(duo)

    panel(duo, (mmpx(14), mmpx(58), W - mmpx(14), mmpx(90)), radius=16, fill=(250, 248, 242, 205))
    tc(d, W / 2, mmpx(60), "2 色刷りのしらべ", load_font("mincho", 96), (28, 52, 96, 255))
    tc(d, W / 2, mmpx(80), "DUOTONE POSTCARD", load_font("gothic_w3", 40), (28, 52, 96, 255))

    with_guides = guides(duo)  # 検版線（仕上がり=マゼンタ / 安全=シアン）
    return save(with_guides, os.path.join(out_dir, "demo-duotone.png"))


def _demo(out_dir: str) -> int:
    """依存・フォント・新ヘルパの動作確認用デモを 3 枚書き出す。"""
    out_dir = os.path.abspath(os.path.expanduser(out_dir))
    os.makedirs(out_dir, exist_ok=True)
    paths = [
        _demo_meishi(out_dir),
        _demo_tate(out_dir),
        _demo_duotone(out_dir),
    ]
    for p in paths:
        with Image.open(p) as im:
            print(f"OK demo: {p} ({im.width}x{im.height})")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="card_compose helpers / demo")
    parser.add_argument("--demo-out", default="/tmp/pcc-demo",
                        help="デモ出力ディレクトリ（3 枚書き出す）")
    args = parser.parse_args()
    raise SystemExit(_demo(args.demo_out))
