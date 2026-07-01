# manifest.json schema

Use this schema when reading or extending manifests produced by `scripts/build_manifest.py`.

## Top level

```json
{
  "schema_version": "1.0",
  "batch": {},
  "items": [],
  "validation": {}
}
```

## `batch`

- `batch_name`: Stable user-provided batch identifier.
- `created_at`: ISO timestamp when the manifest was built.
- `project_root`: Project root used to calculate relative paths.
- `image_dir`: Image directory argument as provided by the caller.
- `source_jsonl`: Source session JSONL path, or `null` for `--no-jsonl`.
- `provider`: Provider adapter name, currently `codex`, or `null` for `--no-jsonl`.
- `mode`: `audit-existing-images` or `image-only`.

## `items[]`

- `index`: 1-based manifest order after natural filename sorting.
- `output_file`: Image path relative to `project_root` when possible.
- `absolute_path`: Resolved local image path for validation on the current machine.
- `final_image_prompt`: Final prompt extracted from the provider transcript. Never invent this value.
- `source_prompt_file`: Reserved for future prompt-log correlation.
- `source_prompt_index`: Numeric index inferred from the image filename, if any.
- `aspect_ratio_requested`: Reserved for future prompt parsing.
- `width`, `height`: Image dimensions, or `null` when unknown.
- `file_size_bytes`: Image file size.
- `sha256`: SHA-256 hash of image bytes.
- `modified_at`: Image mtime in ISO format.
- `generated_at`: Provider event timestamp when available.
- `source_jsonl_event_index`: 1-based image generation event index.
- `source_jsonl_line_number`: JSONL line number where the matched event was found.
- `confidence`: One of `high`, `medium`, `low`, `missing`.
- `needs_review`: Boolean review flag. Set true for `low` and `missing`.
- `notes`: Short machine- and human-readable reasons for confidence.

## `validation`

- `expected_count`: Caller-provided expected image count, or `null`.
- `present_count`: Number of scanned image files.
- `event_count`: Number of extracted provider image generation events.
- `missing_count`: Number of items without a prompt match.
- `missing_files`: Files whose prompt is missing.
- `bad_dimensions_count`: Count of images that do not match expected dimensions.
- `bad_dimensions`: Files with dimension mismatches.
- `duplicate_hash_groups`: Groups of files with identical SHA-256 values.
- `warnings`: JSONL parse warnings and recoverable provider warnings.
- `count_matches_expected`: Present only when `expected_count` is supplied.

## Confidence rules

- `high`: Filename number and generation order align, or filename number, generation order, and prompt number align.
- `medium`: Image count and generation event count match, but filename or prompt-number evidence is weak.
- `low`: The image is paired by order, but event count and image count differ.
- `missing`: No provider event or final prompt could be matched.

Never treat `confidence=high` as proof that semantic content matches the image. It means the handoff evidence is strong enough for normal batch bookkeeping.
