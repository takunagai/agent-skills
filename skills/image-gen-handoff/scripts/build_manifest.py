#!/usr/bin/env python3
"""Build manifest.json, manifest.md, and optional handoff note for image batches."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from providers import get_adapter
from validate_manifest import compute_sha256, image_dimensions

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


@dataclass
class ImageRecord:
    path: Path
    relpath: str
    width: int | None
    height: int | None
    file_size_bytes: int
    sha256: str
    mtime: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path, help="Project root used for relative paths.")
    parser.add_argument("--image-dir", required=True, type=Path, help="Image directory, relative to project root or absolute.")
    parser.add_argument("--jsonl", type=Path, help="Codex session JSONL. Omit with --no-jsonl.")
    parser.add_argument("--provider", default="codex", choices=["codex"], help="Provider adapter.")
    parser.add_argument("--batch-name", required=True, help="Stable batch name for output metadata.")
    parser.add_argument("--out-json", type=Path, help="manifest.json output path.")
    parser.add_argument("--out-md", type=Path, help="manifest.md output path.")
    parser.add_argument("--handoff-md", type=Path, help="Optional handoff note path.")
    parser.add_argument("--expected-count", type=int, help="Expected image count.")
    parser.add_argument("--expected-width", type=int, help="Expected width for all images.")
    parser.add_argument("--expected-height", type=int, help="Expected height for all images.")
    parser.add_argument("--no-jsonl", action="store_true", help="Build an image-only manifest without prompt extraction.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing files or copying images.")
    parser.add_argument("--limit-events", type=int, help="Limit JSONL image events.")
    parser.add_argument("--max-lines", type=int, help="Limit JSONL lines read.")
    parser.add_argument("--copy-to", type=Path, help="Optional: copy images to this directory.")
    parser.add_argument("--overwrite", action="store_true", help="Allow --copy-to to overwrite existing files.")
    parser.add_argument(
        "--rename-format",
        help="Optional with --copy-to: format copied filenames, e.g. '{batch}-{index:03d}{ext}'.",
    )
    return parser.parse_args()


def resolve_under_project(project_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else project_root / path


def iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def scan_images(project_root: Path, image_dir: Path) -> list[ImageRecord]:
    root = resolve_under_project(project_root, image_dir)
    assert root is not None
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda path: natural_key(str(path.relative_to(root))),
    )
    records: list[ImageRecord] = []
    for path in files:
        stat = path.stat()
        width, height = image_dimensions(path)
        records.append(
            ImageRecord(
                path=path,
                relpath=str(path.relative_to(project_root)) if path.is_relative_to(project_root) else str(path),
                width=width,
                height=height,
                file_size_bytes=stat.st_size,
                sha256=compute_sha256(path),
                mtime=iso_from_timestamp(stat.st_mtime),
            )
        )
    return records


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def image_number(path: str) -> int | None:
    matches = re.findall(r"(?<!\d)(\d{1,5})(?!\d)", Path(path).stem)
    return int(matches[-1]) if matches else None


def prompt_mentions_number(prompt: str | None, number: int | None) -> bool:
    if not prompt or number is None:
        return False
    variants = {str(number), f"{number:02d}", f"{number:03d}"}
    return any(re.search(rf"(?<!\d){re.escape(variant)}(?!\d)", prompt) for variant in variants)


def confidence_for(record: ImageRecord, event: dict[str, Any] | None, index: int, equal_counts: bool) -> tuple[str, bool, list[str]]:
    notes: list[str] = []
    if event is None or not event.get("final_image_prompt"):
        return "missing", True, ["final_image_prompt is missing"]
    number = image_number(record.relpath)
    if number == index and prompt_mentions_number(event.get("final_image_prompt"), number):
        return "high", False, ["filename number, generation order, and prompt number align"]
    if number == index and equal_counts:
        return "high", False, ["filename number and generation order align"]
    if equal_counts:
        return "medium", False, ["image count and event order align"]
    notes.append("paired by order but image count and event count differ")
    return "low", True, notes


def duplicate_groups(records: list[ImageRecord]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for record in records:
        groups.setdefault(record.sha256, []).append(record.relpath)
    return [
        {"sha256": sha, "files": files}
        for sha, files in sorted(groups.items())
        if len(files) > 1
    ]


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    image_dir = resolve_under_project(project_root, args.image_dir)
    if image_dir is None or not image_dir.exists():
        raise SystemExit(f"image directory not found: {image_dir}")

    records = scan_images(project_root, args.image_dir)
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not args.no_jsonl:
        if not args.jsonl:
            raise SystemExit("--jsonl is required unless --no-jsonl is set")
        adapter = get_adapter(args.provider)
        extracted, warnings = adapter.extract_events(
            args.jsonl,
            include_result_metadata=False,
            limit_events=args.limit_events,
            max_lines=args.max_lines,
        )
        events = [event.to_dict() for event in extracted]

    equal_counts = bool(events) and len(records) == len(events)
    items: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        event = events[index - 1] if index - 1 < len(events) else None
        confidence, needs_review, notes = confidence_for(record, event, index, equal_counts)
        item = {
            "index": index,
            "output_file": record.relpath,
            "absolute_path": str(record.path.resolve()),
            "final_image_prompt": event.get("final_image_prompt") if event else None,
            "source_prompt_file": None,
            "source_prompt_index": image_number(record.relpath),
            "aspect_ratio_requested": None,
            "width": record.width,
            "height": record.height,
            "file_size_bytes": record.file_size_bytes,
            "sha256": record.sha256,
            "modified_at": record.mtime,
            "generated_at": event.get("created_at") if event else None,
            "source_jsonl_event_index": event.get("event_index") if event else None,
            "source_jsonl_line_number": event.get("line_number") if event else None,
            "confidence": confidence,
            "needs_review": needs_review,
            "notes": notes,
        }
        items.append(item)

    bad_dimensions = [
        item["output_file"]
        for item in items
        if (
            (args.expected_width is not None and item["width"] != args.expected_width)
            or (args.expected_height is not None and item["height"] != args.expected_height)
        )
    ]
    missing = [item["output_file"] for item in items if item["confidence"] == "missing"]
    validation = {
        "expected_count": args.expected_count,
        "present_count": len(records),
        "event_count": len(events),
        "missing_count": len(missing),
        "missing_files": missing,
        "bad_dimensions_count": len(bad_dimensions),
        "bad_dimensions": bad_dimensions,
        "duplicate_hash_groups": duplicate_groups(records),
        "warnings": warnings,
    }
    if args.expected_count is not None:
        validation["count_matches_expected"] = len(records) == args.expected_count

    manifest = {
        "schema_version": "1.0",
        "batch": {
            "batch_name": args.batch_name,
            "created_at": datetime.now().astimezone().isoformat(),
            "project_root": str(project_root),
            "image_dir": str(args.image_dir),
            "source_jsonl": str(args.jsonl) if args.jsonl else None,
            "provider": args.provider if not args.no_jsonl else None,
            "mode": "audit-existing-images" if not args.no_jsonl else "image-only",
        },
        "items": items,
        "validation": validation,
    }
    return manifest


def write_markdown(manifest: dict[str, Any]) -> str:
    batch = manifest["batch"]
    validation = manifest["validation"]
    lines = [
        f"# {batch['batch_name']} manifest",
        "",
        "## Summary",
        "",
        f"- Images: {validation['present_count']}",
        f"- Image generation events: {validation['event_count']}",
        f"- Missing prompts: {validation['missing_count']}",
        f"- Bad dimensions: {validation['bad_dimensions_count']}",
        f"- Duplicate hash groups: {len(validation['duplicate_hash_groups'])}",
        "",
        "## Items",
        "",
        "| # | file | size | confidence | review | prompt |",
        "|---:|------|------|------------|--------|--------|",
    ]
    for item in manifest["items"]:
        prompt = (item.get("final_image_prompt") or "").replace("\n", " ")
        if len(prompt) > 96:
            prompt = prompt[:93] + "..."
        lines.append(
            f"| {item['index']} | `{item['output_file']}` | "
            f"{item.get('width')}x{item.get('height')} | {item['confidence']} | "
            f"{'yes' if item['needs_review'] else 'no'} | {prompt} |"
        )
    return "\n".join(lines) + "\n"


def write_handoff(manifest: dict[str, Any]) -> str:
    batch = manifest["batch"]
    validation = manifest["validation"]
    lines = [
        f"# {batch['batch_name']} 引き継ぎ",
        "",
        "## 現状",
        "",
        f"- 画像数: {validation['present_count']}",
        f"- 抽出イベント数: {validation['event_count']}",
        f"- 最終生成プロンプト欠損: {validation['missing_count']}",
        f"- 寸法不一致: {validation['bad_dimensions_count']}",
        f"- 重複ハッシュグループ: {len(validation['duplicate_hash_groups'])}",
        "",
        "## 成果物",
        "",
        "- `manifest.json`: 画像、最終生成プロンプト、sha256、寸法、対応付け信頼度",
        "- `manifest.md`: 確認用サマリ",
        "",
        "## 要確認",
        "",
    ]
    review_items = [item for item in manifest["items"] if item.get("needs_review")]
    if review_items:
        for item in review_items[:50]:
            lines.append(f"- `{item['output_file']}`: confidence={item['confidence']}; {', '.join(item['notes'])}")
        if len(review_items) > 50:
            lines.append(f"- ... and {len(review_items) - 50} more")
    else:
        lines.append("- なし")
    return "\n".join(lines) + "\n"


def maybe_copy_images(
    manifest: dict[str, Any],
    project_root: Path,
    copy_to: Path,
    rename_format: str | None,
    dry_run: bool,
    overwrite: bool,
) -> None:
    target_root = copy_to if copy_to.is_absolute() else project_root / copy_to
    if dry_run:
        return
    target_root.mkdir(parents=True, exist_ok=True)
    for item in manifest["items"]:
        src = Path(item["absolute_path"])
        ext = src.suffix
        filename = (
            rename_format.format(
                batch=manifest["batch"]["batch_name"],
                index=item["index"],
                stem=src.stem,
                ext=ext,
            )
            if rename_format
            else src.name
        )
        dst = target_root / filename
        if dst.resolve() == src.resolve():
            continue
        if dst.exists() and not overwrite:
            raise SystemExit(f"refusing to overwrite existing file: {dst}")
        shutil.copy2(src, dst)


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args)
    summary = {
        "batch_name": args.batch_name,
        "present_count": manifest["validation"]["present_count"],
        "event_count": manifest["validation"]["event_count"],
        "missing_count": manifest["validation"]["missing_count"],
        "bad_dimensions_count": manifest["validation"]["bad_dimensions_count"],
        "duplicate_hash_group_count": len(manifest["validation"]["duplicate_hash_groups"]),
        "would_write": [] if args.dry_run else [str(path) for path in (args.out_json, args.out_md, args.handoff_md) if path],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0

    project_root = args.project_root.resolve()
    if args.copy_to:
        maybe_copy_images(manifest, project_root, args.copy_to, args.rename_format, args.dry_run, args.overwrite)

    if args.out_json:
        out_json = resolve_under_project(project_root, args.out_json)
        assert out_json is not None
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.out_md:
        out_md = resolve_under_project(project_root, args.out_md)
        assert out_md is not None
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(write_markdown(manifest), encoding="utf-8")
    if args.handoff_md:
        handoff_md = resolve_under_project(project_root, args.handoff_md)
        assert handoff_md is not None
        handoff_md.parent.mkdir(parents=True, exist_ok=True)
        handoff_md.write_text(write_handoff(manifest), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
