# App Icon Structured JSON

生成前使用以下结构。删除不适用字段，但不要省略关键约束。

```json
{
  "input_mode": "text_only | reference_only | reference_plus_text",
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
      "must_differ_from_reference": true,
      "must_differ_from_previous_generation": true
    },
    "single_primary_element_policy": {
      "apply_when": "one dominant subject or one merged symbol",
      "shape_variation": "noticeable but identity-preserving",
      "pose_variation": "noticeable random direction-angle rotation or perspective change",
      "rotation_delta_degrees": "12-35",
      "scale_delta": "0.85-1.18",
      "position_shift": "small shift inside safe area",
      "color_variation": "noticeable but harmonious"
    },
    "multiple_elements_policy": {
      "apply_when": "two or more meaningful visual elements",
      "main_element_preservation": ["identity", "required traits", "semantic orientation", "small-size readability"],
      "position_variation": "randomly adjust relative positions, spacing, and overlap while preserving hierarchy",
      "rotation_delta_degrees": {"main_element": "8-25", "secondary_elements": "10-40"},
      "scale_delta": "0.80-1.20",
      "color_variation": "vary main and secondary palettes without breaking semantic colors"
    },
    "forbidden": ["identity loss", "semantic direction reversal", "important-part occlusion", "safe-area overflow", "main-secondary hierarchy confusion"]
  },
  "pose_variation": {
    "apply_in_reference_only": true,
    "semantic_orientation": "",
    "reference_visual_pose": "",
    "target_visual_pose": "",
    "rotation_delta_degrees": "8-25",
    "perspective_change": "none | subtle | moderate",
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
    "enabled": false,
    "source_policy": "derive_layers_from_structured_json",
    "composite_source": null,
    "foreground_source": "structured_json.foreground_elements",
    "background_source": "structured_json.background_elements",
    "forbid_regenerated_similar_foreground": false,
    "key_color": "#ff00ff",
    "key_color_reason": "selected for maximum distance from all foreground opaque and semi-transparent colors",
    "key_color_candidates": ["#00ff00", "#ff00ff", "#0000ff", "#ff0000", "#ffff00", "#00ffff"],
    "extraction_strategy": "adaptive_chroma_key | local_segmentation_matte | provided_alpha_mask",
    "foreground_derivation": {
      "source": "structured_json.foreground_elements",
      "method": "generate_subject_variant_on_chroma_key",
      "forbid_local_rough_mask_fallback": true,
      "forbid_reference_cutout_as_generation_substitute": true,
      "work_at_original_or_higher_resolution": true,
      "keyed_intermediate": null,
      "alpha_output_original_size": null,
      "main_element_scale_percent_after_key_removal": 70,
      "final_foreground_size_px": [512, 512],
      "verify_true_alpha": true
    },
    "background_derivation": {
      "source": "structured_json.background_elements",
      "method": "generate_new_background_variant_from_json",
      "forbid_placeholder_gradient": true,
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
    "enabled": false,
    "source": "foreground_keyed_source",
    "source_must_be_derived_from_composite_foreground": false,
    "source_must_be_generated_from_keyed_foreground": true,
    "fill_color": "#ffffff",
    "background": "transparent",
    "keyed_intermediate": null,
    "final_size_px": [72, 72],
    "verify_true_alpha": true,
    "verify_visible_pixels_pure_white": true,
    "forbid_solid_alpha_silhouette_only": true,
    "require_internal_negative_space": true,
    "white_fill_regions": [],
    "transparent_negative_regions": [],
    "identity_features_to_preserve": [],
    "simplifiable_details": [],
    "minimum_negative_space_width_percent": 2,
    "forbidden": ["stroke", "outline", "shadow", "gradient", "gray", "color", "glow", "texture", "3d material", "solid blob without required negative details"]
  },
  "output": {
    "mode": "composite | foreground_background_pair",
    "final_width_px": 512,
    "final_height_px": 512,
    "format": "png",
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
      "foreground_alpha_png": null,
      "background_png": null,
      "white_negative_icon_png": null,
      "composite_preview": null
    }
  }
}
```

## Reference Analysis Rules

- When the user provides only a reference image, image attachment, image path, or `Files mentioned by the user` image context, treat it as a `reference_only` generation request by default. Extract JSON, then generate a new App icon variant. Do not stop at analysis, list options, or ask what to do unless the user explicitly requested analysis only or generation is blocked.
- Distinguish semantic identity from observed shape. Record both when the reference uses an abstract symbol.
- Record exact count and orientation of meaningful objects. Separate immutable `semantic_orientation` from changeable `visual_pose`.
- Classify the composition as `single_primary_element` or `multiple_elements` before generation. For a single primary element, create a noticeably different but recognizable shape, pose, random direction-angle rotation, scale, and color treatment. For multiple elements, preserve the main element identity while randomly adjusting element positions, angles, scale relationships, overlap, and colors.
- Every `reference_only` generation must sample fresh random variation parameters and record them in `composition_variation.randomization`. Do not reuse a fixed template pose, the reference pose, or the previous generation's parameter set.
- Identify decorative accents and record them in `decorative_variation`. Accents include sparkles, light dots, particles, small badges, local highlights, background glints, shine fragments, and non-semantic ornamentation.
- Decorative accents should vary randomly in every generation. Change count, position, scale, rotation, opacity, brightness, color, or small shape details while keeping them visually secondary and style-consistent.
- Treat background, primary symbol, badge, text, highlight and shadow as separate layers.
- Record transparent corners separately from internal semi-transparent materials.
- Preserve the reference's mask only when it is visibly part of the asset or explicitly requested.
- In `reference_only`, preserve identity, hierarchy, style family and mask while creating a visibly new variant. Single primary elements should usually use stronger random direction-angle rotation, shape/pose variation, scale change, and color variation than a minor pose tweak. Multiple-element icons may reorganize relative positions, angles, overlap, scale, and colors as long as the main element remains readable.
- Prefer approximately `12-35°` planar rotation for single primary elements, or `8-25°` for main elements and `10-40°` for secondary elements in multi-element compositions. Use smaller changes when the subject is already diagonal or near the safe-area boundary.
- Preserve semantic orientation and functional relationships. Do not reverse directional symbols, vehicle travel direction, animal head/tail direction, tool assembly, object stacking or front/back layer meaning.
- Do not perspective-warp text, numbers, brand marks, flags, arrows, strict symmetric badges or precision geometry unless the user explicitly requests it.
- Separate `primary_colors`, `accent_colors` and `protected_colors`. Primary colors define the subject identity; accent colors support local contrast and detail; protected colors must remain exact or perceptually unchanged.
- In `reference_only`, moderately vary secondary accent colors by default. Suitable targets include grip caps, trim, small badges, inner surfaces, edge highlights and secondary shadows.
- Keep accent changes harmonious with the original palette and material. Preserve brightness ordering between highlight, base and shadow, and ensure the subject remains readable at small size.
- Never let accent colors replace or overpower the primary color identity. Do not change brand colors, flag colors, traffic/status colors or user-specified exact colors without explicit permission.
- For `output.mode: composite`, the background fills the entire 1:1 canvas and is opaque by default. Transparent backgrounds, transparent corners, transparent holes, or blank margins are allowed only when the user explicitly requests transparent PNG or the reference/workflow requires a true alpha asset.

## Foreground And Background Pair

- Enable `layer_split` only when the user requests separate foreground/background output or when the requested deliverable clearly requires movable layers.
- For split output, derive separate generation passes from the structured JSON. Extract primary foreground elements into a keyed subject-variant pass, and extract background information into a new background-variant pass.
- Do not use local rough masks, hand-drawn polygon mattes, simple reference-image cutouts, or local rotate/scale transforms as substitutes for a generated keyed foreground variant. If the image generation tool is unavailable, stop and report that generation is blocked instead of delivering a fallback asset.
- Assign every visible element to foreground or background before generation. Keep only the primary subject and subject-attached effects in the foreground.
- Generate the foreground elements on a uniform adaptive chroma-key background, then locally remove the key screen to create a true-alpha PNG. Do not default blindly to green unless the user explicitly asks for green screen.
- The keyed foreground must be visually clean: no original-background chunks, rectangular color blocks, hard polygon-mask edges, missing handles/edges/critical parts, checkerboard, or discontinuous alpha boundaries.
- Choose the key color with maximum distance from primary colors, accent colors, highlights, glows, shadows and particles. Prefer `#ff00ff` for blue/cyan foregrounds, `#00ff00` for purple/red/warm foregrounds, and avoid any key color present in semi-transparent effects.
- If a blue/cyan foreground also contains purple or magenta accents, prefer yellow `#ffff00` over magenta.
- Generate the background from the structured JSON background description as a new complete fully opaque background variant. Do not include the primary subject, subject ghosting, subject-shaped empty patches, or duplicated foreground decoration.
- The background must be a designed App icon background consistent with the JSON style, palette, lighting, and decorative rules. Reject placeholder gradients, random circles, blank color fields, or generic backgrounds that are not grounded in the JSON.
- Default final layer dimensions to `512x512` unless the user explicitly requests another size.
- Foreground processing order is mandatory: generate keyed foreground from JSON at original or higher work resolution, remove key screen, reconstruct/decontaminate semi-transparent pixels, verify alpha, scale the main element to 70% on a transparent canvas, then resize/normalize the transparent PNG to `512x512`. Never resize the green-screen/keyed source before keying.
- Background processing order is mandatory: generate a complete opaque background variant at original or higher work resolution, verify the background is fully opaque, then resize to `512x512`.
- Semi-transparent foreground glows, highlights, antialiased edges and shadows must be color-decontaminated by reversing key-screen compositing and applying generic despill. Set hidden RGB to zero for fully transparent and extremely low-alpha pixels before resizing; reject visible key-color fringes.
- Move non-subject-attached translucent fog, environmental glow, trails and particles to the background whenever possible. This is more reliable than color-key extraction.
- Keep both layers at exactly the same pixel dimensions and alignment. Do not recenter, rescale or rotate the subject between passes.
- Exclude subject silhouettes, ghosting, duplicate foreground decoration and subject-specific highlights from the background.
- When a contact shadow must remain fixed to the scene, place it in the background. When a glow or shadow must travel with the subject, place it in the foreground and preserve a soft alpha edge.

## White Negative Icon

- Use the keyed foreground source as the visual reference. Generate a minimal pure-white negative-space icon on a uniform key screen, then locally remove the key screen to create transparent PNG output.
- Do not make the white negative icon by simply filling the foreground alpha silhouette with white. It must include readable internal transparent negative-space structures that preserve identity at `72x72`.
- Preserve the subject's outer silhouette and identity-defining parts while simplifying decorative details.
- Express internal structure only with transparent negative space. Use negative holes for openings, component separation and essential internal landmarks.
- Keep every visible pixel pure white. Preserve antialiased alpha edges, but do not use gray RGB values for antialiasing.
- Reject strokes, outlines, shadows, gradients, colors, glow, texture and 3D volume.
- Ensure negative spaces remain open and readable after resizing. Merge or remove fragile micro-details.
- Do not treat color normalization as negative-space design. First generate or construct the required negative alpha regions; only then normalize all visible RGB to white.
- Final white negative icon must be `72x72`, have true transparent background, and pass pure-white visible-pixel validation.

## Small-Size Readability

Reject the result when:

- The primary symbol cannot be identified at approximately 48px.
- Thin details disappear or merge.
- Background contrast is too weak.
- Composite output has transparent areas, blank margins, unpainted canvas regions, or a background that does not fill the entire canvas when transparency was not explicitly requested.
- Several elements compete as equal focal points.
- Important parts cross the safe area or are clipped.
- A `reference_only` result copies the reference pose too closely without a meaningful rotation, perspective or silhouette change.
- A repeated `reference_only` generation reuses the same angle, scale, position, overlap, and color parameters instead of sampling a fresh variation.
- Rotation or perspective makes the subject distorted, hides identity-defining parts, reverses semantic direction or breaks relationships.
- Accent colors remain an overly close copy when adjustment was safe and appropriate.
- Accent colors overpower the primary palette, reduce contrast, break material readability or alter protected/semantic colors.
- Decorative accents are copied mechanically from the reference with no visible random change.
- Decorative accents obscure the main subject, become the primary focal point, create clutter, add text, or introduce a misleading semantic/status symbol.
- Foreground contains background scenery or lacks true transparent pixels after green-screen removal.
- Foreground was not generated from the structured JSON foreground elements, was resized before key-screen removal, was not scaled to approximately 70% after key removal, is not `512x512`, or semi-transparent edges retain visible key-color contamination.
- Foreground uses a local rough mask or reference cutout as a substitute for generation, contains original background chunks, rectangular artifacts, hard polygon-mask edges, broken/missing subject parts, or looks like a low-quality cutout.
- Background was not generated from the structured JSON background information, contains transparency, a subject-shaped hole, subject ghosting or duplicated foreground elements.
- Background is merely a placeholder gradient, blank color field, random decorative circles, or otherwise not a designed background variant consistent with the JSON.
- Background is not `512x512`, or the final background contains partial alpha.
- Foreground and background dimensions/alignment differ, or the recomposed preview shifts the subject.
- White negative icon is not based on the keyed foreground source, is not `72x72`, contains non-white visible pixels, lacks transparency, uses outlines/effects, loses subject identity or becomes an undifferentiated solid blob.
- White negative icon is only a filled alpha silhouette, has no meaningful internal transparent negative spaces, becomes a potato-like blob at `72x72`, or loses the shield/tool/trash-bin identity.

## Platform Notes

- Default to a square master artwork when platform requirements are unspecified.
- Do not automatically bake iOS-style rounded corners into a source icon.
- Do not automatically create Android adaptive-icon foreground/background layers unless requested.
- Transparency is allowed only when explicitly requested or required by the reference/workflow.
- Store-submission requirements may change; verify current platform documentation when the user asks for compliance-ready deliverables.
