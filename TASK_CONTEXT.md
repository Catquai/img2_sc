# Task Context

## Objective

Build and maintain a Codex skill for structured image generation using `image_generation` with target model `gpt-image-2`.

The skill should support:

- Text-only image generation.
- Reference-image regeneration.
- Reference-only requests must auto-generate a new variant after JSON extraction; do not stop at analysis, list processing options, ask what to do, or ask whether to generate unless the image/tool/policy blocks generation.
- Image-only or file-path-only user messages are reference-only generation requests by default; do not ask the user to choose an action.
- Reference image plus text-description generation.
- Composite/sprite-strip resource recognition, including transparent canvas, true child-tile dimensions, square or non-square rounded-rectangle child tiles, transparent gaps, per-tile badges, and per-item invariants.
- Internal translucent-layer recognition, including separate colors, alpha levels, blend/overlap relationships, and layer order distinct from transparent PNG background.
- Frame-animation image resource recognition, including static base extraction, moving element tracking, frame order, and cross-frame invariants.
- Structured JSON prompts before generation.
- Reference-only and reference-plus-text execution must explicitly produce a `final_json` before image generation or deterministic drawing, then draw/validate from that JSON. Do not skip JSON and draw from memory or plain preview.
- Accurate style classification, including non-3D flat/soft-gradient UI icons.
- True transparent PNG output when requested or required by the reference.
- Final image resizing only after alpha transparency is produced.

## Current Skill State

The active skill is stored at:

- `E:\WORK\skill\img2_sc\img2-sc\SKILL.md`

Important current rules:

- Input mode must be classified as `text_only`, `reference_only`, or `reference_plus_text`.
- A user message containing only an image attachment, an image path, or `Files mentioned by the user` image context defaults to `reference_only` unless the user explicitly says only to analyze or not generate.
- Text-only mode must not assume fixed size or transparent PNG unless explicitly requested.
- Reference-only mode defaults to matching the reference image dimensions and transparency mask.
- Variant generation defaults to: semantic identity and style remain consistent, layout stays close, but the result is not a near copy. Prefer noticeable variation through color hue/brightness/saturation, gradient direction, rendering details, and secondary elements; do not over-deform main elements.
- Each reference JSON must classify `main_elements` and `secondary_elements`. Main elements keep identity, required traits, relationships, layer order, readability, and recognizable silhouette with conservative variation. They may have small controlled rotation, scale, and position changes, recorded in JSON limits, unless direction/text/meaning would suffer. Secondary elements can vary more widely/randomly in count, shape, color, opacity, position, and decorative treatment, as long as they do not obscure or confuse main elements.
- Composite/sprite-strip references must preserve the overall canvas while also preserving each child tile's true shape, true dimensions, transparent gaps, and alpha background.
- Sprite-strip `item_count` must come from external rounded-card/tile boundaries and transparent gaps, not from people count, badge count, wall frames, background photos, screens, or internal scene details. Internal small photos/frames belong to their parent card's content and must not become extra tiles.
- Sprite-strip references with equal-size cards must set `composite_layout.same_item_size: true` and preserve identical card width, height, aspect ratio, corner radius, top alignment, and bottom alignment. Candidate generations with non-uniform card sizes fail before post-processing; do not fix them by trimming, stretching, squeezing, or resizing.
- Card-like sprite/composite references must include a `card_inventory` JSON section before generation. It must record card count, whether card shapes/sizes match, each card's bounds, shape, corner radius, primary content, foreground/background subjects, status badge, internal secondary elements, and elements forbidden to become extra cards. Generation prompts must expand this inventory card-by-card rather than using only a single overall description.
- Reference-plus-text mode extracts text overrides such as visual style, colors, shape description, subject replacement, material, background, dimensions, and transparency requirements, then merges them into the reference JSON.
- Merge priority is: explicit user text, observable reference facts, necessary inference, default preference.
- Lightweight app icons should be classified as `flat_gradient_icon` or `soft_gradient_ui_icon`, not automatically as 3D.
- Icons with internal semi-transparent panels must preserve each panel's color, opacity, blend/overlap relationship, and layer order; do not collapse same-color or different-color translucent layers into one solid shape.
- Reference alpha must be analyzed into fully transparent, semi-transparent, and opaque regions in `transparency_analysis`; semi-transparent regions must not be regenerated as solid fills or deleted as fully transparent.
- Semi-transparent or antialiased regions can carry essential icon shape information; do not fill them into opaque blobs if that removes characteristic features.
- Low-alpha containers can contain same-color high-alpha foreground symbols that are only obvious in the alpha channel. The `ic_dialog_notsave` case must include a low-alpha white rounded card, a high-alpha white download arrow, a red warning badge, and a white exclamation mark; do alpha-threshold segmentation before deterministic drawing.
- The `ic_regenerate` case has the same alpha-layer trap: a low-alpha white circular base contains a high-alpha white circular regenerate arrow plus a solid light-blue sparkle. Do not generate only the blue sparkle and base; inspect the alpha threshold/bbox to find the white regenerate arrow. Its JSON must include centered circular-arrow geometry around the sparkle, open gap/arrow-head position, and failure criteria for off-center arrows.
- Nonstandard/abstract observed forms may be semantically translated into conventional icon shapes when generating variants, as long as `semantic_identity`, status badges, layer order, and fill/alpha constraints are preserved. The `ic_no_network` case is `no_network_wifi`: an unusual white Wi-Fi fan can be rendered as conventional Wi-Fi arcs, but the red circular error badge and white x must remain in front.
- The `ic_5` case must be treated as `five_overlapping_cards`: a centered white outlined hollow rounded rectangle front card with a blue number `5`, plus two semi-transparent white rounded cards peeking from each side behind it. It must not be interpreted as a phone, cloud, capsule, white ears, or a single solid white base.
- Base-container icons must be decomposed into construction layers. The base may be a circle, rounded rectangle, pill, square, freeform mask, or other shape, and its `shape_kind`, corner radius, fill/stroke, opacity, and transparent outside area must be preserved. The `ic_change_photo` case is one circular example: semi-transparent white circular base, white stroked hollow rounded-rectangle photo frame, solid light-blue mountain/image symbol, and light-blue pointed sparkle. Do not simplify it to only a blue triangle/star or swap fill, stroke, and opacity roles.
- Transparent PNG post-processing order is: remove green screen, then resize, then verify alpha and dimensions. Do not apply the reference alpha mask to generated variants because it can hard-crop new layouts into the old mask and create incorrect transparent cutoffs. Do not trim generated transparent bounds, stretch, squeeze, recompose, or otherwise post-process a structurally wrong generation to fake matching the reference size; wrong tile count, tile aspect ratio, tile shape, or key content means regenerate from corrected JSON/prompt.
- For composite/sprite-strip assets, remove green screen from the full original generated image first, then crop/resize tiles from the large transparent PNG. Do not crop or resize green-screen images before alpha extraction.
- The `ic_example_2` case is a `313x74` horizontal sprite strip with exactly 3 equal-size non-square rounded-rectangle cards, not 4 and not square cards. All three cards have the same width, height, aspect ratio, corner radius, top y, and bottom y. Card 1: two-person portrait with blue check badge. Card 2: group selfie with red x badge. Card 3: two-person composition with a foreground close-up person and a smaller distant/full-body person, plus red x badge; the distant person is not a wall frame/background photo and must not become a fourth card.

## Known Environment Constraint

The host `image_generation` tool can hit `TooManyRequests` rate limits. Local Garden/API mode is currently unavailable unless `OPENAI_API_KEY` and `ENABLE_GARDEN_IMAGEGEN` are configured.

## Local Scripts

- `img2-sc/scripts/match_reference_size.ps1`: read or match image dimensions.
- `img2-sc/scripts/remove_green_screen.ps1`: convert chroma key background to alpha.
- `img2-sc/scripts/check_png_transparency.ps1`: verify PNG alpha and transparent pixels; defaults to full-pixel scanning and supports `-SampleStep` only for explicit quick sampling.

