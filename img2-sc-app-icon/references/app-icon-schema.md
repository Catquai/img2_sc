# App Icon Structured JSON

生成前使用以下结构。删除不适用字段，但不要省略关键约束。

```json
{
  "input_mode": "text_only | reference_only | reference_plus_text",
  "input_image_role": {
    "role": "reference_image | composite_source | foreground_source_image | background_source_image",
    "decision_reason": "",
    "explicit_user_phrase": "",
    "role_priority_rule": "explicit_layer_role > explicit_locked_split_request > accepted_generation_continuation > ordinary_reference",
    "ordinary_reference_is_default": true,
    "forbid_auto_composite_source_from_complete_icon_appearance": true,
    "multiple_images_must_each_have_role": true,
    "reference_image_flow": "extract_structured_json_then_generate_new_foreground_variant_and_new_complete_background_variant",
    "composite_source_flow": "extract_foreground_visual_lock_then_recreate_same_foreground_on_key_screen_and_inpaint_background",
    "foreground_source_image_flow": "do_not_regenerate_subject; clean_key_or_alpha_then_resize_and_generate_negative_if_enabled",
    "background_source_image_flow": "do_not_regenerate_background_subject_content; flatten_or_repair_then_resize"
  },
  "canvas": {
    "aspect_ratio": "1:1",
    "source_width_px": null,
    "source_height_px": null,
    "shape": "square | rounded_square | circle | transparent_freeform",
    "corner_radius_px": null,
    "corner_radius_percent": null,
    "mask_baked_into_image": false,
    "transparent_outside_shape": false,
    "safe_area_percent": {"left": 12, "top": 12, "right": 12, "bottom": 12},
    "background": {
      "type": "solid | gradient | illustrated | transparent | green_screen",
      "colors": [],
      "details": []
    }
  },
  "platform_intent": {
    "platform": "ios | android | cross_platform | unspecified",
    "usage": "primary_app_icon | launcher_icon | store_icon | master_artwork",
    "platform_applies_mask": true
  },
  "app_identity": {
    "concept": "",
    "primary_symbol": "",
    "recognition_at_small_size": "",
    "must_not_resemble": []
  },
  "style": {
    "family": "flat_gradient | soft_gradient | soft_2_5d | soft_3d | skeuomorphic | illustrated | other",
    "lighting": "",
    "materials": [],
    "edge_treatment": "",
    "shadow": "",
    "detail_level": "low | medium | high",
    "forbidden_styles": []
  },
  "elements": [
    {
      "id": "primary_symbol",
      "identity": "",
      "bounds_percent": {"x": 20, "y": 20, "w": 60, "h": 60},
      "layer": 2,
      "orientation": "",
      "required_traits": [],
      "appearance": {},
      "completeness": "fully visible"
    }
  ],
  "relationships": [],
  "composition_variation": {
    "subject_structure": "single_primary_element | multiple_elements",
    "randomization": {
      "required_every_generation": true,
      "seed_or_run_id": "",
      "sampled_rotation_degrees": {},
      "sampled_scale_delta": {},
      "sampled_position_shift_percent": {},
      "sampled_overlap_change": "",
      "sampled_color_shift": {},
      "minimum_changed_dimensions": 3,
      "changed_dimensions": ["rotation", "scale", "position", "shape", "color", "decorative_layout", "background_element_family", "background_palette"],
      "must_differ_from_reference": true,
      "must_differ_from_previous_generation": true,
      "preserve_primary_object_recognition": true,
      "forbid_identity_breaking_container_deformation": true,
      "prefer_non_destructive_variation_dimensions": ["composition_layout", "arrow_path_and_placement", "card_count_and_arrangement", "overlap_order", "center_of_mass_region", "subject_colorway", "accent_color_palette", "background_element_family", "background_colorway"],
      "folder_upload_container_type": "flat_folder",
      "container_type_extraction_rule": "write exactly one concrete value from the reference; do not write alternatives such as flat_folder | deep_tray_box, folder/tray, folder or container, or maybe",
      "resolved_primary_container": {
        "type": "flat_folder",
        "prompt_phrase": "flat yellow file folder with front panel, rear flap, angled open mouth, shallow pocket relationship, and right folded side flap",
        "required_traits": ["flat folder front panel", "rear flap/back panel", "angled open mouth", "shallow pocket relationship", "folder tab or folded side flap if visible", "readable flat folder silhouette", "readable upward upload arrow", "media/document cards remain readable"],
        "forbidden_traits": ["box frame", "deep tray", "storage bin", "basket", "side-wall container", "thick rectangular rim", "visible high side walls", "deep inner cavity", "thin vertical box", "abstract pillar", "generic paper box"]
      },
      "reference_flat_folder_prompt": "flat yellow file folder with front panel, rear flap, angled open mouth, shallow pocket relationship, and right folded side flap",
      "flat_folder_requirements": ["flat folder front panel", "rear flap/back panel", "angled open mouth", "shallow pocket relationship", "folder tab or folded side flap if visible", "readable flat folder silhouette", "readable upward upload arrow", "media/document cards remain readable"],
      "deep_tray_box_requirements": ["use only if the reference actually shows a deep tray or box", "open pocket or tray front lip", "visible high side walls", "visible inner cavity", "readable tray/box silhouette", "readable upward upload arrow", "media/document cards remain readable"],
      "flat_folder_forbidden_shapes": ["box frame", "deep tray", "storage bin", "basket", "side-wall container", "thick rectangular rim", "thin vertical box", "abstract pillar", "generic paper box"]
    },
    "single_primary_element_policy": {
      "apply_when": "one dominant subject or one merged symbol",
      "shape_variation": "noticeable but identity-preserving",
      "pose_variation": "noticeable random direction-angle rotation or perspective change",
      "rotation_delta_degrees": "18-42",
      "scale_delta": "0.78-1.25",
      "position_shift": "6-16 percent inside safe area",
      "color_variation": "noticeable but harmonious"
    },
    "multiple_elements_policy": {
      "apply_when": "two or more meaningful visual elements",
      "main_element_preservation": ["identity", "required traits", "semantic orientation", "small-size readability"],
      "position_variation": "visibly reorganize relative positions, spacing, overlap, and center of mass while preserving hierarchy",
      "rotation_delta_degrees": {"main_element": "12-32", "secondary_elements": "18-48"},
      "scale_delta": "0.72-1.28",
      "minimum_distance_or_overlap_change_percent": 15,
      "color_variation": "vary main and secondary palettes without breaking semantic colors"
    },
    "forbidden": ["identity loss", "semantic direction reversal", "identity-breaking deformation", "folder/tray becomes a thin vertical box or abstract pillar", "important-part occlusion", "safe-area overflow", "main-secondary hierarchy confusion"]
  },
  "pose_variation": {
    "apply_in_reference_only": true,
    "semantic_orientation": "",
    "reference_visual_pose": "",
    "target_visual_pose": "",
    "rotation_delta_degrees": "12-32",
    "perspective_change": "subtle | moderate",
    "allowed": ["planar rotation", "slight pitch", "slight yaw", "three-quarter view"],
    "forbidden": ["semantic direction reversal", "extreme foreshortening", "identity-breaking deformation", "important-part occlusion"]
  },
  "accent_color_variation": {
    "apply_in_reference_only": true,
    "primary_colors": [],
    "protected_colors": [],
    "accent_colors": [],
    "target_accent_colors": [],
    "variation_strength": "subtle | moderate",
    "adjustable_regions": ["grip cap", "edge highlight", "inner shadow", "small badge", "secondary trim"],
    "preserve": ["primary color identity", "material hierarchy", "highlight-shadow ordering", "small-size contrast"],
    "forbidden": ["primary color replacement", "brand color drift", "semantic status color change", "accent color dominating the subject"]
  },
  "decorative_variation": {
    "apply_in_reference_only": true,
    "decorative_elements": ["sparkles", "light dots", "particles", "small badges", "edge highlights", "background glints", "shine fragments"],
    "randomization": {
      "required_every_generation": true,
      "sampled_count_delta": "",
      "sampled_position_shift_percent": {},
      "sampled_scale_delta": {},
      "sampled_rotation_degrees": {},
      "sampled_opacity_delta": {},
      "sampled_brightness_delta": {},
      "sampled_color_shift": {},
      "sampled_shape_detail_change": ""
    },
    "allowed_changes": ["count", "position", "size", "rotation angle", "opacity", "brightness", "color", "shape detail", "layer order within decorative group"],
    "preserve": ["secondary visual role", "style consistency", "small-size clarity", "main element readability"],
    "forbidden": ["cover main element", "become primary focal point", "add text", "change semantic identity", "create clutter", "introduce misleading status symbol"]
  },
  "invariants": [],
  "allowed_changes": [],
  "forbidden_changes": [],
  "failure_criteria": [],
  "layer_split": {
    "enabled": true,
    "default_enabled_unless_composite_only_requested": true,
    "source_policy": "derive_layers_from_structured_json",
    "reference_image": null,
    "reference_image_is_not_composite_source_by_default": true,
    "composite_source": null,
    "composite_source_allowed_only_when_user_accepts_or_requests_locked_split": true,
    "direct_model_composite_generation_allowed": false,
    "local_composite_full_subject_preview_required": true,
    "local_70pct_composite_preview_required": false,
    "default_generation_order": [
      "extract_structured_json_prompt_from_image",
      "generate_foreground_adaptive_chroma_key_from_json_foreground_elements",
      "generate_background_from_json_background_elements_and_resize_512",
      "remove_chroma_key_locally_to_transparent_foreground",
      "generate_white_negative_from_keyed_foreground_and_resize_72",
      "locally_compose_unscaled_foreground_over_background_to_512",
      "scale_transparent_foreground_subject_to_70_percent_then_canvas_to_512"
    ],
    "foreground_source": "structured_json.foreground_elements",
    "background_source": "structured_json.background_elements",
    "consistency_target": "accepted_composite | independent_layer_variant",
    "default_consistency_target_when_composite_exists": "accepted_composite",
    "forbid_regenerated_similar_foreground": false,
    "key_color": "#ff00ff",
    "key_color_reason": "selected for maximum distance from all foreground opaque and semi-transparent colors",
    "key_color_candidates": ["#00ff00", "#ff00ff", "#0000ff", "#ff0000", "#ffff00", "#00ffff"],
    "key_color_policy": {
      "green_screen_means_chroma_key_unless_user_explicitly_requires_literal_green": true,
      "choose_max_color_distance_from_foreground": true,
      "forbid_literal_green_when_subject_contains_green_or_cyan_green": true,
      "recommended_for_blue_or_cyan_subject": "#ff00ff",
      "recommended_for_green_or_cyan_green_subject": "#ff00ff | #0000ff | #ffff00",
      "literal_green_allowed_only_when_no_large_foreground_green_overlap": true
    },
    "extraction_strategy": "adaptive_chroma_key | provided_alpha_mask",
    "forbidden_extraction_strategy": "local_segmentation_matte_from_complete_composite | rough_mask_from_reference | threshold_cutout_from_reference | connected_component_cutout_from_reference | hand_drawn_polygon_matte",
    "foreground_derivation": {
      "source": "structured_json.foreground_elements",
      "method": "generate_subject_variant_on_chroma_key",
      "visual_lock_source": "composite_source | structured_json_only",
      "forbid_new_foreground_variant_when_composite_source_exists": true,
      "must_generate_visible_variant_when_only_reference_image_exists": true,
      "fail_if_only_background_replaced_in_reference_only": true,
      "foreground_visual_lock": {
        "required_when_composite_source_exists": true,
        "locked_overall_palette": [],
        "locked_folder_or_container_color": "",
        "locked_inner_surface_color": "",
        "locked_upload_arrow_color": "",
        "locked_upload_arrow_direction": "",
        "locked_circular_badge_color": "",
        "locked_card_colors_and_contents": [],
        "locked_card_angles": [],
        "locked_overlap_order": [],
        "locked_lighting_direction": "",
        "locked_material_highlights": ""
      },
      "verify_against_composite_foreground": true,
      "fail_if_color_or_direction_differs_from_composite": true,
      "forbid_local_rough_mask_fallback": true,
      "forbid_reference_cutout_as_generation_substitute": true,
      "forbid_local_layer_creation_from_complete_composite": true,
      "local_processing_allowed_only_for": ["remove_key_from_generated_or_user_provided_keyed_source", "clean_user_provided_alpha", "resize", "normalize_white_alpha", "flatten_background", "compose_preview", "validate_pixels"],
      "complete_composite_input_local_processing_allowed_only_for": ["dimension_reading", "color_sampling", "visual_lock_analysis", "verification"],
      "new_transparency_requires_keyed_source": true,
      "forbid_key_color_inside_subject": true,
      "key_color_must_not_be_subject_material": true,
      "remove_edge_connected_key_color_by_default": true,
      "remove_disconnected_key_like_pixels_only_when_declared_transparent": true,
      "transparent_disconnected_regions": {
        "transparent_negative_regions": [],
        "true_cutout_regions": [],
        "background_gaps_between_foreground_parts": []
      },
      "preserve_disconnected_key_like_pixels_unless_declared_transparent": true,
      "preserve_subject_internal_key_like_material_by_default": true,
      "forbid_auto_deleting_undeclared_internal_key_like_regions": true,
      "fill_subject_internal_holes_before_resize": true,
      "distinguish_inter_element_background_gaps_from_subject_internal_material": true,
      "fail_if_visible_key_like_pixels_remain": true,
      "work_at_original_or_higher_resolution": true,
      "keyed_intermediate": null,
      "alpha_output_original_size": null,
      "alpha_output_before_scale": null,
      "main_element_scale_percent_after_key_removal": 70,
      "final_foreground_size_px": [512, 512],
      "verify_true_alpha": true
    },
    "background_derivation": {
      "source": "structured_json.background_elements",
      "method": "generate_new_background_variant_from_json",
      "forbid_placeholder_gradient": true,
      "must_generate_visible_background_variant_in_reference_only": true,
      "minimum_changed_background_dimensions": 3,
      "changed_background_dimensions": ["radial_glow_position", "gradient_center", "texture_or_dot_wave_path", "particle_distribution", "light_band_direction", "local_hue_balance", "depth_rhythm"],
      "fail_if_reference_background_is_only_slightly_shifted_or_recolored": true,
      "work_at_original_or_higher_resolution": true,
      "opaque_output_original_size": null,
      "final_background_size_px": [512, 512],
      "verify_fully_opaque": true
    },
    "foreground_elements": [],
    "background_elements": [],
    "foreground_exclusions": [],
    "background_exclusions": [],
    "background_fill_strategy": "continue gradients, textures, atmosphere, and hidden scenery behind the removed foreground",
    "shared_constraints": ["same canvas size", "same alignment", "same color space", "same lighting direction"]
  },
  "white_negative_icon": {
    "enabled": true,
    "default_enabled_unless_explicitly_disabled": true,
    "source": "foreground_keyed_source",
    "source_must_be_derived_from_composite_foreground": false,
    "source_must_be_generated_from_keyed_foreground": true,
    "actual_foreground_image_input_required": true,
    "forbid_semantic_only_negative_generation": true,
    "forbid_reusing_previous_negative_template": true,
    "fill_color": "#ffffff",
    "background": "transparent",
    "keyed_intermediate": null,
    "final_size_px": [72, 72],
    "resize_policy": "resize_full_canvas_to_final_size",
    "forbid_trim_and_subject_shrink": true,
    "forbid_scale_percent_after_normalization": true,
    "verify_true_alpha": true,
    "verify_visible_pixels_pure_white": true,
    "forbid_solid_alpha_silhouette_only": true,
    "require_internal_negative_space": true,
    "white_fill_regions": [],
    "transparent_negative_regions": [],
    "true_cutout_regions": [],
    "background_gaps_between_foreground_parts": [],
    "identity_features_to_preserve": [],
    "simplifiable_details": [],
    "minimum_negative_space_width_percent": 2,
    "forbidden": ["stroke", "outline", "shadow", "gradient", "gray", "color", "glow", "texture", "3d material", "solid blob without required negative details"]
  },
  "output": {
    "mode": "foreground_background_pair | composite",
    "default_mode": "foreground_background_pair",
    "final_width_px": 512,
    "final_height_px": 512,
    "format": "png",
    "do_not_generate_final_composite_directly": true,
    "final_composite_must_be_local_layer_composition": true,
    "requires_true_alpha": false,
    "composite_background_policy": {
      "fill_entire_canvas": true,
      "opaque_by_default": true,
      "transparent_only_if_explicitly_requested": true,
      "forbidden": ["transparent corners unless requested", "transparent holes", "blank margins", "unpainted canvas areas"]
    },
    "fit": "cover",
    "files": {
      "composite_source": null,
      "composite": null,
      "foreground_keyed_source": null,
      "foreground_green_screen": null,
      "foreground_alpha_original_png": null,
      "foreground_alpha_png": null,
      "foreground_alpha_70pct_512_png": null,
      "background_png": null,
      "white_negative_icon_png": null,
      "composite_full_subject_preview": null
    }
  }
}
```

## Reference Analysis Rules

- When the user provides only a reference image, image attachment, image path, or `Files mentioned by the user` image context, treat it as a `reference_only` generation request by default. Extract JSON, then generate a new App icon variant. Do not stop at analysis, list options, or ask what to do unless the user explicitly requested analysis only or generation is blocked.
- The original user-provided reference image is `reference_image`, not `composite_source`. Do not enable visual-lock splitting or "only replace background with key color" from the original reference unless the user explicitly says to lock that exact image, split that accepted image, or keep the subject unchanged.
- Before any generation or split, classify every supplied image into exactly one `input_image_role`. A complete-looking icon is still `reference_image` by default. Use `composite_source` only for explicit locked-split requests or an accepted generated result that the user asks to continue splitting. Use `foreground_source_image` / `background_source_image` only when the user names the image as a layer or the file is already clearly a keyed/transparent foreground or background layer.
- Resolve helper script paths relative to the `img2-sc-app-icon` skill directory, not the current shell directory. For example, run `img2-sc-app-icon/scripts/match_reference_size.ps1` when the workspace root is the repository root.
- If the reference is WebP or another format that `System.Drawing` cannot decode, use ImageMagick metadata (`magick identify`) or another structured image library to record dimensions. Do not treat a local metadata-read failure as a generation blocker when the image can still be visually inspected.
- Distinguish semantic identity from observed shape. Record both when the reference uses an abstract symbol.
- Record exact count and orientation of meaningful objects. Separate immutable `semantic_orientation` from changeable `visual_pose`.
- Classify the composition as `single_primary_element` or `multiple_elements` before generation. For a single primary element, create a clearly different but recognizable shape, pose, random direction-angle rotation, scale, center of mass, and color treatment. For multiple elements, preserve the main element identity while visibly reorganizing element positions, angles, scale relationships, overlap order, spacing, and colors.
- For repeated `text_only` requests with the same or highly similar prompt, or when the user says the change is too small, treat the next generation as a new variant and sample fresh `composition_variation.randomization`. Change at least three visible dimensions: subject view angle or rotation, main element position or center of mass, file/card count or angles, arrow path/placement/scale, subject or background colorway, background element family, lighting center, or decorative layout.
- For `text_only + output.mode: composite`, do not reuse a fixed centered template. The image prompt must explicitly state the sampled variation parameters for this generation. Avoid repeating the previous bbox layout, arrow path, file arrangement, subject pose, and background composition family.
- For `text_only` folder icons, when the user asks for a standard/simple/open folder and does not ask for a tray, box, pouch, basket, or storage container, set the folder identity to `simple_flat_standard_file_folder` or `standard_open_file_folder`. Use the exact prompt phrase `standard tabbed file folder with front flap, back sheet, open top edge, thin paper-folder layers, visible inner fold, and classic folder tab`. Do not use `folder pocket`, `folder pouch`, `open tray`, `box`, `storage container`, `basket`, `deep cavity`, or `thick side walls` as folder identity or visual structure terms.
- Every `reference_only` generation must sample fresh random variation parameters and record them in `composition_variation.randomization`. At least three independent variation dimensions must change visibly. Do not reuse a fixed template pose, the reference pose, the reference element placement, or the previous generation's parameter set.
- Repeated `reference_only` generations must differ from the previous output without breaking the primary object's semantic identity. Prefer non-destructive dimensions such as composition layout, arrow path, card arrangement, overlap order, subject colorway, accent colors, background element family, background palette, and background layout before changing the core container silhouette.
- Identify decorative accents and record them in `decorative_variation`. Accents include sparkles, light dots, particles, small badges, local highlights, background glints, shine fragments, and non-semantic ornamentation.
- Decorative accents should vary randomly in every generation. Change count, position, scale, rotation, opacity, brightness, color, or small shape details while keeping them visually secondary and style-consistent.
- During reference analysis, assign every visible element to foreground or background before any split generation. Write this assignment into `layer_split.foreground_elements`, `layer_split.background_elements`, `foreground_exclusions`, and `background_exclusions`.
- The final foreground and background layers must obey the JSON element assignment. The same sparkle, bubble, glint, sweep, shadow, badge, primary part, or secondary part must not appear in both final layers. If an accent is assigned to foreground, the background must exclude it; if it is assigned to background, the foreground must exclude it.
- Treat background, primary symbol, badge, text, highlight and shadow as separate layers.
- Record transparent corners separately from internal semi-transparent materials.
- Preserve the reference's mask only when it is visibly part of the asset or explicitly requested.
- In `reference_only`, preserve identity, hierarchy, style family and mask while creating a visibly new variant. Do not preserve the reference composition by default. Single primary elements must usually use stronger random direction-angle rotation, shape/pose variation, scale change, center shift, and color variation than a minor pose tweak. Multiple-element icons should reorganize relative positions, angles, overlap order, scale, spacing, and colors as long as the main element remains readable.
- For folder/upload icons, infer exactly one concrete container type from visual evidence and write only that value into JSON. Do not write alternatives such as `flat_folder | deep_tray_box`, `folder/tray`, `folder or container`, `open folder or tray`, or `maybe`. If the reference is a flat manila-style folder, the JSON must set `resolved_primary_container.type` to `flat_folder` and use the exact flat-folder semantic prompt: `flat yellow file folder with front panel, rear flap, angled open mouth, shallow pocket relationship, and right folded side flap`. Do not describe a flat folder as a deep tray, storage bin, basket, side-wall container, thick rectangular rim, generic box, visible high side walls, or deep inner cavity. Use tray/container/side-wall/interior-cavity language only when the reference actually shows a deep tray or box. Before writing a foreground prompt, copy `resolved_primary_container.type`, `prompt_phrase`, `required_traits`, and `forbidden_traits` verbatim into the prompt. If silhouette change would reduce recognizability, use composition, color, arrow, card, and background changes instead.
- In `reference_only`, a keyed foreground pass that only removes/replaces the original background is a failure. The keyed foreground must itself be the new variant layer unless a real `composite_source` was explicitly selected.
- Treat "green screen" as a generic chroma-key request unless the user explicitly asks for literal green. Select the key color by maximum distance from the generated foreground colors; if the foreground contains green or cyan-green materials, do not use literal green as the key color.
- New transparency must come from a keyed source or a provided alpha source. If the source image is a complete composite/reference image, local segmentation, thresholding, connected components, hand-drawn mattes, or cutouts may be used only for analysis/verification, never as the delivered foreground, background, negative icon, or transparent PNG source. If no generated keyed source or provided alpha/keyed source exists, stop and generate one or report that the task is blocked.
- For local key removal, remove edge-connected key-color regions by default. Disconnected key-like regions are removed only when the structured JSON declares them as `transparent_negative_regions`, `true_cutout_regions`, or `background_gaps_between_foreground_parts`. Undeclared internal key-like regions must be preserved or fixed in the keyed source; do not auto-delete them.
- In `reference_only`, the background layer must also be visibly varied while preserving the same background style family. Change at least three dimensions such as glow position, gradient center, texture/dot-wave path, particle distribution, light-band direction, local hue balance, or depth rhythm.
- Prefer approximately `18-42°` planar rotation for single primary elements, or `12-32°` for main elements and `18-48°` for secondary elements in multi-element compositions. Use smaller changes only when the subject is already diagonal, strict geometry, or near the safe-area boundary, and compensate with stronger scale, position, color, shape, or decoration changes.
- Preserve semantic orientation and functional relationships. Do not reverse directional symbols, vehicle travel direction, animal head/tail direction, tool assembly, object stacking or front/back layer meaning.
- Do not perspective-warp text, numbers, brand marks, flags, arrows, strict symmetric badges or precision geometry unless the user explicitly requests it.
- Separate `primary_colors`, `accent_colors` and `protected_colors`. Primary colors define the subject identity; accent colors support local contrast and detail; protected colors must remain exact or perceptually unchanged.
- In `reference_only`, moderately vary secondary accent colors by default. Suitable targets include grip caps, trim, small badges, inner surfaces, edge highlights and secondary shadows.
- Keep accent changes harmonious with the original palette and material. Preserve brightness ordering between highlight, base and shadow, and ensure the subject remains readable at small size.
- Never let accent colors replace or overpower the primary color identity. Do not change brand colors, flag colors, traffic/status colors or user-specified exact colors without explicit permission.
- For `output.mode: composite`, the background fills the entire 1:1 canvas and is opaque by default. Transparent backgrounds, transparent corners, transparent holes, or blank margins are allowed only when the user explicitly requests transparent PNG or the reference/workflow requires a true alpha asset.
- For `output.mode: composite`, unless the user explicitly requests rounded corners or a baked app-icon mask, the final image must use a full square canvas with sharp 90-degree image corners. The background must reach all four edges. Do not bake rounded corners, a rounded-square tile, iOS mask, app-icon mockup, outer margin, or transparent/light corner frame into the image.
- When a prompt uses app-icon words such as `mobile app icon`, `launcher icon`, `store icon`, or `app icon master artwork`, include an explicit canvas negative constraint: `full square canvas with sharp 90-degree image corners; background reaches all four edges; do not bake rounded corners, rounded-square tile, iOS mask, app-icon mockup, outer margin, or transparent corners`.

## Generation Prompt Reliability

- Keep the first image-generation prompt focused on the structured JSON's essential constraints: app identity, canvas/output, primary elements, relationships, sampled variation parameters, invariants, and failure criteria. Avoid pasting the entire schema or long explanatory checklists into the model call.
- If a long structured prompt fails at the image-generation service layer, retry once with a compact prompt that still names `gpt-image-2`, preserves the same app identity, element relationships, sampled randomization, output size, and hard omissions. Do not silently drop identity, safe-area, opacity, background-fill, or no-text/no-mockup constraints.
- When falling back to a compact prompt, keep the structured JSON as the local source of truth for verification and report that the generation used a shortened prompt.

## Foreground And Background Pair

- Enable `layer_split` by default for normal app-icon generation unless the user explicitly requests composite-only output.
- Do not ask the image model to generate the final composite directly in the default flow. Generate separate passes from the structured JSON, then create only the unscaled-subject composite check image locally from the transparent foreground and opaque background.
- The default order is fixed: extract structured JSON, generate keyed foreground from foreground elements, generate and resize opaque background from background elements, remove key color locally, generate the white negative icon from `foreground_keyed_source` and resize the whole canvas to `72x72`, locally compose the unscaled transparent foreground over the background as `composite_full_subject_preview`, then scale the transparent foreground subject to `70%` and normalize the foreground canvas to `512x512`. Do not generate a 70% foreground composite preview by default.
- For split output, derive separate generation passes from the structured JSON. Extract primary foreground elements into a keyed subject-variant pass, and extract background information into a background pass.
- Do not use local rough masks, threshold masks, connected-component cutouts, hand-drawn polygon mattes, simple reference-image cutouts, or local rotate/scale transforms as substitutes for a generated keyed foreground, repaired background, or white negative icon. Local image processing is allowed only after a generated/provided keyed source or provided alpha source exists, and only for key removal, alpha cleanup, resizing, normalization, composition, and validation. If the image generation tool is unavailable, stop and report that generation is blocked instead of delivering a fallback asset.
- Assign every visible element to foreground or background before generation. Keep only the primary subject and subject-attached effects in the foreground.
- Before generation, verify that `foreground_elements` and `background_elements` do not contain duplicate element identities. Fix the JSON first if the same element appears in both lists.
- Generate the foreground elements on a uniform adaptive chroma-key background, then locally remove the key screen to create a true-alpha PNG. Do not default blindly to green unless the user explicitly asks for green screen.
- The keyed foreground must be visually clean: no original-background chunks, rectangular color blocks, hard polygon-mask edges, missing handles/edges/critical parts, checkerboard, or discontinuous alpha boundaries.
- The key color may appear only outside the declared foreground subject. It must not appear as a placeholder inside subject holes, folder openings, card gaps, badge grooves, tool slots, or other interior regions unless those regions are explicitly declared as true transparent negative space in the JSON.
- Choose the key color with maximum distance from primary colors, accent colors, highlights, glows, shadows and particles. Prefer `#ff00ff` for blue/cyan foregrounds, `#00ff00` for purple/red/warm foregrounds, and avoid any key color present in semi-transparent effects.
- If a blue/cyan foreground also contains purple or magenta accents, prefer yellow `#ffff00` over magenta.
- Generate the background from the structured JSON background description as a new complete fully opaque background variant. Do not include the primary subject, subject ghosting, subject-shaped empty patches, or duplicated foreground decoration.
- The background must be a designed App icon background consistent with the JSON style, palette, lighting, and decorative rules. Reject placeholder gradients, random circles, blank color fields, or generic backgrounds that are not grounded in the JSON.
- Default final layer dimensions to `512x512` unless the user explicitly requests another size.
- Foreground processing order is mandatory: generate keyed foreground from JSON at original or higher work resolution, remove key screen, reconstruct/decontaminate semi-transparent pixels, verify alpha, scale the main element to 70% on a transparent canvas, then resize/normalize the transparent PNG to `512x512`. Never resize the green-screen/keyed source before keying.
- Background processing order is mandatory: generate a complete opaque background variant at original or higher work resolution, verify the background is fully opaque, then resize to `512x512`.
- Before removing the key screen, decide which foreground regions are meant to be opaque. Solid or glassy app-icon subjects such as shields, brushes, bristles, handles, badges and main symbols usually keep their rendered opacity; do not globally turn the whole subject semi-transparent just because it was generated on a key screen.
- Use alpha reconstruction and reverse key-screen compositing only for regions that are genuinely semi-transparent: soft glows, white shine, antialiased edges, sweep highlights and shadows. Set hidden RGB to zero for fully transparent and extremely low-alpha pixels before resizing; reject visible key-color fringes.
- When the subject should stay opaque and only star/sparkle/white-glow edges contain key-color contamination, prefer connected-background key removal: flood-fill key-colored pixels connected to the canvas edges, set only that connected background transparent, keep non-connected subject pixels opaque, then apply local despill to visible magenta/green fringes. Pillow or an equivalent structured image library is preferred for this case.
- After key removal, inspect subject interiors before resizing. If folder interiors, card-behind gaps, arrow inner regions, badge grooves, or other non-transparent subject areas become transparent holes because key color was removed, repair/fill them at the original resolution before scaling. Do not deliver foreground layers with unintended internal transparency.
- Move non-subject-attached translucent fog, environmental glow, trails and particles to the background whenever possible. This is more reliable than color-key extraction.
- Keep both layers at exactly the same pixel dimensions and alignment. Do not recenter, rescale or rotate the subject between passes.
- Exclude subject silhouettes, ghosting, duplicate foreground decoration and subject-specific highlights from the background.
- When a contact shadow must remain fixed to the scene, place it in the background. When a glow or shadow must travel with the subject, place it in the foreground and preserve a soft alpha edge.

## White Negative Icon

- Use the actual `foreground_keyed_source` image file as the visual reference input. Generate a minimal pure-white negative-space icon on a uniform key screen, then locally remove the key screen to create transparent PNG output.
- Do not generate the white negative icon from semantic description alone, conversation memory, a previously generated negative icon, or a reused folder/upload template. If the current image generation tool cannot attach the actual `foreground_keyed_source` image as an input/reference, do not call the model for this pass; use local alpha/vector processing or report that the negative icon is blocked.
- Before generation, write a `negative_visual_lock` from the actual `foreground_keyed_source` image: outer silhouette, card count, card angles, arrow position, resolved container shape, overlap order, and required internal cutouts. Do not build the lock from `foreground_alpha_png` or semantic text. The generated negative keyed source must match that lock.
- Do not make the white negative icon by simply filling the foreground alpha silhouette with white. It must include readable internal transparent negative-space structures that preserve identity at `72x72`.
- The white negative icon must preserve recognizable internal identity features. For shield-plus-cleaning-tool icons, preserve features such as shield inner/outer separation, brush head/handle separation, bristle group separation, or equivalent transparent negative-space structures.
- Preserve the subject's outer silhouette and identity-defining parts while simplifying decorative details.
- Express internal structure only with transparent negative space. Use negative holes for openings, component separation and essential internal landmarks.
- Keep every visible pixel pure white. Preserve antialiased alpha edges, but do not use gray RGB values for antialiasing.
- Reject strokes, outlines, shadows, gradients, colors, glow, texture and 3D volume.
- Ensure negative spaces remain open and readable after resizing. Merge or remove fragile micro-details.
- Do not treat color normalization as negative-space design. First generate or construct the required negative alpha regions; only then normalize all visible RGB to white.
- Final white negative icon must be `72x72`, have true transparent background, and pass pure-white visible-pixel validation.
- The final white negative icon is produced by resizing the whole normalized image canvas to `72x72`. Do not trim the subject, thumbnail it, apply scale-percent reduction, or add extra margins after normalization. If the subject is too large or too small, regenerate or renormalize the source canvas instead of shrinking the main element during final output.

## Small-Size Readability

Reject the result when:

- The primary symbol cannot be identified at approximately 48px.
- Thin details disappear or merge.
- Background contrast is too weak.
- Composite output has transparent areas, blank margins, unpainted canvas regions, or a background that does not fill the entire canvas when transparency was not explicitly requested.
- Composite output bakes in rounded background corners, a rounded-square tile, iOS-style mask, app-icon mockup frame, outer margin, or corner cutouts when rounded corners were not explicitly requested.
- Several elements compete as equal focal points.
- Important parts cross the safe area or are clipped.
- A `reference_only` result copies the reference pose, silhouette, overlap, center of mass, or element placement too closely without meaningful changes in at least three independent dimensions.
- A repeated `reference_only` generation reuses the same angle, scale, position, overlap, and color parameters instead of sampling a fresh variation.
- A repeated `text_only` or `text_only + composite` generation reuses the same subject view, file/card arrangement, arrow path/placement, center of mass, and background composition family instead of sampling a fresh variation.
- A composite-only prompt omits the sampled variation parameters or repeats the previous bbox/layout template after the user asks for more change.
- A `text_only` standard/simple/open folder prompt describes the main folder as `folder pocket`, `folder pouch`, tray, box, storage container, basket, deep cavity, or thick side-wall structure when the user did not request those container types.
- A repeated `reference_only` generation achieves difference mainly by deforming the resolved primary container until it is no longer recognizable instead of using composition, color, foreground relationship, or background variation.
- A `reference_only` result only changes rendering quality, lighting, minor highlights, small decorative dots, or a subtle accent color while keeping the same layout and subject pose.
- A `reference_only` keyed foreground merely replaces the reference image background with chroma key while preserving the same subject pose, element placement, overlap, and scale.
- A `reference_only` background layer merely copies the reference background layout with tiny color shifts, small translation, or a few extra random particles.
- A keyed foreground uses literal green while the foreground subject contains green/cyan-green material and a safer key color was available.
- Local key removal deletes disconnected internal key-like subject material that was not declared as transparent negative space, true cutout, or inter-element background gap.
- Local key removal preserves disconnected key-like pixels that were explicitly declared as transparent negative space, true cutout, or inter-element background gap.
- Rotation or perspective makes the subject distorted, hides identity-defining parts, reverses semantic direction or breaks relationships.
- A `flat_folder` upload reference result turns the folder into a box frame, deep tray, storage bin, basket, side-wall container, thick rectangular rim, thin vertical holder, abstract column, generic box, or otherwise loses the readable flat folder front panel, rear flap, angled opening, shallow pocket relationship, and folder silhouette.
- Accent colors remain an overly close copy when adjustment was safe and appropriate.
- Accent colors overpower the primary palette, reduce contrast, break material readability or alter protected/semantic colors.
- Decorative accents are copied mechanically from the reference with no visible random change.
- Decorative accents obscure the main subject, become the primary focal point, create clutter, add text, or introduce a misleading semantic/status symbol.
- Foreground contains background scenery or lacks true transparent pixels after green-screen removal.
- Foreground was not generated from the structured JSON foreground elements, was resized before key-screen removal, was not scaled to approximately 70% after key removal, is not `512x512`, or semi-transparent edges retain visible key-color contamination.
- Foreground contains unintended transparent holes inside the main subject after key removal. Folder openings, object interiors, card gaps, grooves, or other non-transparent internal regions are empty/transparent instead of filled with plausible subject color or shadow.
- Foreground uses a local rough mask or reference cutout as a substitute for generation, contains original background chunks, rectangular artifacts, hard polygon-mask edges, broken/missing subject parts, or looks like a low-quality cutout.
- Background was not generated from the structured JSON background information, contains transparency, a subject-shaped hole, subject ghosting or duplicated foreground elements.
- Background is merely a placeholder gradient, blank color field, random decorative circles, or otherwise not a designed background variant consistent with the JSON.
- Background is not `512x512`, or the final background contains partial alpha.
- Foreground and background dimensions/alignment differ, or the unscaled-subject recomposed check image shifts the subject.
- The same element appears in both final foreground and final background layers, including duplicated sparkles, white glints, sweep highlights, badges, bubbles, shadows, or any foreground-attached effect.
- White negative icon is not based on the actual keyed foreground source image file, is not `72x72`, contains non-white visible pixels, lacks transparency, uses outlines/effects, loses subject identity or becomes an undifferentiated solid blob.
- White negative icon was generated from semantic description, conversation memory, a previous negative template, or a generic folder/upload concept instead of the current foreground image's actual silhouette, card count, angles, arrow placement and overlap order.
- White negative icon is only a filled alpha silhouette, has no meaningful internal transparent negative spaces, lacks recognizable internal features, becomes a potato-like blob at `72x72`, or loses the shield/tool/trash-bin identity.
- White negative icon was trimmed and the main element was shrunk before placing it into a `72x72` canvas, or otherwise uses a final subject-shrink/extra-margin step instead of resizing the full normalized canvas to `72x72`.

## Platform Notes

- Default to a square master artwork when platform requirements are unspecified.
- Do not automatically bake iOS-style rounded corners into a source icon.
- Do not automatically create Android adaptive-icon foreground/background layers unless requested.
- Transparency is allowed only when explicitly requested or required by the reference/workflow.
- Store-submission requirements may change; verify current platform documentation when the user asks for compliance-ready deliverables.
