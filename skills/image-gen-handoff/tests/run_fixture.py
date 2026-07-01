#!/usr/bin/env python3
"""Create a tiny fixture in a temp directory and exercise the main scripts."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path


PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lQn1GQAAAABJRU5ErkJggg=="


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="image-gen-handoff-fixture-") as tmp:
        project = Path(tmp) / "project"
        image_dir = project / "Output"
        worklog_dir = project / "worklog"
        image_dir.mkdir(parents=True)
        worklog_dir.mkdir()
        image_bytes = base64.b64decode(PNG_1X1)
        (image_dir / "sample-01.png").write_bytes(image_bytes)
        (image_dir / "sample-02.png").write_bytes(image_bytes + b"trailing")
        jsonl = project / "session.jsonl"
        rows = [
            {"type": "message", "content": "prepare prompts"},
            {
                "type": "response_item",
                "item": {
                    "type": "image_generation_call",
                    "id": "img_1",
                    "prompt": "01. A red square icon",
                    "result": PNG_1X1,
                },
            },
            {
                "type": "response_item",
                "item": {
                    "type": "image_generation_call",
                    "id": "img_2",
                    "prompt": "02. A blue square icon",
                    "result": PNG_1X1,
                },
            },
        ]
        jsonl.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

        manifest_json = image_dir / "fixture-manifest.json"
        manifest_md = image_dir / "fixture-manifest.md"
        handoff_md = worklog_dir / "fixture_handoff.md"
        subprocess.run(
            [
                sys.executable,
                str(skill_dir / "scripts" / "build_manifest.py"),
                "--project-root",
                str(project),
                "--image-dir",
                "Output",
                "--jsonl",
                str(jsonl),
                "--batch-name",
                "fixture",
                "--out-json",
                "Output/fixture-manifest.json",
                "--out-md",
                "Output/fixture-manifest.md",
                "--handoff-md",
                "worklog/fixture_handoff.md",
                "--expected-count",
                "2",
            ],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(skill_dir / "scripts" / "validate_manifest.py"),
                "--manifest",
                str(manifest_json),
                "--expected-count",
                "2",
            ],
            check=True,
        )
        assert manifest_json.exists()
        assert manifest_md.exists()
        assert handoff_md.exists()

        copied = project / "copied"
        copied.mkdir()
        (copied / "sample-01.png").write_text("existing", encoding="utf-8")
        conflict = subprocess.run(
            [
                sys.executable,
                str(skill_dir / "scripts" / "build_manifest.py"),
                "--project-root",
                str(project),
                "--image-dir",
                "Output",
                "--no-jsonl",
                "--batch-name",
                "fixture-copy",
                "--copy-to",
                "copied",
            ],
            text=True,
            capture_output=True,
        )
        assert conflict.returncode != 0
        assert "refusing to overwrite" in conflict.stderr
    print("fixture ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
