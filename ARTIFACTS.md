# Artifact Manifest

This file lists selected final image outputs that are useful to sync through Git. Large intermediate green-screen images, transparent intermediates, and rejected diagnostic samples should not be promoted as final artifacts.

## Final Outputs

- `test-img/ic_app_manager_40_gpt_image_2_96x96.png`: final app manager icon variant, 96x96.
- `test-img/ic_app_video_40_gpt_image_2_96x96.png`: final video icon variant, 96x96, verified alpha.
- `test-img/ic_compare_auto_regenerated_159x160.png`: compare/auto icon variant.
- `test-img/ic_evaluate_t_regenerated_360x360.png`: evaluation icon variant.
- `test-img/ic_home_app_manager_regenerated_474x288.png`: app manager wide icon variant.
- `test-img/ic_home_loan_regenerated_230x230.png`: home loan icon variant.
- `test-img/ic_home_mortgages_regenerated_230x230.png`: home mortgages icon variant.
- `test-img/ic_r_2_regenerated_144x144.png`: trash icon variant.
- `test-img/ic_setting_translate_regenerated_94x94.png`: translate icon variant.
- `test-img/image_import_38_gpt_image_2_512x512.png`: coin stack icon variant, final resized output.
- `test-img/list_ai_regenerated_72x72.png`: AI list icon variant.
- `test-img/shield_broom_2026_regenerated_273x273.png`: shield/broom/year icon variant.
- `test-img/tag_hot_gpt_image_2_96x48.png`: HOT tag variant, generated through gpt-image-2 flow.
- `test-img/tag_hot_regenerated_96x48.png`: original HOT tag regenerated output.
- `test-img/tag_hot_regenerated_v2_96x48.png`: improved HOT tag regenerated output.

## Excluded Intermediates

- `*_green.png`
- `*_green_*x*.png`
- `*_transparent_large.png`
- Very large raw generation files unless explicitly promoted to a final artifact.
- `test-img/**/rejected_*`: failed or diagnostic samples. Keep them only when useful for debugging, never treat them as valid deliverables.

## Current Diagnostic Notes

- `test-img/app-icon-layer-output/rejected_jsonsplit_bad_mask/`: rejected `img2-sc-app-icon` samples produced by a local rough-mask fallback. These failed because the foreground was not a generated keyed subject variant, the background was a placeholder gradient, and the white negative icon became a filled blob without internal negative-space structure.
- `test-img/app-icon-layer-output/folder_upload/`: current app-icon layer-split diagnostic set for the folder upload icon.
  - `folder_upload_composite_source.png`: accepted composite source used to diagnose foreground consistency.
  - `folder_upload_foreground_keyed_source.png`: keyed foreground generation that exposed the mismatch; it changed the circular upload badge arrow color/style relative to the composite, so it is diagnostic rather than final-approved split output.
  - `folder_upload_foreground_70pct_512.png`: cleaned transparent foreground layer after key-like purple removal; useful for alpha cleanup regression checks.
  - `folder_upload_background_512.png`: opaque generated background layer used for recomposition checks.
  - `folder_upload_composite_preview_512.png`: recomposed preview from current foreground/background layers; useful for validation, but foreground consistency issue means it should not be treated as an approved split of `folder_upload_composite_source.png`.
  - `folder_upload_white_negative_72.png`: final checked 72x72 white negative icon; pure white visible pixels, true alpha, no visible edge noise.
  - `folder_upload_white_negative_preview_dark_pillow.png`: dark preview for visually inspecting the 72x72 white negative icon.
  - `folder_upload_white_negative_normalized_edge_clean.png`: cleaned normalized negative source after removing edge-connected white noise, retained as a small diagnostic artifact.
  - `folder_upload_white_negative_72_zoom8.png`: enlarged nearest-neighbor preview for reviewing internal negative-space structure.

Latest folder-upload conclusion:

- The foreground mismatch happened before post-processing: `foreground_keyed_source` was an independent second generation rather than a visual-lock recreation of `composite_source`.
- `img2-sc-app-icon` now requires `foreground_visual_lock` whenever an accepted `composite_source` exists, so the foreground pass must match the composite foreground's color, badge arrow, direction, card contents, lighting, and overlap.
- `check_white_alpha_icon.ps1` now reports `edge_visible_pixels` and fails by default when white negative icons contain visible edge-touching noise.

## Git Sync Rule

Sync human-readable state and useful artifacts through Git:

- `TASK_CONTEXT.md`
- `ARTIFACTS.md`
- `README.md`
- `img2-sc*/SKILL.md`
- `img2-sc*/references/*.md`
- `img2-sc*/scripts/*.ps1`
- `img2-sc*/scripts/*.py`
- selected final images in `test-img/`

Do not try to sync a Codex/chat window as task state.
