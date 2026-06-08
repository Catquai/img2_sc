# Task Context

This repository is the portable task state. Sync this file, `ARTIFACTS.md`, the skill directories, scripts, and selected `test-img` outputs through Git. Do not rely on a Codex/chat window as durable state.

## Workspace

- Current workspace: `E:\WORK\skill\img2_sc`
- Primary branch: `main`
- Skill directories:
  - `img2-sc`
  - `img2-sc-app-icon`
  - `img2-sc-flag`
  - `img2-sc-frame`

## Objective

Maintain Codex skills for structured image generation and deterministic post-processing around `gpt-image-2` workflows.

The skills should support:

- Reference-only image inputs as generation requests by default.
- Structured JSON extraction before generation or deterministic drawing.
- Batch recognition for folders of reference images.
- Consistent output folders and original-name preservation where requested.
- Final images and selected test artifacts under `test-img`.
- Local post-processing for alpha cleanup, size normalization, and validation.

## Current Focus

### `img2-sc-app-icon`

This skill handles mobile App primary icon generation and split-layer outputs.

Current split-layer rule:

- Build structured JSON first.
- Extract `foreground_elements` from JSON and generate a keyed foreground subject variant.
- Remove the key screen locally before resizing.
- Scale the main foreground subject to about 70% on a transparent canvas.
- Output the foreground layer as `512x512` transparent PNG.
- Extract `background_elements` from JSON and generate a new complete opaque background variant.
- Output the background layer as `512x512`.
- Generate the white negative icon from the keyed foreground reference, not from a crude local mask.
- Remove key screen locally and output the white negative icon as `72x72` transparent PNG.

Rejected behavior:

- Do not use local rough masks, hand-drawn polygon mattes, simple reference cutouts, or rotate/scale transforms as substitutes for generated keyed foreground variants.
- Do not deliver placeholder gradients or random circles as designed backgrounds.
- Do not deliver white filled alpha silhouettes as negative icons. They must include readable internal negative-space structure.
- If image generation is blocked or unavailable, stop and report the block rather than delivering local fallback assets.

### `img2-sc-frame`

This skill handles frame recolor/regeneration workflows.

Current rule:

- Automatically recognize reference images inside folders.
- Batch process folder inputs.
- Preserve each reference image's original base name for outputs.
- Use `test-img/frame_recolor_outputs` for generated test outputs.

### `img2-sc-flag`

This skill handles flag/icon regeneration workflows.

Current rule:

- Automatically recognize reference images inside folders.
- Batch process folder inputs.
- Preserve each reference image's original base name for outputs.
- Keep output image-only by default unless metadata is explicitly requested.

## Artifact Policy

Use `ARTIFACTS.md` as the curated manifest of files worth syncing or reviewing. Generated intermediates and failed samples should stay under obvious output/rejected directories and should not be promoted as final artifacts.

Current test output convention:

- Generated image tests: `test-img/`
- App icon layer tests: `test-img/app-icon-layer-output/`
- Frame recolor tests: `test-img/frame_recolor_outputs/`
- White negative icon tests: `test-img/white-negative-icon-output/`
- Rejected or diagnostic samples: keep in a `rejected_*` subdirectory.

## Local Scripts

Important scripts are under the matching skill directories.

`img2-sc-app-icon/scripts` includes:

- `remove_green_screen.ps1`
- `resize_image.ps1`
- `check_png_transparency.ps1`
- `normalize_white_alpha_icon.ps1`
- `check_white_alpha_icon.ps1`
- `compose_layer_pair.ps1`

`resize_image.ps1` supports `-ScalePercent`, used for the app-icon 70% foreground scaling rule.

## Handoff Rule

When resuming work in another thread or machine, read in this order:

1. `README.md`
2. `TASK_CONTEXT.md`
3. `ARTIFACTS.md`
4. The relevant `SKILL.md`
5. The relevant `references/*.md`
6. The relevant `scripts/*.ps1`

The chat window is not the source of truth. The repository is.
