#!/usr/bin/env python3
"""Extract Codex image_generation_call events from session JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from providers import get_adapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True, type=Path, help="Path to a Codex session JSONL file.")
    parser.add_argument("--provider", default="codex", choices=["codex"], help="Provider adapter to use.")
    parser.add_argument("--out", type=Path, help="Write extracted event metadata as JSON.")
    parser.add_argument("--limit-events", type=int, help="Stop after N image generation events.")
    parser.add_argument("--max-lines", type=int, help="Stop after reading N JSONL lines.")
    parser.add_argument(
        "--include-result-metadata",
        action="store_true",
        help="Record result byte lengths and magic headers. Base64 payloads are never emitted.",
    )
    parser.add_argument(
        "--extract-images",
        action="store_true",
        help="Optional: decode image payloads from JSONL and write them to --extract-dir.",
    )
    parser.add_argument("--extract-dir", type=Path, help="Directory for --extract-images output.")
    parser.add_argument("--extract-prefix", default="imagegen", help="Filename prefix for extracted images.")
    parser.add_argument("--overwrite", action="store_true", help="Allow --extract-images to overwrite files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    adapter = get_adapter(args.provider)
    events, warnings = adapter.extract_events(
        args.jsonl,
        include_result_metadata=args.include_result_metadata,
        limit_events=args.limit_events,
        max_lines=args.max_lines,
    )
    payload = {
        "provider": args.provider,
        "source_jsonl": str(args.jsonl),
        "event_count": len(events),
        "warnings": warnings,
        "events": [event.to_dict() for event in events],
    }
    if args.extract_images:
        if not args.extract_dir:
            raise SystemExit("--extract-images requires --extract-dir")
        written = adapter.extract_images(
            args.jsonl,
            args.extract_dir,
            prefix=args.extract_prefix,
            limit_events=args.limit_events,
            max_lines=args.max_lines,
            overwrite=args.overwrite,
        )
        payload["extracted_images"] = [str(path) for path in written]

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
