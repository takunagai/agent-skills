# Prompt Engineering Guide

## 6-Element Prompt Structure

Effective prompts combine these elements:

1. **Subject** - What to generate (e.g., "a golden retriever puppy")
2. **Action** - What the subject is doing (e.g., "playing with a ball")
3. **Environment** - Setting and background (e.g., "in a sunlit park")
4. **Composition** - Camera angle and framing (e.g., "close-up, shallow depth of field")
5. **Lighting** - Light quality and direction (e.g., "warm golden hour light")
6. **Style** - Artistic style (e.g., "photorealistic", "watercolor painting", "3D render")

Example: `A golden retriever puppy playing with a red ball in a sunlit park. Close-up shot with shallow depth of field. Warm golden hour lighting. Photorealistic style.`

## Text Rendering Rule

To render text within images, wrap the text in **double quotation marks**:

- `A coffee cup with "PREMIUM BLEND" written on it` (correct)
- `A coffee cup with PREMIUM BLEND written on it` (may fail or distort)

Pro model produces significantly more accurate text rendering than Flash.

## Negative Constraints

The script automatically appends quality constraints. For additional control, add to your prompt:

```
Avoid: [specific unwanted elements]
```

Common constraints: `low quality, blurry, noisy, deformed hands, watermark, text artifacts, oversaturated colors, cropped, out of frame`

## Model-Specific Tips

**Flash** - Keep prompts concise (1-3 sentences). Best for rapid iteration and drafts.

**Flash2 (Recommended)** - Supports detailed prompts (3-5 sentences) like Pro, with Flash-level speed. Best balance of quality and speed. Use `--image-search` for product/real-world object accuracy. Supports ultra-wide/tall ratios (1:4, 4:1, 1:8, 8:1) for banners and tall visuals. Use `512px` size for icons and thumbnails.

**Pro** - Use detailed prompts (3-6 sentences). Specify technical details for best results. Ideal for final production images with maximum text rendering accuracy.

## Image Editing Prompts

When editing with `--input-image`:
- Be specific about what to change: "Change the sky to sunset orange" (good) vs "Make it better" (vague)
- Reference elements visible in the image
- Combine additions and modifications: "Add a cat on the windowsill and change the curtains to blue"

## Industry Templates

### A. E-Commerce / Marketing

Purpose: Brand consistency and accurate text rendering.

```
[Product] placed on [surface/environment]. [Lighting style] lighting.
Product label reads "[Brand Text]" in [font style].
Clean, professional product photography. White/neutral background.
```

Recommended: **Flash2** (fast + accurate) or **Pro** (highest text accuracy), up to 14 reference images.

### B. Education / Technical Documentation

Purpose: Factual, search-grounded diagrams and infographics.

```
Detailed cross-section diagram of [subject].
Accurate anatomical/technical labels with annotations.
Clean infographic style with [color scheme].
```

Recommended: **Flash2** or **Pro** + `--google-search` flag for factual accuracy. Flash2 also supports `--image-search` for visual references.

### C. Creative Photography

Purpose: Studio-quality lighting and composition.

```
[Subject] [action]. Shot with [lens, e.g., 85mm f/1.4].
[Camera angle, e.g., low angle]. [Lighting, e.g., Chiaroscuro lighting].
[Style, e.g., hyperrealistic 3D render / cinematic photography].
```

Workflow: **Flash2** for rapid iteration (with all Pro features), then **Pro** for final production if highest text accuracy needed.

## Style Reference Prompting

When using reference images (`-r`), explicitly describe which visual aspects to adopt.

### Specifying Reference Aspects

Be explicit about what to take from the reference:

```
Apply the warm color palette and soft brush strokes from the reference image.
A bustling city market at noon. Wide angle composition.
```

```
Match the dramatic chiaroscuro lighting from the reference.
A portrait of a musician holding a violin. Close-up, dark background.
```

```
Use the composition layout and framing style from the reference.
A still life with flowers and fruit on a wooden table.
```

### Multiple References

When using multiple reference images, assign a role to each:

```
Use the first reference image for color palette and the second for composition.
A serene lake surrounded by autumn trees. Golden hour lighting.
```

```
Combine the lighting style from the first reference with the texture and brushwork from the second.
An old stone bridge over a quiet river.
```

### Reference + Input Image Editing

When combining `-i` (edit target) and `-r` (style reference):

```
Repaint the input image in the artistic style of the reference.
Preserve the original composition and subject placement.
```

```
Apply the color grading and atmosphere from the reference to the input photograph.
Keep the subject sharp and well-defined.
```

### Best Practices

- Name specific visual elements: "color palette", "lighting", "texture", "brush strokes", "composition", "framing"
- Avoid vague references: "make it look like the reference" is less effective than "apply the warm earth tones and soft diffused lighting from the reference"
- Flash2 or Pro recommended for reference-based generation (Flash supports only 1 total image)
