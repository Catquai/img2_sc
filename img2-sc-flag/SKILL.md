---
name: img2-sc-flag
description: 根据国旗参考图生成轻微变体国旗图标。适用于用户提供国旗图标参考图、图片路径、图片附件或包含多张参考图的文件夹，并要求重新生成、微调、变体、相似图、批量处理、同尺寸输出、透明 PNG、圆角国旗、国家/语言选择器旗帜图标或 UI 国旗资源；必须保持参考图构图、最终尺寸、圆角大小、透明度、裁切和国旗元素一致，只允许小幅随机调色。批量处理时自动识别文件夹内参考图，并按参考图原文件名保存结果。
---

# img2-sc-flag

## 核心规则

这个 skill 只处理“根据国旗参考图生成轻微变体”的任务。不要重新设计国旗，不要查找或替换为标准国旗版本，不要更换图案，不要改变构图、比例、裁切、圆角、透明背景或尺寸。

唯一允许的变化是轻微随机调色：小幅色相偏移、小幅饱和度变化、小幅明暗变化。色彩变化必须看起来像同一张参考图的轻调色版本，而不是新设计。

## 默认意图

- 当用户只提供图片、图片附件、图片路径或 `Files mentioned by the user` 中的国旗图片，而没有明确说“只分析 / 不生成 / 先别生成”时，默认这是 `reference_only` 生成请求，不要追问要做什么。
- 当用户提供文件夹路径，或明确说“处理这个文件夹 / 批量处理 / 文件夹内图片”时，默认这是 `batch_reference_folder` 请求：自动识别文件夹内可处理图片，逐张按 `reference_only` 规则生成轻微变体，不要要求用户逐张指定。
- 当用户提供参考图加文字要求时，按 `reference_plus_text` 处理，但文字要求不能覆盖国旗元素、布局、尺寸、圆角、透明遮罩等不变约束，除非用户明确要求改变这些输出条件。
- 只有参考图无法读取、生成工具不可用、策略限制，或用户明确要求仅分析时，才停下来说明原因或询问下一步。

## 文件夹批量处理

- 自动识别文件夹内常见图片格式：`.png`、`.jpg`、`.jpeg`、`.webp`、`.bmp`。默认跳过非图片文件、隐藏文件、临时文件和无法读取的损坏图片。
- 默认只处理用户提供文件夹的直接子文件；只有用户明确要求“递归 / 包含子文件夹”时，才递归处理子目录。
- 每一张参考图都必须独立读取尺寸、alpha、圆角、外形和国旗元素，并独立产出对应的 `final_json`。不要把第一张图的尺寸、遮罩或色彩规则套用到整批图片。
- 批量输出不得覆盖源文件。若用户指定输出目录，则输出到该目录；否则在参考图文件夹旁创建独立输出目录，建议命名为 `<原文件夹名>_flag_output`。
- 输出文件必须按参考图原名称保存：保留原始 basename 和扩展名，例如 `ic_italy.png` 输出仍命名为 `ic_italy.png`。如必须转换格式以保留透明 PNG，则保留 basename，扩展名改为 `.png`。
- 如果输出目录中已存在同名文件，不要静默覆盖；除非用户明确允许覆盖，否则使用独立批次目录或追加安全后缀，并在结果说明中列出命名策略。
- 批量处理完成后必须汇总成功、失败和跳过的文件列表。失败文件不应阻塞整批任务，除非全部失败或工具不可用。

## 工作流程

1. 读取参考图或参考图文件夹。
   - 单图输入按单张参考图处理。
   - 文件夹输入先枚举可处理图片并建立批量任务列表，再逐张执行后续步骤。
   - 获取参考图像素尺寸，最终输出必须与参考图完全相同。
   - 检查参考图是否有 alpha 通道、透明区域、半透明抗锯齿边缘、圆角或圆形遮罩。
   - 估计圆角大小：记录角落透明范围、圆角半径像素值或相对比例。
   - 判断画布外形：`full_rectangle`、`rounded_rectangle`、`circle`、`transparent_freeform` 或其他可观察形状。

2. 产出 `final_json`。
   - 生成或重建前必须先写出结构化 `final_json`，不要只凭预览或自然语言记忆直接绘制。
   - `final_json` 必须记录 canvas、shape、alpha_policy、flag_elements、color_adjustment_policy、invariants、failure_criteria 和 output。
   - 对条纹、色块、徽章、星星、文字、裁切关系等逐项记录数量、顺序、相对位置、比例和颜色身份。

3. 提取不变约束。
   - 保持国旗条纹、色块、徽章、星星、文字、比例、位置、层级和裁切方式不变。
   - 保持参考图画布外形：矩形、圆角矩形、圆形或透明自由形状必须一致。
   - 保持透明度关系：透明背景、半透明抗锯齿边缘、圆角外透明区、内部半透明层都要匹配。
   - 不主动修正参考图里的非标准国旗比例、偏色、裁切、圆角或 UI 化处理；以参考图为准。

4. 只做轻微随机色彩微调。
   - 允许每个主色做小幅随机色相偏移。
   - 允许轻微调整饱和度和亮度，但不能明显变暗、变亮、褪色或过饱和。
   - 禁止改变主色身份，例如红色不能变橙色/粉色，蓝色不能变紫色，白色不能变灰或米色，绿色不能变青色或黄色。
   - 禁止添加纹理、阴影、渐变、3D、高光、贴纸边框、描边或新装饰，除非参考图本来就有。

5. 生成或重建。
   - 如果参考图是简单几何国旗，优先使用确定性绘制或像素级后处理完成颜色微调。
   - 如果使用图像生成，提示词必须强调“参考图一致、仅轻微随机调色、尺寸和透明遮罩最终必须恢复为参考图一致”。
   - 图像生成后必须后处理到参考图尺寸，并恢复或匹配参考图透明遮罩。
   - 不要通过裁切、拉伸、挤压或强套 alpha mask 修复结构错误；国旗元素、裁切或形状错了就重新生成或重建。

6. 验证输出。
   - 最终宽高必须逐像素等于参考图。
   - 圆角大小、透明角、alpha 边缘和透明区域必须与参考图一致。
   - 国旗构图、图案数量、顺序、位置、层级和比例不得变化。
   - 色彩变化只能是轻微随机微调；如果一眼看起来不像同一张参考图的轻调色版本，判定失败。

## `final_json` 模板

```json
{
  "mode": "reference_only",
  "canvas": {
    "width_px": 96,
    "height_px": 72,
    "shape": "rounded_rectangle",
    "corner_radius_px": 8,
    "transparent_outside_shape": true
  },
  "alpha_policy": {
    "preserve_reference_alpha": true,
    "preserve_antialias_edges": true,
    "do_not_trim_or_expand_transparent_bounds": true
  },
  "flag_elements": [
    {
      "id": "stripe_1",
      "identity": "flag color band",
      "bounds_percent": {"x": 0, "y": 0, "w": 33.33, "h": 100},
      "color_identity": "green",
      "layer": 1,
      "invariant": "position, size, order, and crop stay unchanged"
    }
  ],
  "color_adjustment_policy": {
    "allowed": ["small hue shift", "small saturation shift", "small brightness shift"],
    "forbidden": ["change color identity", "add texture", "add shadow", "add gradient", "add outline", "add new elements"],
    "strength": "subtle"
  },
  "invariants": [
    "Keep the exact flag layout from the reference",
    "Keep the exact output size",
    "Keep the same alpha mask and rounded corners"
  ],
  "failure_criteria": [
    "Output dimensions differ from reference",
    "Flag stripes, symbols, text, or crop changed",
    "Color identity changed instead of subtle tuning",
    "Rounded corners or alpha edge differ from reference"
  ],
  "output": {
    "final_width_px": 96,
    "final_height_px": 72,
    "format": "png",
    "save_as_original_filename": true
  }
}
```

## 提示词模板

```text
根据参考图生成一个国旗图标轻微变体。保持参考图的构图、国旗图案、条纹/徽章/星星/文字位置、画布外形、圆角大小、透明背景和 alpha 边缘一致。最终输出尺寸必须与参考图完全相同。只允许随机微调颜色：轻微色相、饱和度和明暗变化；整体明暗不能与参考图差距过大。不要添加新元素、纹理、阴影、渐变、3D、描边、边框或贴纸效果。

结构化约束：
<粘贴 final_json>
```

## 参考规则

需要更短的执行清单时，读取 `references/flag-icon-rules.md`。

## 失败标准

- 输出尺寸与参考图不一致。
- 圆角半径、透明角或 alpha 边缘与参考图明显不一致。
- 国旗图案、条纹顺序、徽章、星星、文字、比例、层级或位置发生变化。
- 主动查找标准国旗并替换了参考图里的 UI 化比例、偏色、裁切或圆角。
- 色彩变化过大，导致主色身份改变或整体明暗明显偏离参考图。
- 增加了参考图没有的纹理、阴影、渐变、高光、边框、描边或装饰。
