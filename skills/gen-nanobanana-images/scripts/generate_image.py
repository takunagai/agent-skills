#!/usr/bin/env python3
"""Nano Banana Image Generation CLI.

Generate and edit images using Google Gemini image models
(Nano Banana: Flash, Flash2 (Nano Banana 2), Pro).

Supports text-to-image generation, image editing, and multi-turn refinement.
"""

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# モデル定義 — ModelSpec dataclass で一元管理
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelSpec:
    id: str
    thinking_levels: tuple
    aspect_ratios: tuple
    image_sizes: tuple          # 空 = imageSize 指定不可
    max_input_images: int
    supports_multi_turn: bool
    supports_google_search: bool
    supports_image_search: bool


ASPECT_RATIOS_BASE = (
    "1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
)
ASPECT_RATIOS_EXTENDED = ("1:4", "4:1", "1:8", "8:1")  # flash2 のみ

# モデルは 2026-05-28 GA 版の 3 構成（flash2 / pro / lite）。
# 旧 flash (2.5 系) と preview ID は廃止済み（2026-06-25 shutdown）のため使用しない。
# 廃止経緯の詳細は references/api-reference.md「旧モデル（廃止）」を参照。
MODEL_SPECS: dict = {
    "flash2": ModelSpec(
        id="gemini-3.1-flash-image",
        thinking_levels=("minimal", "high"),
        aspect_ratios=ASPECT_RATIOS_BASE + ASPECT_RATIOS_EXTENDED,
        image_sizes=("512px", "1K", "2K", "4K"),
        max_input_images=14,
        supports_multi_turn=True,
        supports_google_search=True,
        supports_image_search=True,
    ),
    "pro": ModelSpec(
        id="gemini-3-pro-image",
        thinking_levels=("low", "high"),
        aspect_ratios=ASPECT_RATIOS_BASE,
        image_sizes=("1K", "2K", "4K"),
        max_input_images=14,
        supports_multi_turn=True,
        supports_google_search=True,
        supports_image_search=False,
    ),
    "lite": ModelSpec(
        id="gemini-3.1-flash-lite-image",
        thinking_levels=("minimal", "high"),
        aspect_ratios=ASPECT_RATIOS_BASE,
        image_sizes=("1K",),
        max_input_images=14,
        supports_multi_turn=True,
        supports_google_search=False,
        supports_image_search=False,
    ),
}

# ヘルプ表示・argparse 用の集約値
ALL_ASPECT_RATIOS = ASPECT_RATIOS_BASE + ASPECT_RATIOS_EXTENDED
ALL_IMAGE_SIZES = ("512px", "1K", "2K", "4K")
MODEL_CHOICES = list(MODEL_SPECS.keys())

# Negative Constraints は既定 OFF（空文字）。付加したい場合は config.json の
# "negative_constraints" キーに文字列を設定する（opt-in）。以下は設定例:
#   "negative_constraints": "Avoid: low quality, blurry, noisy, deformed hands,
#                            watermark, oversaturated colors."

MAX_FILE_SIZE_MB = 7
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2

DEFAULT_NUM_IMAGES = 1
MAX_NUM_IMAGES = 10  # Google Cloud ドキュメントの記載上限に合わせる

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}

MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

# ユーザーが config.json で変更可能なデフォルト値
# negative_constraints は既定 OFF（空文字）。config.json で opt-in する。
CONFIGURABLE_DEFAULTS = {
    "model": "flash2",
    "aspect_ratio": "1:1",
    "output_dir": ".",
    "num_images": DEFAULT_NUM_IMAGES,
    "timeout": 120,
    "thinking_level": None,
    "negative_constraints": "",
}


def load_config():
    """スキルディレクトリの config.json を読み込む。存在しなければ空辞書を返す。"""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir.parent / "config.json"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        valid_keys = set(CONFIGURABLE_DEFAULTS.keys())
        unknown = set(config.keys()) - valid_keys
        if unknown:
            print(
                f"Warning: config.json に不明なキーがあります（無視されます）: {', '.join(sorted(unknown))}",
                file=sys.stderr,
            )
        return {k: v for k, v in config.items() if k in valid_keys}
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: config.json の読み込みに失敗しました: {e}", file=sys.stderr)
        return {}


def parse_args(config=None):
    """CLI 引数を解析する。config で指定された値が argparse のデフォルトになる。"""
    if config is None:
        config = {}
    defaults = {**CONFIGURABLE_DEFAULTS, **config}

    parser = argparse.ArgumentParser(
        description="Generate and edit images using Nano Banana (Gemini) models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # テキストから画像生成（Flash2 — デフォルト）
  %(prog)s -p "A red apple on white background"

  # Flash2 で 4K・超縦長生成
  %(prog)s -p "A tall lighthouse on a cliff" -a 1:8 -s 4K

  # Flash2 で Image Search 連携
  %(prog)s -p "Latest iPhone model photo" --image-search

  # Flash2 でマルチターンチャット
  %(prog)s -p "A cozy cabin in the woods" -c

  # Pro モデルで高解像度生成
  %(prog)s -p "A futuristic cityscape at sunset" -m pro -s 4K -a 16:9

  # 既存画像の編集
  %(prog)s -p "Make the sky sunset orange" -i photo.jpg

  # マルチターンチャット（継続）
  %(prog)s -p "Add snow on the roof" --session session.json

  # Google Search 連携
  %(prog)s -p "Accurate diagram of human heart anatomy" -g

  # Image Search + Google Search 同時使用（flash2 のみ）
  %(prog)s -p "Photo of the latest Tesla model" -m flash2 --image-search -g

  # スタイルリファレンスで新規生成
  %(prog)s -p "A mountain landscape" -r style.png

  # 複数画像の編集
  %(prog)s -p "Blend into double exposure" -i portrait.jpg landscape.jpg

  # 同一プロンプトで3枚のバリエーションを生成
  %(prog)s -p "A red apple on white background" -N 3

  # Lite モデルで最速・最安のドラフト生成（1K 専用）
  %(prog)s -p "Quick draft sketch" -m lite
""",
    )

    parser.add_argument(
        "-p", "--prompt", default=None, help="テキストプロンプト（--list-models 以外では必須）"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="API に問い合わせて利用可能な画像生成モデル一覧を表示",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=defaults["model"],
        choices=MODEL_CHOICES,
        help=(
            f"モデル選択: flash2 (推奨・万能), pro (最高品質・テキスト精度最高), "
            f"lite (最速最安・1K専用・ドラフト/大量生成向け) (default: {defaults['model']}). "
            f"旧 flash (2.5) は廃止。ドラフト用途は lite を使用"
        ),
    )
    parser.add_argument(
        "-i", "--input-image", nargs="+", default=None,
        help="編集用入力画像パス（複数指定可: -i img1.jpg img2.jpg）",
    )
    parser.add_argument(
        "-r", "--reference", nargs="+", default=None,
        help="スタイル/構図リファレンス画像パス（複数指定可: -r style1.png style2.png）",
    )
    parser.add_argument(
        "-o", "--output-dir", default=defaults["output_dir"],
        help=f"出力ディレクトリ (default: {defaults['output_dir']})",
    )
    parser.add_argument(
        "-n", "--output-name", default=None, help="出力ファイル名（拡張子なし）"
    )
    parser.add_argument(
        "-a",
        "--aspect-ratio",
        default=defaults["aspect_ratio"],
        help=f"アスペクト比 (default: {defaults['aspect_ratio']}, choices: {', '.join(ALL_ASPECT_RATIOS)})",
    )
    parser.add_argument(
        "-s",
        "--image-size",
        default=None,
        choices=list(ALL_IMAGE_SIZES),
        help="解像度 (flash2: 512px/1K/2K/4K, pro: 1K/2K/4K, lite: 1K のみ)",
    )
    parser.add_argument(
        "-t",
        "--thinking-level",
        default=defaults["thinking_level"],
        help="思考レベル (flash2: minimal/high, pro: low/high, lite: minimal/high)",
    )
    parser.add_argument(
        "-g",
        "--google-search",
        action="store_true",
        help="Google Search 連携を有効化（flash2/pro）",
    )
    parser.add_argument(
        "--image-search",
        action="store_true",
        help="Image Search 連携を有効化（flash2 のみ。-g と併用可）",
    )
    parser.add_argument(
        "-c", "--chat", action="store_true", help="マルチターンチャットモード（新規セッション開始、flash2/pro）"
    )
    parser.add_argument(
        "--session", default=None, help="セッション JSON パス（既存セッションを継続）"
    )
    parser.add_argument(
        "-N", "--num-images", type=int, default=defaults["num_images"],
        help=f"生成する画像の枚数 (default: {defaults['num_images']}, max: {MAX_NUM_IMAGES}). 各枚ごとに個別の API 呼び出しを行います",
    )
    parser.add_argument(
        "--timeout", type=int, default=defaults["timeout"],
        help=f"タイムアウト秒数 (default: {defaults['timeout']})",
    )

    args = parser.parse_args()
    # negative_constraints は CLI 引数ではなく config.json からのみ変更可能
    args.negative_constraints = defaults["negative_constraints"]
    return args


def _validate_image_file(path_str):
    """単一画像ファイルのバリデーション。エラー時はメッセージ文字列を返す。正常は None。"""
    p = Path(path_str)
    if not p.exists():
        return f"画像ファイルが見つかりません: {path_str}"
    ext = p.suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        return f"サポートされていない画像形式です: {path_str} (対応: {supported})"
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"画像ファイルが大きすぎます: {path_str} ({size_mb:.1f}MB, 上限: {MAX_FILE_SIZE_MB}MB)"
    return None


def _unique_output_path(out_path):
    """出力先に同名ファイルがあれば連番を振って回避する。

    Returns:
        tuple: (Path, renamed: bool) — renamed が True なら連番回避したことを示す。
    """
    p = Path(out_path)
    if not p.exists():
        return p, False
    stem, suffix, parent = p.stem, p.suffix, p.parent
    i = 2
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate, True
        i += 1


def _augment_prompt(prompt, has_input, has_reference, input_count=0, ref_count=0):
    """入力/リファレンス画像の存在に応じてプロンプトに注釈を付加する。"""
    if has_input and has_reference:
        prefix = (
            f"Edit the {input_count} input image(s). "
            f"Use the {ref_count} reference image(s) for style and composition guidance. "
        )
        return prefix + prompt
    if has_reference and not has_input:
        prefix = (
            f"Use the {ref_count} reference image(s) for style and composition guidance. "
        )
        return prefix + prompt
    # -i のみ or 画像なし: 注釈なし（既存動作を維持）
    return prompt


def validate_args(args):
    """引数のバリデーション。エラー時は sys.exit(1)。"""
    # API キー確認
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required.",
            file=sys.stderr,
        )
        print(
            "  Get your key at: https://aistudio.google.com/apikey", file=sys.stderr
        )
        sys.exit(1)

    spec = MODEL_SPECS[args.model]

    # アスペクト比
    if args.aspect_ratio not in spec.aspect_ratios:
        print(
            f"Error: Invalid aspect ratio '{args.aspect_ratio}' for {args.model}. "
            f"Valid: {', '.join(spec.aspect_ratios)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 画像サイズ
    if args.image_size:
        if not spec.image_sizes:
            print(
                f"Error: --image-size is not available for the {args.model} model.",
                file=sys.stderr,
            )
            sys.exit(1)
        if args.image_size not in spec.image_sizes:
            print(
                f"Error: Invalid image size '{args.image_size}' for {args.model}. "
                f"Valid: {', '.join(spec.image_sizes)}",
                file=sys.stderr,
            )
            sys.exit(1)

    # Google Search
    if args.google_search and not spec.supports_google_search:
        print(
            f"Error: --google-search is not available for the {args.model} model.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Image Search
    if args.image_search and not spec.supports_image_search:
        print(
            f"Error: --image-search is not available for the {args.model} model. "
            f"Image Search is only supported by flash2.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Image Search は typed SearchTypes を持つ SDK が必須（v1.65.0+、推奨 v2.10.0+）
    if args.image_search:
        from google.genai import types
        if not hasattr(types, "SearchTypes"):
            print(
                "Error: --image-search には新しい google-genai SDK が必要です"
                "（types.SearchTypes 未対応）。\n"
                "  次を実行してください: pip install -U 'google-genai>=2.10.0'",
                file=sys.stderr,
            )
            sys.exit(1)

    # 思考レベルのバリデーション
    if args.thinking_level:
        if args.thinking_level not in spec.thinking_levels:
            print(
                f"Error: Invalid thinking level '{args.thinking_level}' for {args.model}. "
                f"Valid: {', '.join(spec.thinking_levels)}",
                file=sys.stderr,
            )
            sys.exit(1)

    # 生成枚数のバリデーション
    if args.num_images < 1:
        print("Error: --num-images は1以上を指定してください。", file=sys.stderr)
        sys.exit(1)
    if args.num_images > MAX_NUM_IMAGES:
        print(
            f"Error: --num-images の上限は {MAX_NUM_IMAGES} 枚です（指定: {args.num_images}枚）。",
            file=sys.stderr,
        )
        sys.exit(1)

    # マルチターンでは -N 無効（1回のターンで1枚が原則）
    if (args.chat or args.session) and args.num_images > 1:
        print(
            "Error: マルチターンモード (--chat/--session) では --num-images は1のみ指定可能です。",
            file=sys.stderr,
        )
        sys.exit(1)

    # 入力画像・リファレンス画像のバリデーション
    all_images = []
    if args.input_image:
        for img in args.input_image:
            err = _validate_image_file(img)
            if err:
                print(f"Error: {err}", file=sys.stderr)
                sys.exit(1)
            all_images.append(img)
    if args.reference:
        for img in args.reference:
            err = _validate_image_file(img)
            if err:
                print(f"Error: {err}", file=sys.stderr)
                sys.exit(1)
            all_images.append(img)

    if all_images:
        total_count = len(all_images)
        if total_count > spec.max_input_images:
            print(
                f"Error: {args.model} モデルの画像上限は{spec.max_input_images}枚です"
                f"（指定: {total_count}枚）。",
                file=sys.stderr,
            )
            sys.exit(1)
        # 合計サイズチェック
        total_size_mb = sum(
            Path(img).stat().st_size / (1024 * 1024) for img in all_images
        )
        if total_size_mb > MAX_FILE_SIZE_MB:
            print(
                f"Error: 画像の合計サイズが上限を超えています: {total_size_mb:.1f}MB（上限: {MAX_FILE_SIZE_MB}MB）",
                file=sys.stderr,
            )
            sys.exit(1)

    # セッションファイルの存在確認
    if args.session and not Path(args.session).exists():
        print(f"Error: Session file not found: {args.session}", file=sys.stderr)
        sys.exit(1)

    # chat と session は排他
    if args.chat and args.session:
        print(
            "Error: --chat and --session are mutually exclusive. "
            "Use --chat for new sessions, --session to continue.",
            file=sys.stderr,
        )
        sys.exit(1)

    # マルチターン対応チェック
    if (args.chat or args.session) and not spec.supports_multi_turn:
        print(
            f"Error: Multi-turn chat (--chat/--session) is not available for the {args.model} model.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 出力ディレクトリの確認
    out_dir = Path(args.output_dir)
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {out_dir}")

    # 4K 時のタイムアウト自動調整
    if args.image_size == "4K" and args.timeout < 420:
        args.timeout = 420
        print("Note: Timeout auto-adjusted to 420s for 4K generation.")

    return api_key


def build_config(args):
    """GenerateContentConfig を構築する。"""
    from google.genai import types

    # ImageConfig のパラメータ（キャメルケース）
    image_config_params = {"aspectRatio": args.aspect_ratio}
    if args.image_size:
        image_config_params["imageSize"] = args.image_size

    config_params = {
        "responseModalities": ["IMAGE", "TEXT"],
        "imageConfig": types.ImageConfig(**image_config_params),
    }

    # 思考レベル
    if args.thinking_level:
        config_params["thinkingConfig"] = types.ThinkingConfig(
            thinkingLevel=args.thinking_level.upper(),
        )

    # Google Search / Image Search 連携
    if args.google_search or args.image_search:
        if args.image_search:
            # Image Search (± Web Search) — flash2 専用。
            # typed SearchTypes は SDK v1.65.0+（推奨 v2.10.0+）が必須。
            # 対応可否は validate_args() で事前チェック済み。
            search_types_params = {}
            if args.google_search:
                search_types_params["webSearch"] = types.WebSearch()
            search_types_params["imageSearch"] = types.ImageSearch()
            config_params["tools"] = [
                types.Tool(googleSearch=types.GoogleSearch(
                    searchTypes=types.SearchTypes(**search_types_params)
                ))
            ]
        else:
            # Web Search のみ（既存動作を維持）
            config_params["tools"] = [types.Tool(googleSearch=types.GoogleSearch())]

    return types.GenerateContentConfig(**config_params)


def build_contents(args, api_key):
    """contents 配列を構築する（テキスト/画像入力/マルチターン履歴）。"""
    from google.genai import types

    has_input = bool(args.input_image)
    has_reference = bool(args.reference)
    input_count = len(args.input_image) if args.input_image else 0
    ref_count = len(args.reference) if args.reference else 0

    # プロンプト注釈 + Negative Constraints
    augmented = _augment_prompt(
        args.prompt, has_input, has_reference, input_count, ref_count
    )
    if args.negative_constraints:
        full_prompt = f"{augmented}\n\n{args.negative_constraints}"
    else:
        full_prompt = augmented

    parts = []

    # 入力画像（編集対象）
    if args.input_image:
        for img_str in args.input_image:
            img_path = Path(img_str)
            img_bytes = img_path.read_bytes()
            mime_type = MIME_MAP.get(img_path.suffix.lower(), "image/png")
            parts.append(
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
            )

    # リファレンス画像（スタイル参照）
    if args.reference:
        for ref_str in args.reference:
            ref_path = Path(ref_str)
            ref_bytes = ref_path.read_bytes()
            mime_type = MIME_MAP.get(ref_path.suffix.lower(), "image/png")
            parts.append(
                types.Part.from_bytes(data=ref_bytes, mime_type=mime_type)
            )

    parts.append(types.Part.from_text(text=full_prompt))

    return [types.Content(role="user", parts=parts)]


def load_session(session_path):
    """セッション JSON を読み込む。"""
    with open(session_path, "r") as f:
        return json.load(f)


def save_session(session_path, session_data):
    """セッション JSON を保存する。"""
    with open(session_path, "w") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)


def rebuild_history_contents(session_data, new_prompt, negative_constraints=""):
    """セッション履歴から contents を再構築する。"""
    from google.genai import types

    contents = []

    for entry in session_data.get("history", []):
        parts = []
        for part_data in entry.get("parts", []):
            if "text" in part_data:
                parts.append(types.Part.from_text(text=part_data["text"]))
            elif "thought_signature_b64" in part_data:
                # base64 文字列で保存された thought_signature を bytes に戻して再構築
                sig_bytes = base64.b64decode(part_data["thought_signature_b64"])
                parts.append(types.Part(thoughtSignature=sig_bytes))
            elif "image_file" in part_data:
                # 保存済み画像を読み込んで Part に変換
                img_path = Path(part_data["image_file"])
                if img_path.exists():
                    img_bytes = img_path.read_bytes()
                    mime_type = MIME_MAP.get(img_path.suffix.lower(), "image/png")
                    parts.append(
                        types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
                    )
                else:
                    print(
                        f"Warning: Session image not found: {img_path}",
                        file=sys.stderr,
                    )
            elif "thought" in part_data:
                # thought テキストは再送信不要（スキップ）
                pass

        if parts:
            contents.append(types.Content(role=entry["role"], parts=parts))

    # 新しいユーザープロンプトを追加
    if negative_constraints:
        full_prompt = f"{new_prompt}\n\n{negative_constraints}"
    else:
        full_prompt = new_prompt
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=full_prompt)],
        )
    )

    return contents


def extract_and_save_images(response, output_dir, output_name, turn_num=0, call_index=0):
    """レスポンスから画像を抽出して保存する。

    Returns:
        tuple: (saved_paths, thought_signatures, text_parts)
    """
    saved_paths = []
    thought_signatures = []
    text_parts = []
    img_count = 0

    if not response.candidates or not response.candidates[0].content.parts:
        print(
            "Warning: No content in response. The image may have been filtered.",
            file=sys.stderr,
        )
        return saved_paths, thought_signatures, text_parts

    for part in response.candidates[0].content.parts:
        # thought テキスト（デバッグ用、保存はしない）
        if hasattr(part, "thought") and part.thought:
            continue

        # thought_signature
        if hasattr(part, "thought_signature") and part.thought_signature:
            thought_signatures.append(part.thought_signature)

        # テキスト部分
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

        # 画像部分
        if hasattr(part, "inline_data") and part.inline_data:
            img_count += 1
            variant_suffix = f"_v{call_index + 1}" if call_index > 0 else ""
            if output_name:
                base = f"{output_name}{variant_suffix}"
                if img_count == 1:
                    filename = f"{base}.png"
                else:
                    filename = f"{base}_{img_count}.png"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if turn_num > 0:
                    filename = f"nanobanana_{timestamp}_t{turn_num}{variant_suffix}_{img_count}.png"
                else:
                    filename = f"nanobanana_{timestamp}{variant_suffix}_{img_count}.png"

            out_path = Path(output_dir) / filename
            # 既存ファイルの黙殺上書きを防ぐ（連番で回避）
            out_path, renamed = _unique_output_path(out_path)
            if renamed:
                print(f"Note: 同名ファイルが存在するため {out_path.name} に保存します（上書き回避）。")

            # PIL で画像を保存
            try:
                image = part.as_image()
                image.save(str(out_path))
                saved_paths.append(str(out_path))
                print(f"Saved: {out_path}")
            except Exception as e:
                # PIL が使えない場合は直接バイトを保存
                try:
                    img_bytes = part.inline_data.data
                    if isinstance(img_bytes, str):
                        img_bytes = base64.b64decode(img_bytes)
                    out_path.write_bytes(img_bytes)
                    saved_paths.append(str(out_path))
                    print(f"Saved (raw): {out_path}")
                except Exception as e2:
                    print(f"Error saving image: {e2}", file=sys.stderr)

    if img_count == 0:
        print(
            "Warning: No images in response. The prompt may have been filtered "
            "by safety settings, or the model returned text only.",
            file=sys.stderr,
        )

    return saved_paths, thought_signatures, text_parts


def make_client(api_key, timeout):
    """タイムアウト（秒）を反映した Gemini クライアントを生成する。

    SDK の HttpOptions.timeout はミリ秒単位のため *1000 して渡す。
    これにより --timeout / 4K 時の自動 420s が実際にリクエストへ伝播する。
    """
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout * 1000),
    )


def api_call_with_retry(client, model_id, contents, config):
    """API 呼び出しをリトライ付きで実行する。

    タイムアウトは client 生成時（make_client）に設定済み。
    """
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
            return response
        except Exception as e:
            last_error = e
            error_str = str(e)

            # リトライ不可能なエラー
            if "400" in error_str or "403" in error_str or "404" in error_str:
                raise

            # リトライ可能なエラー (429, 503, etc.)
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2**attempt)
                print(
                    f"Retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES}): {e}",
                    file=sys.stderr,
                )
                time.sleep(delay)

    raise last_error


def list_available_models(api_key):
    """API に問い合わせて利用可能な画像生成モデル一覧を表示する。"""
    from google import genai

    client = genai.Client(api_key=api_key)
    print("Querying available image generation models...\n")

    image_models = []
    for m in client.models.list():
        name = m.name if hasattr(m, "name") else str(m)
        # "image" を含む Gemini モデルを抽出
        if "image" in name.lower() and "gemini" in name.lower():
            # models/ プレフィックスを除去
            model_id = name.replace("models/", "")
            image_models.append(model_id)

    if image_models:
        print("Available image generation models:")
        for model_id in sorted(image_models):
            # 現在の設定との対応を表示
            alias = None
            for key, spec in MODEL_SPECS.items():
                if spec.id == model_id:
                    alias = key
            if alias:
                print(f"  {model_id}  (--model {alias})")
            else:
                print(f"  {model_id}")

        # 設定済みモデルが一覧にない場合は警告
        for alias, spec in MODEL_SPECS.items():
            if spec.id not in image_models:
                print(
                    f"\nWarning: Configured '{alias}' model ({spec.id}) "
                    f"is NOT in the available models list."
                )
    else:
        print("No image generation models found.")

    print(f"\nCurrently configured:")
    for alias, spec in MODEL_SPECS.items():
        print(f"  {alias}: {spec.id}")


def generate_single_shot(args, api_key):
    """単発生成（text-to-image / 画像編集）。N 枚指定時はループで順次生成。"""
    client = make_client(api_key, args.timeout)
    model_id = MODEL_SPECS[args.model].id

    config = build_config(args)
    contents = build_contents(args, api_key)

    all_saved_paths = []

    for i in range(args.num_images):
        if args.num_images > 1:
            print(f"\nGenerating image {i + 1}/{args.num_images} with {args.model} model ({model_id})...")
        else:
            print(f"Generating with {args.model} model ({model_id})...")

        try:
            response = api_call_with_retry(client, model_id, contents, config)
            saved_paths, thought_sigs, text_parts = extract_and_save_images(
                response, args.output_dir, args.output_name, call_index=i
            )
            all_saved_paths.extend(saved_paths)
            for text in text_parts:
                print(f"\nModel response: {text}")
        except Exception as e:
            if args.num_images > 1:
                print(f"Warning: Image {i + 1}/{args.num_images} failed: {e}", file=sys.stderr)
                continue
            else:
                raise

    if not all_saved_paths:
        sys.exit(2)

    if args.num_images > 1:
        print(f"\nTotal: {len(all_saved_paths)} images generated.")

    return all_saved_paths


def generate_chat(args, api_key):
    """マルチターンチャット（セッションファイル管理）。"""
    client = make_client(api_key, args.timeout)
    model_id = MODEL_SPECS[args.model].id
    config = build_config(args)

    session_data = None
    turn_num = 1

    if args.session:
        # 既存セッションを継続
        session_data = load_session(args.session)
        turn_num = len(
            [e for e in session_data.get("history", []) if e["role"] == "user"]
        ) + 1
        contents = rebuild_history_contents(session_data, args.prompt, args.negative_constraints)
        session_path = args.session
        print(f"Continuing session (turn {turn_num}): {args.session}")
    else:
        # 新規セッション
        contents = build_contents(args, api_key)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_path = str(
            Path(args.output_dir) / f"session_{timestamp}.json"
        )
        session_data = {
            "model": model_id,
            "created": datetime.now(timezone.utc).isoformat(),
            "config": {
                "aspect_ratio": args.aspect_ratio,
            },
            "history": [],
        }
        if args.image_size:
            session_data["config"]["image_size"] = args.image_size
        print(f"Starting new chat session: {session_path}")

    print(f"Generating with {args.model} model ({model_id})...")
    response = api_call_with_retry(client, model_id, contents, config)

    saved_paths, thought_sigs, text_parts = extract_and_save_images(
        response, args.output_dir, args.output_name, turn_num=turn_num
    )

    # テキスト応答があれば表示
    for text in text_parts:
        print(f"\nModel response: {text}")

    if not saved_paths and not text_parts:
        print("Error: No output from model.", file=sys.stderr)
        sys.exit(2)

    # セッション履歴を更新
    # ユーザーの入力を記録
    has_input = bool(args.input_image)
    has_reference = bool(args.reference)
    input_count = len(args.input_image) if args.input_image else 0
    ref_count = len(args.reference) if args.reference else 0
    augmented = _augment_prompt(
        args.prompt, has_input, has_reference, input_count, ref_count
    )
    if args.negative_constraints:
        user_parts = [{"text": f"{augmented}\n\n{args.negative_constraints}"}]
    else:
        user_parts = [{"text": augmented}]
    if not args.session:
        # 新規セッションの初回のみ画像パーツを記録
        if args.input_image:
            for img in args.input_image:
                user_parts.insert(
                    len(user_parts) - 1,
                    {"image_file": str(Path(img).resolve()), "image_role": "input"},
                )
        if args.reference:
            for ref in args.reference:
                user_parts.insert(
                    len(user_parts) - 1,
                    {"image_file": str(Path(ref).resolve()), "image_role": "reference"},
                )
    session_data["history"].append({"role": "user", "parts": user_parts})

    # モデルの応答を記録
    model_parts = []
    for sig in thought_sigs:
        # thought_signature は bytes。JSON 直列化のため base64 文字列で保存する。
        model_parts.append(
            {"thought_signature_b64": base64.b64encode(sig).decode("ascii")}
        )
    for path in saved_paths:
        model_parts.append({"image_file": str(Path(path).resolve())})
    for text in text_parts:
        model_parts.append({"text": text})
    session_data["history"].append({"role": "model", "parts": model_parts})

    # セッション保存
    save_session(session_path, session_data)
    print(f"\nSession saved: {session_path}")
    print(f"To continue: generate_image.py -p '<next prompt>' -m {args.model} --session {session_path}")

    return saved_paths


def main():
    """エントリポイント。"""
    config = load_config()
    args = parse_args(config)

    # Lazy import チェック
    try:
        from google import genai  # noqa: F401
    except ImportError:
        print(
            "Error: google-genai package is not installed.", file=sys.stderr
        )
        print("  Install with: pip install google-genai Pillow", file=sys.stderr)
        sys.exit(1)

    # --list-models は --prompt 不要で実行可能
    if args.list_models:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print(
                "Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required.",
                file=sys.stderr,
            )
            sys.exit(1)
        list_available_models(api_key)
        sys.exit(0)

    # --prompt は --list-models 以外では必須
    if not args.prompt:
        print("Error: --prompt (-p) is required.", file=sys.stderr)
        sys.exit(1)

    api_key = validate_args(args)

    try:
        if args.chat or args.session:
            generate_chat(args, api_key)
        else:
            generate_single_shot(args, api_key)
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            print(f"Error: Rate limit exceeded. Please wait and retry.\n{e}", file=sys.stderr)
        elif "403" in error_str:
            print(f"Error: Permission denied. Check your API key.\n{e}", file=sys.stderr)
        elif "404" in error_str:
            print(
                f"Error: Model not found. The model ID may have changed.\n{e}\n\n"
                f"Run with --list-models to see available image generation models.",
                file=sys.stderr,
            )
        elif "400" in error_str:
            print(f"Error: Bad request. Check your prompt and parameters.\n{e}", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
