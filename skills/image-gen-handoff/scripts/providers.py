#!/usr/bin/env python3
"""Provider adapters for image-gen-handoff."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator


@dataclass
class ImageGenEvent:
    provider: str
    event_index: int
    line_number: int
    json_path: str
    event_type: str
    created_at: str | None
    final_image_prompt: str | None
    prompt_source: str
    prompt_sha256: str | None
    result_count: int
    result_byte_lengths: list[int]
    result_magic: list[str]
    raw_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def iter_jsonl(path: Path, max_lines: int | None = None) -> Iterator[tuple[int, dict[str, Any] | None, str | None]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if max_lines is not None and line_number > max_lines:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield line_number, json.loads(stripped), None
            except json.JSONDecodeError as exc:
                yield line_number, None, str(exc)


def compact_hash(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def looks_like_base64(value: str) -> bool:
    if len(value) < 128:
        return False
    sample = value[:256]
    return all(ch.isalnum() or ch in "+/=_-" for ch in sample)


def summarize_base64_payload(value: str) -> tuple[int | None, str | None]:
    try:
        payload = value
        if "," in payload and payload[:64].startswith("data:"):
            payload = payload.split(",", 1)[1]
        raw = base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError):
        return None, None
    return len(raw), raw[:12].hex()


def parse_maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def walk(value: Any, path: str = "$") -> Iterator[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def node_type(node: Any) -> str | None:
    if not isinstance(node, dict):
        return None
    value = node.get("type") or node.get("name") or node.get("tool_name")
    return value if isinstance(value, str) else None


def is_image_generation_node(node: Any) -> bool:
    kind = node_type(node)
    return bool(kind and "image_generation_call" in kind)


def first_string_from_keys(node: dict[str, Any], keys: tuple[str, ...]) -> tuple[str | None, str | None]:
    for key in keys:
        if key not in node:
            continue
        value = parse_maybe_json(node[key])
        if isinstance(value, str) and value.strip() and not looks_like_base64(value):
            return value.strip(), key
        if isinstance(value, dict):
            nested, source = first_string_from_keys(value, keys)
            if nested:
                return nested, f"{key}.{source}"
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, str) and item.strip() and not looks_like_base64(item):
                    return item.strip(), f"{key}[{index}]"
                if isinstance(item, dict):
                    nested, source = first_string_from_keys(item, keys)
                    if nested:
                        return nested, f"{key}[{index}].{source}"
    return None, None


def extract_prompt_from_node(node: dict[str, Any]) -> tuple[str | None, str]:
    preferred = (
        "prompt",
        "final_image_prompt",
        "revised_prompt",
        "input_text",
        "input",
        "query",
        "text",
        "content",
    )
    prompt, source = first_string_from_keys(node, preferred)
    if prompt:
        return prompt, source or "node"

    for key in ("arguments", "args", "parameters", "input"):
        if key not in node:
            continue
        parsed = parse_maybe_json(node[key])
        if isinstance(parsed, dict):
            prompt, source = first_string_from_keys(parsed, preferred)
            if prompt:
                return prompt, f"{key}.{source}"
    return None, "missing"


def collect_recent_texts(obj: Any, limit_per_line: int = 12) -> list[str]:
    texts: list[str] = []
    useful_keys = {"prompt", "final_image_prompt", "input", "text", "content", "message"}
    for path, value in walk(obj):
        if len(texts) >= limit_per_line:
            break
        if not isinstance(value, str):
            continue
        if looks_like_base64(value) or len(value) > 20000:
            continue
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        if key in useful_keys and value.strip():
            texts.append(value.strip())
    return texts


def collect_result_metadata(node: dict[str, Any], include_result_metadata: bool) -> tuple[int, list[int], list[str]]:
    count = 0
    lengths: list[int] = []
    magic: list[str] = []
    for path, value in walk(node):
        if not isinstance(value, str):
            continue
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        if key not in {"result", "image", "b64_json", "data"} and not looks_like_base64(value):
            continue
        if not looks_like_base64(value):
            continue
        count += 1
        if include_result_metadata:
            byte_length, header = summarize_base64_payload(value)
            if byte_length is not None:
                lengths.append(byte_length)
            if header:
                magic.append(header)
    return count, lengths, magic


class CodexAdapter:
    provider = "codex"

    def extract_events(
        self,
        jsonl_path: Path,
        *,
        include_result_metadata: bool = False,
        limit_events: int | None = None,
        max_lines: int | None = None,
    ) -> tuple[list[ImageGenEvent], list[str]]:
        events: list[ImageGenEvent] = []
        warnings: list[str] = []
        recent_texts: deque[str] = deque(maxlen=20)

        for line_number, obj, error in iter_jsonl(jsonl_path, max_lines=max_lines):
            if error:
                warnings.append(f"line {line_number}: invalid JSON: {error}")
                continue
            if obj is None:
                continue

            for text in collect_recent_texts(obj):
                recent_texts.append(text)

            for json_path, node in walk(obj):
                if not is_image_generation_node(node):
                    continue
                assert isinstance(node, dict)
                prompt, prompt_source = extract_prompt_from_node(node)
                if not prompt and recent_texts:
                    prompt = recent_texts[-1]
                    prompt_source = "nearest_prior_text"
                result_count, byte_lengths, magic = collect_result_metadata(node, include_result_metadata)
                event = ImageGenEvent(
                    provider=self.provider,
                    event_index=len(events) + 1,
                    line_number=line_number,
                    json_path=json_path,
                    event_type=node_type(node) or "image_generation_call",
                    created_at=find_first_created_at(obj),
                    final_image_prompt=prompt,
                    prompt_source=prompt_source,
                    prompt_sha256=compact_hash(prompt),
                    result_count=result_count,
                    result_byte_lengths=byte_lengths,
                    result_magic=magic,
                    raw_id=find_first_id(node),
                )
                events.append(event)
                if limit_events is not None and len(events) >= limit_events:
                    return events, warnings
        return events, warnings

    def extract_images(
        self,
        jsonl_path: Path,
        output_dir: Path,
        *,
        prefix: str = "imagegen",
        limit_events: int | None = None,
        max_lines: int | None = None,
        overwrite: bool = False,
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        event_number = 0
        for _line_number, obj, error in iter_jsonl(jsonl_path, max_lines=max_lines):
            if error or obj is None:
                continue
            for _json_path, node in walk(obj):
                if not is_image_generation_node(node):
                    continue
                assert isinstance(node, dict)
                event_number += 1
                for payload_index, payload in enumerate(iter_base64_payloads(node), start=1):
                    suffix = detect_image_suffix(payload) or "png"
                    out = output_dir / f"{prefix}-{event_number:04d}-{payload_index:02d}.{suffix}"
                    if out.exists() and not overwrite:
                        raise FileExistsError(f"refusing to overwrite {out}")
                    out.write_bytes(payload)
                    written.append(out)
                if limit_events is not None and event_number >= limit_events:
                    return written
        return written


def find_first_id(node: Any) -> str | None:
    if isinstance(node, dict):
        for key in ("id", "call_id", "item_id"):
            value = node.get(key)
            if isinstance(value, str):
                return value
    return None


def find_first_created_at(obj: Any) -> str | None:
    for _path, value in walk(obj):
        if isinstance(value, dict):
            for key in ("created_at", "timestamp", "time"):
                candidate = value.get(key)
                if isinstance(candidate, str):
                    return candidate
    return None


def iter_base64_payloads(node: Any) -> Iterator[bytes]:
    for _path, value in walk(node):
        if not isinstance(value, str) or not looks_like_base64(value):
            continue
        try:
            payload = value
            if "," in payload and payload[:64].startswith("data:"):
                payload = payload.split(",", 1)[1]
            raw = base64.b64decode(payload, validate=False)
        except (binascii.Error, ValueError):
            continue
        if raw.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"RIFF")):
            yield raw


def detect_image_suffix(payload: bytes) -> str | None:
    if payload.startswith(b"\x89PNG"):
        return "png"
    if payload.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if payload.startswith(b"GIF8"):
        return "gif"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "webp"
    return None


def get_adapter(name: str) -> CodexAdapter:
    if name == "codex":
        return CodexAdapter()
    raise ValueError(f"unsupported provider: {name}")
