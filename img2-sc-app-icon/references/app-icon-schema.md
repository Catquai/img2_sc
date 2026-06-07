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
  "invariants": [],
  "allowed_changes": [],
  "forbidden_changes": [],
  "failure_criteria": [],
  "layer_split": {
    "enabled": false,
    "key_color": "#ff00ff",
    "key_color_reason": "selected for maximum distance from all foreground opaque and semi-transparent colors",
    "key_color_candidates": ["#00ff00", "#ff00ff", "#0000ff", "#ff0000", "#ffff00", "#00ffff"],
    "extraction_strategy": "adaptive_chroma_key | local_segmentation_matte | provided_alpha_mask",
    "foreground_elements": [],
    "background_elements": [],
    "foreground_exclusions": [],
    "background_exclusions": [],
    "background_fill_strategy": "continue gradients, textures, atmosphere, and hidden scenery behind the removed foreground",
    "shared_constraints": ["same canvas size", "same alignment", "same color space", "same lighting direction"]
  },
  "white_negative_icon": {
    "enabled": false,
    "source": "foreground_alpha_png",
    "fill_color": "#ffffff",
    "background": "transparent",
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
    "fit": "cover",
    "files": {
      "composite": null,
      "foreground_green_screen": null,
      "foreground_alpha_png": null,
      "background_png": null,
      "composite_preview": null
    }
  }
}
```

## Reference Analysis Rules

- Distinguish semantic identity from observed shape. Record both when the reference uses an abstract symbol.
- Record exact count and orientation of meaningful objects. Separate immutable `semantic_orientation` from changeable `visual_pose`.
- Treat background, primary symbol, badge, text, highlight and shadow as separate layers.
- Record transparent corners separately from internal semi-transparent materials.
- Preserve the reference's mask only when it is visibly part of the asset or explicitly requested.
- In `reference_only`, preserve identity, hierarchy, style family and mask while creating a visibly new pose. By default, add light-to-moderate rotation, pitch, yaw or three-quarter perspective to the primary symbol; adjust its bounds and nearby secondary elements as needed to maintain balance and safe-area margins.
- Prefer approximately `8-25°` planar rotation or a subtle/moderate perspective change. Use smaller changes when the subject is already diagonal or near the safe-area boundary.
- Preserve semantic orientation and functional relationships. Do not reverse directional symbols, vehicle travel direction, animal head/tail direction, tool assembly, object stacking or front/back layer meaning.
- Do not perspective-warp text, numbers, brand marks, flags, arrows, strict symmetric badges or precision geometry unless the user explicitly requests it.
- Separate `primary_colors`, `accent_colors` and `protected_colors`. Primary colors define the subject identity; accent colors support local contrast and detail; protected colors must remain exact or perceptually unchanged.
- In `reference_only`, moderately vary secondary accent colors by default. Suitable targets include grip caps, trim, small badges, inner surfaces, edge highlights and secondary shadows.
- Keep accent changes harmonious with the original palette and material. Preserve brightness ordering between highlight, base and shadow, and ensure the subject remains readable at small size.
- Never let accent colors replace or overpower the primary color identity. Do not change brand colors, flag colors, traffic/status colors or user-specified exact colors without explicit permission.

## Foreground And Background Pair

- Enable `layer_split` only when the user requests separate foreground/background output or when the requested deliverable clearly requires movable layers.
- Assign every visible element to foreground or background before generation. Keep only the primary subject and subject-attached effects in the foreground.
- Generate the foreground on a uniform adaptive chroma-key color, then locally remove the key screen to create a true-alpha PNG. Do not default blindly to green.
- Choose the key color with maximum distance from primary colors, accent colors, highlights, glows, shadows and particles. Prefer `#ff00ff` for blue/cyan foregrounds, `#00ff00` for purple/red/warm foregrounds, and avoid any key color present in semi-transparent effects.
- If a blue/cyan foreground also contains purple or magenta accents, prefer yellow `#ffff00` over magenta.
- Generate the background as a complete fully opaque image. Continue gradients, clouds, textures, particles and scenery behind the removed subject; never leave a transparent hole or subject-shaped empty patch.
- Default final layer dimensions to `512x512` unless the user explicitly requests another size.
- Foreground processing order is mandatory: remove green screen at original generated resolution, reconstruct/decontaminate semi-transparent pixels, verify alpha, then resize the transparent PNG. Never resize the green-screen source before keying.
- Background processing order is mandatory: fill/flatten all transparent and semi-transparent areas at original generated resolution, verify the background is fully opaque, then resize. Never resize a transparent background layer before filling.
- Semi-transparent foreground glows, highlights, antialiased edges and shadows must be color-decontaminated by reversing key-screen compositing and applying generic despill. Set hidden RGB to zero for fully transparent and extremely low-alpha pixels before resizing; reject visible key-color fringes.
- Move non-subject-attached translucent fog, environmental glow, trails and particles to the background whenever possible. This is more reliable than color-key extraction.
- Keep both layers at exactly the same pixel dimensions and alignment. Do not recenter, rescale or rotate the subject between passes.
- Exclude subject silhouettes, ghosting, duplicate foreground decoration and subject-specific highlights from the background.
- When a contact shadow must remain fixed to the scene, place it in the background. When a glow or shadow must travel with the subject, place it in the foreground and preserve a soft alpha edge.

## White Negative Icon

- Use only the completed transparent foreground layer as the source reference.
- Preserve the subject's outer silhouette and identity-defining parts while simplifying decorative details.
- Express internal structure only with transparent negative space. Use negative holes for openings, component separation and essential internal landmarks.
- Keep every visible pixel pure white. Preserve antialiased alpha edges, but do not use gray RGB values for antialiasing.
- Reject strokes, outlines, shadows, gradients, colors, glow, texture and 3D volume.
- Ensure negative spaces remain open and readable after resizing. Merge or remove fragile micro-details.
- Do not treat color normalization as negative-space design. First generate or construct the required negative alpha regions; only then normalize all visible RGB to white.

## Small-Size Readability

Reject the result when:

- The primary symbol cannot be identified at approximately 48px.
- Thin details disappear or merge.
- Background contrast is too weak.
- Several elements compete as equal focal points.
- Important parts cross the safe area or are clipped.
- A `reference_only` result copies the reference pose too closely without a meaningful rotation, perspective or silhouette change.
- Rotation or perspective makes the subject distorted, hides identity-defining parts, reverses semantic direction or breaks relationships.
- Accent colors remain an overly close copy when adjustment was safe and appropriate.
- Accent colors overpower the primary palette, reduce contrast, break material readability or alter protected/semantic colors.
- Foreground contains background scenery or lacks true transparent pixels after green-screen removal.
- Foreground was resized before key-screen removal, or semi-transparent edges retain visible key-color contamination.
- Background contains transparency, a subject-shaped hole, subject ghosting or duplicated foreground elements.
- Background was resized before transparent areas were filled, or the final background contains partial alpha.
- Foreground and background dimensions/alignment differ, or the recomposed preview shifts the subject.
- White negative icon contains non-white visible pixels, lacks transparency, uses outlines/effects, loses subject identity or becomes an undifferentiated solid blob.

## Platform Notes

- Default to a square master artwork when platform requirements are unspecified.
- Do not automatically bake iOS-style rounded corners into a source icon.
- Do not automatically create Android adaptive-icon foreground/background layers unless requested.
- Transparency is allowed only when explicitly requested or required by the reference/workflow.
- Store-submission requirements may change; verify current platform documentation when the user asks for compliance-ready deliverables.
