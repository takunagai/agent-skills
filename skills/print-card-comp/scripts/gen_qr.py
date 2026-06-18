#!/usr/bin/env python3
"""Generate a print-ready QR code (PNG + SVG) with segno.

印刷物カンプ用の QR コードを生成する。誤り訂正は印刷向けに既定 Q、
入稿用にベクター (SVG) も併せて出力する。

Usage:
    python3 gen_qr.py --url "https://example.com/" --out ~/Downloads/proj --name QR
    python3 gen_qr.py --url "https://example.com/" --out . --error h --scale 24

Dependencies: segno (see ../requirements.txt). pip が SSL エラーを出す環境では
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org segno
"""
import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a print-ready QR code (PNG + SVG).")
    parser.add_argument("--url", required=True, help="エンコードする URL / 文字列")
    parser.add_argument("--out", default=".", help="出力ディレクトリ（既定: カレント）")
    parser.add_argument("--name", default="QR", help="出力ファイル名（拡張子なし。既定: QR）")
    parser.add_argument(
        "--error",
        default="q",
        choices=["l", "m", "q", "h"],
        help="誤り訂正レベル l/m/q/h（既定: q。印刷でロゴ重ねや汚れに強くしたいなら h）",
    )
    parser.add_argument("--scale", type=int, default=20, help="1 モジュールのピクセル数（既定: 20）")
    parser.add_argument("--border", type=int, default=4, help="クワイエットゾーン（モジュール数。既定: 4）")
    parser.add_argument("--dark", default="#1a1a1a", help="暗モジュールの色（既定: #1a1a1a。真っ黒を避け柔らかく）")
    parser.add_argument("--light", default="white", help="明部の色（既定: white。透過は 'transparent'）")
    args = parser.parse_args()

    try:
        import segno
    except ImportError:
        print(
            "segno が見つかりません。`pip install -r requirements.txt` を実行してください。\n"
            "SSL エラー時: pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org segno",
            file=sys.stderr,
        )
        return 1

    out_dir = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out_dir, exist_ok=True)

    qr = segno.make(args.url, error=args.error)

    light = None if args.light == "transparent" else args.light
    png_path = os.path.join(out_dir, f"{args.name}.png")
    svg_path = os.path.join(out_dir, f"{args.name}.svg")

    qr.save(png_path, scale=args.scale, border=args.border, dark=args.dark, light=light)
    qr.save(svg_path, scale=args.scale, border=args.border, dark=args.dark, light=light)

    # version は記号バージョン (1-40)、誤り訂正は大文字記号で返る
    print(f"OK: {png_path}")
    print(f"OK: {svg_path}")
    print(f"  version={qr.version} error={qr.error} url={args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
