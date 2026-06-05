# Image Generation Skill Workspace

This repository stores readable task context, reusable skill files, helper scripts, and selected final image artifacts for the GPT-Image-2 structured image generation workflow.

It is intended for Git-based handoff across machines or sessions. Do not rely on a Codex chat window as the source of truth.

## Key Files

- `image2-reference-regenerate/SKILL.md`: main Chinese skill instructions.
- `image2-reference-regenerate/agents/openai.yaml`: agent entry metadata and default prompt.
- `image2-reference-regenerate/scripts/`: local PNG post-processing helpers.
- `TASK_CONTEXT.md`: concise current task state and decisions.
- `ARTIFACTS.md`: generated image artifact manifest.

## Workflow Summary

1. Convert user input into structured JSON.
2. Support `text_only`, `reference_only`, and `reference_plus_text` modes.
3. Generate with `image_generation` targeting `gpt-image-2`.
4. For transparent PNGs, generate on green screen, remove green screen first, then resize with transparent background.
5. Verify final size and alpha.

