# Artifact Manifest

This file lists selected final image outputs that are useful to sync through Git. Large intermediate green-screen images and large transparent intermediates are excluded by `.gitignore`.

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
