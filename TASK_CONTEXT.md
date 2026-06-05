# Task Context

## Objective

Build and maintain a Codex skill for structured image generation using `image_generation` with target model `gpt-image-2`.

The skill should support:

- Text-only image generation.
- Reference-image regeneration.
- Reference image plus text-description generation.
- Structured JSON prompts before generation.
- Accurate style classification, including non-3D flat/soft-gradient UI icons.
- True transparent PNG output when requested or required by the reference.
- Final image resizing only after alpha transparency is produced.

## Current Skill State

The active skill is stored at:

- `F:\image\image2-reference-regenerate\SKILL.md`

Important current rules:

- Input mode must be classified as `text_only`, `reference_only`, or `reference_plus_text`.
- Text-only mode must not assume fixed size or transparent PNG unless explicitly requested.
- Reference-only mode defaults to matching the reference image dimensions and transparency mask.
- Reference-plus-text mode extracts text overrides such as visual style, colors, shape description, subject replacement, material, background, dimensions, and transparency requirements, then merges them into the reference JSON.
- Merge priority is: explicit user text, observable reference facts, necessary inference, default preference.
- Lightweight app icons should be classified as `flat_gradient_icon` or `soft_gradient_ui_icon`, not automatically as 3D.
- Transparent PNG post-processing order is: remove green screen, then resize, then verify alpha and dimensions.

## Known Environment Constraint

The host `image_generation` tool can hit `TooManyRequests` rate limits. Local Garden/API mode is currently unavailable unless `OPENAI_API_KEY` and `ENABLE_GARDEN_IMAGEGEN` are configured.

## Local Scripts

- `image2-reference-regenerate/scripts/match_reference_size.ps1`: read or match image dimensions.
- `image2-reference-regenerate/scripts/remove_green_screen.ps1`: convert chroma key background to alpha.
- `image2-reference-regenerate/scripts/check_png_transparency.ps1`: verify PNG alpha and transparent pixels.

