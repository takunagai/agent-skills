#!/usr/bin/env python3
"""PIL composition helpers for print card comps.

印刷物カンプの PIL 合成で繰り返し使うヘルパ群。レイアウトは案件ごとに変わるため、
本モジュールは「共通の道具」だけを提供し、配置は呼び出し側で都度記述する。

import して使う:
    import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
    from card_compose import new_canvas, cover, tc, pc, panel, load_fonts

直接実行するとデモカードを書き出し、依存とフォントの動作を確認できる:
    python3 card_compose.py --demo-out /tmp/card_demo.png

フォント: 既定は macOS のヒラギノ。別 OS では FONTS を差し替えるか、
環境変数 PRINT_CARD_FONT_MINCHO / _GOTHIC_W3 / _GOTHIC_W6 で上書きする。
見つからない場合は PIL のデフォルトフォントにフォールバックする（警告を出す）。
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

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
}

_ENV_OVERRIDE = {
    "mincho": "PRINT_CARD_FONT_MINCHO",
    "gothic_w3": "PRINT_CARD_FONT_GOTHIC_W3",
    "gothic_w6": "PRINT_CARD_FONT_GOTHIC_W6",
}

_warned = set()


def load_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    """役割名（mincho / gothic_w3 / gothic_w6）とサイズからフォントを得る。

    優先順: env (PRINT_CARD_FONT_*) -> OS 別の候補リスト。role にフォントの
    パスを直接渡してもよい（その場合はそのパスだけを試す）。
    どの CJK フォントも見つからない場合は PIL デフォルトに代替するが、日本語は
    豆腐（□）になるため強く警告する（本番は必ず CJK フォントを用意すること）。
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


def tc(draw: ImageDraw.ImageDraw, cx: float, y: float, text: str, font, fill) -> None:
    """中央揃えテキスト（cx を中心に描画）。"""
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def pc(base: Image.Image, im: Image.Image, cx: float, cy: float, w: int = None) -> None:
    """画像を中心 (cx, cy) に alpha_composite で配置。w 指定で幅リサイズ。"""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    if w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
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
    """角丸の塗りバッジ + 中央テキスト（CTA「詳しくはこちら」等）。"""
    panel(base, box, radius, fill)
    x0, y0, x1, y1 = box
    bb = font.getbbox(text) if hasattr(font, "getbbox") else None
    th = (bb[3] - bb[1]) if bb else font.size
    tc(ImageDraw.Draw(base), (x0 + x1) / 2, (y0 + y1) / 2 - th / 2, text, font, text_fill)


def save(base: Image.Image, path: str) -> str:
    """RGBA のまま PNG 保存（カンプは透過情報を保つ）。パスを返す。"""
    out = os.path.abspath(os.path.expanduser(path))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    base.save(out)
    return out


def _demo(out_path: str) -> int:
    """依存とフォントの動作確認用デモ。しおり型ミニカードを 1 枚書き出す。"""
    W, H = 827, 2480  # しおり型 60x180mm 塗り足し込み @350dpi
    fonts = load_fonts({"copy": ("mincho", 72), "info": ("gothic_w3", 40), "name": ("gothic_w6", 44)})

    # 背景（デモなのでグラデ風の単色塗り）
    base = new_canvas(W, H, (236, 232, 224, 255))
    d = ImageDraw.Draw(base)

    # 白下地パネル + コピー
    panel(base, (80, 1900, W - 80, 2150), radius=24, fill=(252, 250, 245, 200))
    tc(d, W / 2, 1950, "足もとから、しずかに。", fonts["copy"], (40, 38, 36, 255))

    # 赤バッジ
    badge(base, (W / 2 - 200, 2250, W / 2 + 200, 2360), radius=40,
          fill=(196, 24, 36, 255), text="詳しくはこちら", font=fonts["info"])

    # 会社名
    tc(d, W / 2, 1820, "DEMO PRINT CARD", fonts["name"], (60, 58, 56, 255))

    path = save(base, out_path)
    print(f"OK demo: {path} ({W}x{H})")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="card_compose helpers / demo")
    parser.add_argument("--demo-out", default="/tmp/card_compose_demo.png", help="デモ出力先")
    args = parser.parse_args()
    raise SystemExit(_demo(args.demo_out))
