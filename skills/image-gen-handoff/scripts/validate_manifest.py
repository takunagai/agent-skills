#!/usr/bin/env python3
"""Validate an image-gen-handoff manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.json.")
    parser.add_argument("--project-root", type=Path, help="Override project root in the manifest.")
    parser.add_argument("--expected-count", type=int, help="Override expected image count.")
    parser.add_argument("--expected-width", type=int, help="Expected width for all images.")
    parser.add_argument("--expected-height", type=int, help="Expected height for all images.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> tuple[int | None, int | None]:
    with path.open("rb") as handle:
        header = handle.read(64)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">II", header[16:24])
        if header.startswith(b"GIF8") and len(header) >= 10:
            return struct.unpack("<HH", header[6:10])
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            return webp_dimensions(path)
        if header.startswith(b"\xff\xd8\xff"):
            return jpeg_dimensions(path)
    return None, None


def jpeg_dimensions(path: Path) -> tuple[int | None, int | None]:
    data = path.read_bytes()
    index = 2
    while index < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break
        length = int.from_bytes(data[index:index + 2], "big")
        if marker in range(0xC0, 0xCF) and marker not in {0xC4, 0xC8, 0xCC}:
            if index + 7 <= len(data):
                height = int.from_bytes(data[index + 3:index + 5], "big")
                width = int.from_bytes(data[index + 5:index + 7], "big")
                return width, height
        index += length
    return None, None


def webp_dimensions(path: Path) -> tuple[int | None, int | None]:
    data = path.read_bytes()[:64]
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 " and len(data) >= 30:
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
        return width, height
    if chunk == b"VP8L" and len(data) >= 25:
        bits = int.from_bytes(data[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None, None


def resolve_item_path(project_root: Path, item: dict[str, Any]) -> Path:
    output_file = Path(item["output_file"])
    if output_file.is_absolute():
        return output_file
    return project_root / output_file


def duplicate_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for item in items:
        groups.setdefault(item.get("sha256"), []).append(item.get("output_file"))
    return [{"sha256": sha, "files": files} for sha, files in groups.items() if sha and len(files) > 1]


def validate(manifest: dict[str, Any], project_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    items = manifest.get("items", [])
    missing_files: list[str] = []
    sha_mismatches: list[str] = []
    dimension_mismatches: list[dict[str, Any]] = []

    for item in items:
        path = resolve_item_path(project_root, item)
        if not path.exists():
            missing_files.append(item["output_file"])
            continue
        actual_sha = compute_sha256(path)
        if actual_sha != item.get("sha256"):
            sha_mismatches.append(item["output_file"])
        width, height = image_dimensions(path)
        expected_width = args.expected_width if args.expected_width is not None else item.get("width")
        expected_height = args.expected_height if args.expected_height is not None else item.get("height")
        if width != expected_width or height != expected_height:
            dimension_mismatches.append(
                {
                    "file": item["output_file"],
                    "expected": [expected_width, expected_height],
                    "actual": [width, height],
                }
            )

    expected_count = args.expected_count
    if expected_count is None:
        expected_count = manifest.get("validation", {}).get("expected_count")
    result = {
        "ok": not missing_files and not sha_mismatches and not dimension_mismatches,
        "present_count": len(items),
        "expected_count": expected_count,
        "count_matches_expected": None if expected_count is None else len(items) == expected_count,
        "missing_files": missing_files,
        "sha_mismatches": sha_mismatches,
        "dimension_mismatches": dimension_mismatches,
        "duplicate_hash_groups": duplicate_groups(items),
    }
    if result["count_matches_expected"] is False:
        result["ok"] = False
    return result


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    project_root = args.project_root or Path(manifest["batch"]["project_root"])
    result = validate(manifest, project_root, args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok: {result['ok']}")
        print(f"present_count: {result['present_count']}")
        print(f"missing_files: {len(result['missing_files'])}")
        print(f"sha_mismatches: {len(result['sha_mismatches'])}")
        print(f"dimension_mismatches: {len(result['dimension_mismatches'])}")
        print(f"duplicate_hash_groups: {len(result['duplicate_hash_groups'])}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
