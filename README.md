# Image Generation Skill Workspace

This repository stores readable task context, reusable skill files, helper scripts, and selected final image artifacts for the GPT-Image-2 structured image generation workflow.

It is intended for Git-based handoff across machines or sessions. Do not rely on a Codex chat window as the source of truth.

## Key Files

- `img2-sc/SKILL.md`: main Chinese skill instructions for `img2-sc-all`.
- `img2-sc-app-icon/SKILL.md`: App primary icon and split-layer workflow.
- `img2-sc-flag/SKILL.md`: flag/icon recolor and regeneration workflow.
- `img2-sc-frame/SKILL.md`: frame animation and sprite recolor workflow.
- `img2-sc*/agents/openai.yaml`: agent entry metadata and default prompts.
- `img2-sc*/scripts/`: local PNG post-processing helpers.
- `img2-sc*/references/`: focused reference rules and schemas.
- `test-img/`: selected synced test outputs and diagnostic samples.
- `TASK_CONTEXT.md`: concise current task state and decisions.
- `ARTIFACTS.md`: generated image artifact manifest.

## Workflow Summary

1. Convert user input into structured JSON.
2. Support `text_only`, `reference_only`, and `reference_plus_text` modes.
3. Generate with `image_generation` targeting `gpt-image-2`.
4. For transparent PNGs, generate on green screen, remove green screen first, then resize with transparent background.
5. Verify final size and alpha.

