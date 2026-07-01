#!/usr/bin/env python3
"""Optionally compress a session JSONL after manifest creation. Never deletes the source."""

from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True, type=Path, help="Source JSONL to archive.")
    parser.add_argument("--manifest", required=True, type=Path, help="Existing manifest.json proving handoff artifacts exist.")
    parser.add_argument("--archive-dir", required=True, type=Path, help="Directory for compressed copy.")
    parser.add_argument("--format", choices=["gz", "zst"], default="gz", help="Compression format.")
    parser.add_argument("--dry-run", action="store_true", help="Show destination without writing.")
    return parser.parse_args()


def gzip_copy(src: Path, dst: Path) -> None:
    with src.open("rb") as source, gzip.open(dst, "wb", compresslevel=6) as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)


def zstd_copy(src: Path, dst: Path) -> None:
    if shutil.which("zstd") is None:
        raise SystemExit("zstd executable not found; use --format gz")
    with dst.open("wb") as target:
        subprocess.run(["zstd", "-q", "-c", str(src)], check=True, stdout=target)


def main() -> int:
    args = parse_args()
    if not args.jsonl.exists():
        raise SystemExit(f"JSONL not found: {args.jsonl}")
    if not args.manifest.exists():
        raise SystemExit(f"manifest not found: {args.manifest}")
    suffix = ".jsonl.gz" if args.format == "gz" else ".jsonl.zst"
    destination = args.archive_dir / f"{args.jsonl.stem}{suffix}"
    print(f"source: {args.jsonl}")
    print(f"destination: {destination}")
    print("source_will_be_deleted: false")
    if args.dry_run:
        return 0
    args.archive_dir.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SystemExit(f"refusing to overwrite existing archive: {destination}")
    if args.format == "gz":
        gzip_copy(args.jsonl, destination)
    else:
        zstd_copy(args.jsonl, destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
