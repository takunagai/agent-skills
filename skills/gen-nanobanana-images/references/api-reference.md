# Nano Banana API Reference

## Model Specifications

GA models (Flash2 / Pro released 2026-05-28, Lite released 2026-06-30):

| Feature | Flash2 / NB2 (推奨) | Pro (最高品質) | Lite (最速最安) |
|---------|---------------------|---------------|----------------|
| Model ID | `gemini-3.1-flash-image` | `gemini-3-pro-image` | `gemini-3.1-flash-lite-image` |
| Max Input Tokens | 32,768 | 65,536 | 32,768 |
| Max Output Tokens | 8,192 | 32,768 | 8,192 |
| Max Images/Prompt | 14 | 14 | 14 |
| Image Sizes | 512px, 1K, 2K, 4K | 1K, 2K, 4K | 1K only |
| Text Rendering | Good | High accuracy | Basic |
| Google Search | Yes | Yes | No |
| Image Search | Yes (exclusive) | No | No |
| Thinking Levels | minimal, high | low, high | minimal, high |
| Multi-Turn Editing | Yes | Yes (thought_signature required) | Yes |
| Aspect Ratios | 10 + 4 ultra | 10 standard | 10 standard |
| Speed | Fast (~5-15s) | Slower (~15-60s, 4K: ~180-360s) | Fastest |
| Cost | Low | Higher | Lowest |

### 旧モデル（廃止）

- `gemini-2.5-flash-image`（旧 Flash）: 公式で「レガシー。移行を強く推奨」。本スキルからは削除済み。ドラフト用途は Lite を使う。
- `gemini-3.1-flash-image-preview` / `gemini-3-pro-image-preview`（preview ID）: 2026-05-28 に deprecated 告知、**2026-06-25 shutdown**。GA ID（`gemini-3.1-flash-image` / `gemini-3-pro-image`）へ移行済み。`--list-models` には preview ID がまだ列挙されることがあるが常用してはならない。

## Pricing（画像 1 枚あたり, Standard tier, 2026-06-30, 出典 https://ai.google.dev/gemini-api/docs/pricing）

| Model | 512px | 1K | 2K | 4K |
|-------|-------|-----|-----|-----|
| Lite | — | $0.0336 | — | — |
| Flash2 | $0.045 | $0.067 | $0.101 | $0.151 |
| Pro | — | $0.134 | $0.134 | $0.24 |

（Pro は 512px 帯なし。Lite は 1K のみ。）

## Aspect Ratios

**Standard (all models)**: `1:1`, `3:2`, `2:3`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

**Extended (flash2 only)**: `1:4`, `4:1`, `1:8`, `8:1`

## API Classes

### GenerateContentConfig

```python
from google.genai import types

config = types.GenerateContentConfig(
    responseModalities=["IMAGE", "TEXT"],  # IMAGE, TEXT, or both
    imageConfig=types.ImageConfig(
        aspectRatio="16:9",   # Required
        imageSize="2K",       # flash2: 512px/1K/2K/4K, pro: 1K/2K/4K
    ),
    thinkingConfig=types.ThinkingConfig(
        thinkingLevel="HIGH",  # Enum: MINIMAL, LOW, MEDIUM, HIGH
    ),
    tools=[types.Tool(googleSearch=types.GoogleSearch())],  # flash2/pro
)

# Image Search (flash2 only) — with optional Web Search
config_with_image_search = types.GenerateContentConfig(
    responseModalities=["IMAGE", "TEXT"],
    imageConfig=types.ImageConfig(aspectRatio="1:1"),
    tools=[types.Tool(googleSearch=types.GoogleSearch(
        searchTypes=types.SearchTypes(
            imageSearch=types.ImageSearch(),
            webSearch=types.WebSearch(),  # optional: combine with web search
        )
    ))],
)
```

> **SDK requirement for Image Search**: the typed `types.SearchTypes` / `types.ImageSearch` / `types.WebSearch` classes were introduced in **`google-genai` v1.65.0** (2026-02-26); **v2.10.0+ recommended**. On older SDKs these classes are absent and there is no working raw-dict fallback (the API rejects it via `extra_forbidden`). The script checks `hasattr(types, "SearchTypes")` at startup and exits with an upgrade message if missing. Image Search grounding is **flash2 only**.

### Part Types for Image Input

```python
# ローカルファイルから
part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

# Cloud Storage URI から
part = types.Part.from_uri(file_uri="gs://bucket/image.png", mime_type="image/png")

# Base64 インライン
part = types.Part(inline_data=types.Blob(mime_type="image/png", data=b64_string))
```

Supported MIME types: `image/png`, `image/jpeg`, `image/webp`, `image/heic`, `image/heif`

### Response Structure

```python
response = client.models.generate_content(model=model_id, contents=contents, config=config)

for part in response.candidates[0].content.parts:
    if part.thought:           # 思考テキスト (デバッグ用)
        pass
    if part.thought_signature: # Multi-turn用署名
        pass
    if part.text:              # テキスト応答
        print(part.text)
    if part.inline_data:       # 画像データ
        image = part.as_image()  # -> PIL.Image
        image.save("output.png")
```

## Thought Signature Protocol

Thought signatures are mandatory for Gemini 3 Pro Image multi-turn editing.

### Rules
1. Signatures appear on the **first part after thoughts** (text or image) and **every subsequent image part**
2. **All signatures** from the previous model response must be included in the next request
3. Missing or invalid signatures cause **400 errors**
4. The model uses signatures to understand the original image's composition and logic

### Session persistence (base64)

`thought_signature` values are raw **bytes** and cannot be `json.dump`-ed directly. The script stores each signature in the session JSON as a base64 string under the key **`thought_signature_b64`** (`base64.b64encode(sig).decode("ascii")`), and decodes it back to bytes with `base64.b64decode` when rebuilding history for the next turn. (Earlier builds tried to serialize the raw bytes and crashed with `TypeError: Object of type bytes is not JSON serializable`, so no legacy `thought_signature` key exists in valid session files.)

### Signature Positions in Response

```
Part 0: thought (text)           -> No signature
Part 1: text or image            -> HAS thought_signature (first after thoughts)
Part 2: image                    -> HAS thought_signature
Part 3: image                    -> HAS thought_signature
```

### Bypass (Migration Only)

For migration scenarios lacking valid signatures, use the bypass string:
```
"context_engineering_is_the_way_to_go"
```
This disables strict validation. Only use for migration, not production workflows.

## Error Codes

| HTTP Code | Cause | Resolution |
|-----------|-------|------------|
| 400 | Invalid request (bad params, missing thought_signature) | Check parameters and session integrity |
| 403 | Invalid API key or quota exceeded | Verify API key at aistudio.google.com |
| 404 | Model not found | Check model ID spelling |
| 429 | Rate limit exceeded | Wait and retry with exponential backoff |
| 500 | Internal server error | Retry after delay |
| 503 | Service temporarily unavailable | Retry with exponential backoff |

### Content Filtering

If the response contains no image parts, the prompt was likely filtered by safety settings. Try:
- Removing potentially sensitive content from the prompt
- Using more neutral language
- Avoiding copyrighted characters or real persons

## Constraints Summary

| Constraint | Value |
|-----------|-------|
| Max inline file size | 7 MB |
| Max Cloud Storage file size | 30 MB |
| Max images per prompt (all models) | 14 |
| Image sizes (Flash2) | 512px, 1K, 2K, 4K |
| Image sizes (Pro) | 1K, 2K, 4K |
| Image sizes (Lite) | 1K only |
| Temperature range | 0.0 - 2.0 |
| topP default | 0.95 |
| topK | 64 (fixed) |
| Knowledge cutoff | January 2025 |
