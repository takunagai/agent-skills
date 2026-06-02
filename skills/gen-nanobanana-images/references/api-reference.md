# Nano Banana API Reference

## Model Specifications

| Feature | Flash (旧版) | Flash2 / NB2 (推奨) | Pro (最高品質) |
|---------|-------------|---------------------|---------------|
| Model ID | `gemini-2.5-flash-image` | `gemini-3.1-flash-image-preview` | `gemini-3-pro-image-preview` |
| Max Input Tokens | 32,768 | 32,768 | 65,536 |
| Max Output Tokens | 8,192 | 8,192 | 32,768 |
| Max Images/Prompt | 1 | 14 | 14 |
| Image Sizes | 1K only | 512px, 1K, 2K, 4K | 1K, 2K, 4K |
| Text Rendering | Basic | Good | High accuracy |
| Google Search | No | Yes | Yes |
| Image Search | No | Yes (exclusive) | No |
| Thinking Levels | minimal, low, medium, high | minimal, high | low, high |
| Multi-Turn Editing | No | Yes (thought_signature: SDK auto) | Yes (thought_signature required) |
| Aspect Ratios | 10 standard | 10 + 4 ultra | 10 standard |
| Speed | Fast (~5-15s) | Fast (~5-15s) | Slower (~15-60s, 4K: ~180-360s) |
| Cost | Lowest | Low | Higher |

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
| Max images per prompt (Flash2/Pro) | 14 |
| Max images per prompt (Flash) | 1 |
| Image sizes (Flash2) | 512px, 1K, 2K, 4K |
| Image sizes (Pro) | 1K, 2K, 4K |
| Temperature range | 0.0 - 2.0 |
| topP default | 0.95 |
| topK | 64 (fixed) |
| Knowledge cutoff | January 2025 |
