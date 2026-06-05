---
name: image2-reference-regenerate
description: 根据文本描述、参考图，或参考图结合文本描述生成图像。使用时先判定输入模式：纯文本生图时，将用户文本拆解成结构化 JSON 提示词，再依据 JSON 生成新图像，并特别检查用户是否明确要求固定尺寸或透明 PNG；参考图生图时，从参考图提炼结构化 JSON 提示词，记录画布、画布外形/圆角类型与大小、透明遮罩、风格指纹、可见元素、图标/形状身份、位置、层级、不变性约束、允许变化范围和失败标准；参考图结合文本描述生图时，先提炼参考图 JSON，再从文本中提取关键语义（视觉风格、色彩、外形描述、主体替换、材质、背景、尺寸、透明要求等）并合并/替换到 JSON。之后使用 image_generation 工具并指定 gpt-image-2 模型，根据最终 JSON 生成新图像；如果需要透明背景，必须先本地去绿幕得到真实 alpha PNG，再把透明 PNG 调整为目标尺寸。适用于文本生图、参考图重生成、复刻构图、参考图+文字改写、生成相似但不雷同的图、保持内容元素/布局/风格/图标身份/画布外形/尺寸一致且输出透明 PNG 的任务。
---

# GPT-Image-2 结构化图像生成

## 概述

使用这个 skill 时，先把用户输入转成结构化 JSON 提示词，再依据 JSON 生成新图像。输入可能是纯文本、参考图，或参考图结合文本描述。生成过程必须保持 JSON 中定义的关键语义、图标身份、元素位置、元素完整性、视觉风格、画布外形和输出要求。对参考图任务，默认生成新的变体而不是近似复制；对纯文本任务，默认以用户描述为准，不强制继承参考图尺寸或透明背景，除非用户明确要求。

## 工作流

1. 判定输入模式。
   - `text_only`：用户只提供文本描述，没有参考图。必须把文本拆解为结构化 JSON 提示词，再依据 JSON 生成新图像。
   - `reference_only`：用户提供参考图，没有额外改写文本。必须先把参考图提炼成结构化 JSON 提示词，再依据 JSON 生成语义一致但不雷同的新变体。
   - `reference_plus_text`：用户同时提供参考图和文本描述。必须先从参考图提炼基础 JSON，再从文本中提取关键语义并合并/替换到基础 JSON，最后依据合并后的 JSON 生成新图像。
   - 对任何模式，都要检查用户是否明确要求固定尺寸、透明 PNG、圆角/遮罩、输出格式、背景颜色、文字内容或主体数量。只有明确要求或参考图本身约束时，才强制这些输出条件。

2. 如果存在参考图，先检查参考图。
   - 使用可用的视觉检查工具识别主体、构图、视角、光照、色彩、背景、文字、材质和所有显著对象。
   - 记录参考图像素尺寸。如果无法直接读取元数据，运行 `scripts/match_reference_size.ps1 -Info -Paths <reference-image>`。
   - 识别画布外形和透明遮罩。必须判断参考图是 `circle`、`rounded_square`、`rounded_rectangle`、`pill`、`full_rectangle`、`transparent_freeform` 还是其他形状。
   - 记录圆角类型与大小：圆形写 `shape: circle`、`corner_radius_percent: 50`；圆角矩形写实际半径百分比和像素估计值；胶囊形写 `shape: pill`；透明自由形状写 `shape: transparent_freeform` 并描述可见内容边界。
   - 检查四角像素/透明区域。如果四角透明且可见区域为圆形，生成图必须使用圆形遮罩，不能生成圆角矩形底座。
   - 如果提供了多张参考图，默认选择主参考图决定最终尺寸，除非用户另有说明。
   - 生成元素地图。对每个可见元素记录相对边界框：`x`、`y`、`w`、`h`，单位为画布宽高百分比，同时记录层级、颜色，以及该元素是否被画布裁切。
   - 生成图标身份地图。对每个可识别的图形符号或对象标注具体类别，例如 `star`、`car`、`money bag`、`magnifying glass`、`shield`、`calendar`、`arrow`、`coin`、`chart`、`person`、`document`、`text label`。
   - 对每个图标身份记录不能改变的形状定义特征。例如：车必须有车身、车顶/座舱、前后方向、车轮、车窗和车灯；放大镜必须有圆形镜片和手柄；星星必须有尖角；钱袋在可见时必须有扎口和货币符号。
   - 对文字记录精确可见字符串、字符数量、基线角度、字重、填充色、描边色、阴影/高光，以及每个字符是否完整位于画布内。
   - 生成风格指纹。记录参考图是 `flat_gradient_icon`、`soft_gradient_ui_icon`、`soft_2.5d_icon`、`soft_3d`、`拟物图标`、`扁平矢量`、`线性图标`、`像素风`、`照片感` 还是 `手绘插画`；记录渐变方式、边缘硬度、圆角、内外阴影、高光、厚度感、投影、材质和整体饱和度。
   - 必须先判断风格强度，不得把所有 App 图标默认归为 3D。只有参考图同时具有明显厚度/体积建模、真实材质高光、可见接触阴影或三维透视时，才可标记为 `soft_3d` 或 `拟物图标`。
   - 如果参考图只是简洁几何图形、平面图标符号、柔和线性渐变、轻微内阴影或轻微高光，应标记为 `soft_gradient_ui_icon` 或 `flat_gradient_icon`，并在 JSON 中明确禁止生成额外厚重 3D、立体凸起、真实材质、复杂投影或明显景深。
   - 判断参考图是否具有明显的柔和 3D/拟物渲染。如果有，JSON 中必须明确禁止生成成扁平 SVG/vector clipart 风格；如果没有，禁止在提示词中加入 `volumetric forms`、`3D bevels`、`skeuomorphic`、`realistic material` 等会增强立体感的词。
   - 生成变化指令。记录哪些内容必须保持不变，哪些内容必须变化。默认要求保持图标身份、数量级、主布局、层级关系、透明遮罩和风格；同时改变元素轮廓、局部比例、装饰细节、颜色色相/明度或材质细节。

3. 判断是否适合直接使用图像生成。
   - 只有在参考图本身就是扁平矢量、线性图标、几何徽章、文字标牌，或必须严格保证精确文字/几何时，才优先使用确定性 SVG/canvas/vector 重建后导出位图。
   - 如果参考图是柔和 3D、拟物图标、渐变体积、粘土质感、半写实插画、柔焦阴影或照片感，优先使用 `gpt-image-2` 复现风格；不要用确定性矢量绘制替代，否则会变成扁平 SVG 插画。
   - 如果参考图是 `flat_gradient_icon` 或 `soft_gradient_ui_icon`，仍可使用 `gpt-image-2` 生成变体，但提示词必须强调“平面 UI 图标、柔和渐变、轻微高光、无明显 3D 厚度”，不要要求真实体积、厚重倒角、接触阴影或拟物材质。
   - `gpt-image-2` 更适合新鲜视觉渲染、纹理、插画、照片感或绘画风格输出。不要只依赖 `gpt-image-2` 来保证精确排版、微小可读文字或严格图标几何。
   - 如果用户明确要求必须使用 `gpt-image-2`，提示词中必须加入完整性约束，并拒绝任何裁切、遗漏、错层、替换或扭曲关键元素的结果。

4. 提炼结构化 JSON 提示词。
   - 在调用任何生成工具前，必须根据 `JSON 提示词契约` 生成一个 JSON 对象。
   - `text_only` 模式：必须从用户文本中提取主体、动作、场景、构图、视觉风格、色彩、材质、光照、背景、文字、画布比例、尺寸、透明背景、输出格式和禁止项。不要臆造用户没有要求的固定尺寸或透明背景；如果用户没有指定尺寸，使用模型支持的合理比例并在 `output.final_width_px/final_height_px` 中留空或标记为 `null`。
   - `reference_only` 模式：必须把参考图翻译为明确 JSON 属性，不要使用 `same as reference` 这类模糊值。
   - `reference_plus_text` 模式：先生成参考图基础 JSON，再生成 `text_overrides`，最后合并为 `final_json`。文本中明确指定的视觉风格、色彩、主体替换、外形描述、材质、背景、文字、尺寸、透明要求优先级高于参考图；文本没有提到的布局、元素位置、层级、画布外形和输出约束默认继承参考图。
   - 合并时必须记录每个覆盖来源：`source: "reference"`、`source: "user_text"` 或 `source: "inferred"`。如果文本与参考图冲突，以用户文本为准，但要保留不冲突的参考图结构。
   - 用户文本只说“参考图风格/参考图构图/类似参考图”时，不要替换全部 JSON；只继承相应字段。
   - 元素位置只能使用标准化百分比边界：`x`、`y`、`w`、`h`，范围为 `0` 到 `100`。
   - 在 JSON 字段中用具体视觉语言描述目标图像：内容、构图、风格、光照、颜色、宽高比和需要避免的内容。
   - 避免 `same as reference` 这类模糊值；必须把参考图翻译为明确 JSON 属性。
   - JSON 中必须包含完整的元素地图和图标身份地图。给每个必需图标/对象命名并写出不变特征，例如：`side-view car facing right with two wheels, roof/cabin, blue body, rear red light, front yellow light`；`tan money bag on top of the car with tied neck and dollar sign`。
   - JSON 中必须加入元素完整性约束：除非参考图本身裁切该元素，否则所有命名元素必须完整可见；文字不能被裁切；装饰层不能遮挡关键对象。
   - JSON 中必须加入图像不变性约束：不得把参考图里的图标身份替换成近似但错误的对象，例如把车替换成普通椭圆车身、把钱袋替换成盒子、把放大镜替换成圆圈、把星星替换成模糊闪光形状。
   - JSON 中必须加入风格不变性约束：不得把柔和 3D/拟物/渐变体积图标改成扁平 SVG、硬边矢量、卡通贴纸、低细节剪贴画或普通 logo 图形；也不得把原本平面/轻渐变图标过度生成成厚重 3D、粘土、玻璃拟物、真实材质或强投影图标。
   - JSON 中必须加入画布外形不变性约束：生成图的 `canvas.shape`、`corner_radius_percent`、透明边角和可见遮罩必须严格匹配参考图。
   - JSON 中必须加入变化约束：生成图不能与参考图过于相似，必须在 `variation` 字段中指定造型变化、配色变化和禁止近似复制的要求。
   - JSON 中必须加入透明 PNG 约束：如果参考图是 `transparent_freeform` 或有透明角/透明遮罩，`output.transparent_png` 必须为 `true`。生成阶段使用纯色绿幕背景辅助分离，后处理本地去绿幕生成真实 alpha PNG；禁止白底、黑底、棋盘格底和把透明预览格子画进图里。
   - 对涉及身份敏感或版权相关的元素，只在用户请求和政策允许时保留；否则应泛化为非识别性的视觉描述。

5. 根据 JSON 提示词生成。
   - 必须优先使用 `image_generation` 工具，并在工具/API 支持模型参数时明确指定 `gpt-image-2` 模型。
   - 如果当前环境只暴露封装后的图像生成工具，则在提示词和调用说明中明确写明目标模型为 `gpt-image-2`。
   - 如果工具/API 支持图像输入，把参考图作为视觉上下文传入。
   - 可以把 JSON 转为简洁的生成提示词，但不能丢弃任何 `style_fingerprint`、`required_traits`、`bounds_percent`、`layer`、`relationship`、`invariants` 或 `failure_criteria`。
   - 生成提示词必须先描述风格，再描述元素。风格描述必须来自 JSON 的 `style.rendering` 和 `style.depth_level`，不得套用固定 3D 模板。
   - 对拟物/软 3D 参考图，才可明确要求 `soft 3D app icon rendering, smooth gradients, rounded volumetric forms, soft blurred contact shadow, subtle highlights, no flat vector SVG look`。
   - 对平面或轻渐变 UI 图标，应明确要求 `flat/soft gradient UI app icon, clean geometric shapes, smooth color transitions, subtle inner highlight only, no obvious 3D thickness, no heavy bevel, no realistic material, no cast shadow`。
   - 生成提示词必须明确变化要求。例如：`create a new variation, not a near copy; keep semantic identity and layout but alter silhouettes, proportions, detail shapes, and color palette moderately`。
   - 按 JSON 中的 `canvas.aspect_ratio` 请求最接近的支持比例。精确像素尺寸由后处理完成。
   - 生成提示词必须明确画布外形。例如：`circular icon mask with transparent corners, not a rounded square` 或 `wide rounded rectangle banner with 44px corner radius`。
   - 当 `output.transparent_png` 为 `true` 时，必须在提示词中写明：`place the generated object on a solid pure green chroma key background (#00ff00), no checkerboard pattern, no white background, no black background, no shadows cast onto the background`。生成后使用本地脚本去绿幕得到真实透明 PNG。
   - 条件允许时，先生成较大尺寸，再下采样到参考图尺寸。这样通常比直接生成小图更能保留边缘和小文字。

6. 先处理透明背景，再调整到目标尺寸。
   - 如果 `output.transparent_png` 为 `true`，必须先对原始绿幕生成图去绿幕，得到未缩放的真实透明 PNG：

```bash
powershell -ExecutionPolicy Bypass -File scripts/remove_green_screen.ps1 -Source <green-screen-generated-image> -Output <transparent-large-image> -KeyColor "#00ff00"
```

   - 然后再把这个透明 PNG 调整为目标尺寸。参考图模式默认目标尺寸为参考图尺寸；纯文本模式只有用户明确指定尺寸时才执行固定尺寸后处理：

```bash
powershell -ExecutionPolicy Bypass -File scripts/match_reference_size.ps1 -Reference <reference-image> -Generated <transparent-large-image> -Output <final-image> -Background "#ffffff00"
```

   - 禁止先缩放/裁切绿幕图再去绿幕。缩放会把绿色背景插值混入主体边缘，导致去绿幕后出现绿色边、半透明脏边或 alpha 轮廓不干净。
   - 透明 PNG 缩放时必须显式传入 `-Background "#ffffff00"`，否则默认不透明背景会破坏最终 alpha。
   - 如果 `output.transparent_png` 不是 `true`，才可以直接对生成图运行 `match_reference_size.ps1`。
   - 纯文本模式如果用户没有指定固定尺寸，不要强制运行 `match_reference_size.ps1`；保留生成工具输出的原始尺寸即可。
   - 当最终文件必须填满同一画布且不能留白时，优先使用 `-Fit cover`。
   - 当完整保留生成图内容比填满画布更重要时，使用 `-Fit contain -Background "#ffffff"`。

7. 验证最终文件。
   - 如果有参考图或用户明确指定固定尺寸，重新运行 `scripts/match_reference_size.ps1 -Info -Paths "<reference-image>,<final-image>"` 或检查目标尺寸，确认输出尺寸符合 JSON。
   - 以 JSON 提示词为准，而不是凭记忆检查。`elements` 中列出的每个对象都必须存在、层级正确，并位于允许的相对区域内。
   - 对照 `canvas.shape` 和 `canvas.corner_radius_percent`。输出图的外形、圆角大小、透明角和遮罩必须与参考图一致；圆形参考图不能输出为圆角矩形，圆角矩形参考图也不能输出为圆形。
   - 对照 `style_fingerprint`。输出必须匹配参考图的渲染媒介、体积感、材质、边缘柔和度、阴影和高光；如果软 3D 图标被生成成扁平 SVG 插画，必须判定失败；如果轻渐变/平面图标被生成成明显 3D、厚重拟物、玻璃块、粘土或强投影，也必须判定失败。
   - 对照 `variation`。输出必须是新变体：元素语义和布局一致，但轮廓、颜色或细节不能与参考图过于接近。如果看起来像直接临摹或仅缩放/重采样参考图，必须判定失败。
   - 对照 `output.transparent_png`。如果要求透明 PNG，最终文件必须是带 alpha 通道的 PNG，且透明区域像素 alpha 必须为 `0`。棋盘格、白底、黑底、未去除的绿幕或截图式透明预览都必须判定失败。
   - 当 `output.transparent_png` 为 `true` 时，运行 `scripts/check_png_transparency.ps1 -Path <final-image>`。脚本必须返回成功；如果失败，说明文件不是合格的真实透明 PNG。
   - 对照元素地图。每个必需元素都必须存在、处于正确相对区域并完整可见。
   - 对照图标身份地图。每个可识别对象都必须保持具体类别和形状定义特征。
   - 对照 `failure_criteria`。只要任一失败条件成立，就拒绝该输出。
   - 如果必需元素缺失、被裁切、不可读、位置偏移超过画布宽/高约 `10%`，或变成不同图标/对象类别，则必须修改 JSON 或对该元素使用确定性重建。
   - 在最终回复中展示或引用最终图像路径。

## JSON 提示词契约

生成前始终先提炼这个 JSON。保持 JSON 合法：键和值使用双引号，不写注释，不写尾随逗号。

```json
{
  "input_mode": "reference_plus_text",
  "user_requirements": {
    "text_description": "optional user text prompt",
    "explicit_fixed_size": false,
    "explicit_width_px": null,
    "explicit_height_px": null,
    "explicit_transparent_png": false,
    "explicit_output_format": null
  },
  "text_overrides": {
    "apply": true,
    "style": {"value": "soft_gradient_ui_icon", "source": "user_text"},
    "colors": {"value": ["#22c7ff", "#ff7a59"], "source": "user_text"},
    "shape_description": {"value": "rounded square app icon with a music note", "source": "user_text"},
    "subject_replacements": [],
    "background": null,
    "preserve_from_reference": ["composition", "layer order", "canvas shape"],
    "replace_from_text": ["style", "colors", "subject details"]
  },
  "canvas": {
    "width_px": 273,
    "height_px": 273,
    "size_source": "reference",
    "aspect_ratio": "1:1",
    "shape": "rounded_square",
    "corner_radius_px": 33,
    "corner_radius_percent": 12,
    "mask": {
      "transparent_outside_shape": true,
      "must_match_reference_shape": true
    },
    "background": {
      "type": "rounded_square_gradient",
      "colors": ["#4aa2f5", "#42e6d1"],
      "transparent_outside_corners": true
    }
  },
  "style": {
    "rendering": "soft 3D app icon",
    "style_family": "soft skeuomorphic 3D, not flat SVG",
    "lighting": "top-left soft highlight",
    "depth": "subtle 3D bevels and shadows",
    "materials": ["smooth satin plastic", "warm metallic coin"],
    "edge_quality": "soft rounded volumetric edges",
    "shadow": "soft blurred contact shadow",
    "forbidden_styles": ["flat SVG", "hard-edge vector clipart", "low-detail cartoon sticker"]
  },
  "variation": {
    "goal": "new variation, not a near copy",
    "preserve": ["semantic identities", "main layout", "layer order", "style family", "canvas shape", "final dimensions"],
    "must_change": ["silhouette details", "local proportions", "secondary decorations", "color palette hue or brightness"],
    "color_shift": "moderate; keep harmony but avoid matching the reference colors exactly",
    "shape_shift": "moderate; keep recognizability but avoid tracing the same outlines",
    "similarity_limit": "do not look like a direct copy, recolor, resize, or lightly edited version of the reference"
  },
  "elements": [
    {
      "id": "shield",
      "identity": "shield",
      "bounds_percent": {"x": 14, "y": 17, "w": 45, "h": 56},
      "layer": 2,
      "required_traits": ["upright shield silhouette", "blue inner shield", "light border", "center vertical facet"],
      "appearance": {"main_colors": ["#b9d7ff", "#4b84f2"], "opacity": 0.9},
      "completeness": "fully visible behind broom except intentional overlap"
    }
  ],
  "relationships": [
    "broom overlaps shield in the foreground",
    "year ribbon stays anchored to lower-right corner"
  ],
  "invariants": [
    "Do not replace shield with generic polygon or badge",
    "Do not replace broom with brush, feather, or abstract fan",
    "Keep all required elements complete and recognizable",
    "Keep the same rendering style and material treatment as the reference"
  ],
  "failure_criteria": [
    "A required icon identity is changed",
    "A required element is missing",
    "A required element is clipped when the reference is not clipped",
    "Canvas shape, corner radius, or transparent mask differs from the reference",
    "Generated image is too similar to the reference in element shapes or colors",
    "Transparent PNG requirement is violated by white, black, colored, or checkerboard background",
    "Soft 3D or skeuomorphic reference style becomes flat SVG/vector clipart",
    "Text content changes or becomes unreadable",
    "Layer order contradicts relationships"
  ],
  "output": {
    "final_width_px": 273,
    "final_height_px": 273,
    "size_required": true,
    "size_source": "reference",
    "fit": "cover",
    "format": "png",
    "transparent_png": true,
    "transparent_source": "reference_mask",
    "alpha_required": true,
    "generation_background": {
      "type": "chroma_key_green",
      "color": "#00ff00",
      "remove_locally": true
    },
    "forbidden_backgrounds": ["checkerboard transparency preview", "white background", "black background", "unremoved green screen"]
  }
}
```

把这个 JSON 当作生成和验收的唯一事实来源。如果生成效果不好，先通过补充缺失的特征、关系或失败条件来修改 JSON，再重新生成。

## 输入模式与文本合并

`text_only` 模式：
- 只依据用户文本创建 JSON，不继承任何参考图字段。
- 必须检查用户是否明确写了尺寸，例如 `96x96`、`1024*1024`、`固定尺寸`、`和某图一样大`。没有明确尺寸时，不要强制后处理到固定像素。
- 必须检查用户是否明确写了透明 PNG、透明背景、alpha、无背景、抠图。没有明确透明要求时，不要默认走绿幕去背景流程。
- 文本里的风格、色彩、外形描述、主体、背景和文字必须进入 JSON 的对应字段，而不是只写在最终自然语言 prompt 里。

`reference_only` 模式：
- 参考图决定基础 JSON，包括尺寸、画布外形、透明遮罩、元素地图、图标身份、布局和风格指纹。
- 默认输出尺寸匹配参考图。
- 如果参考图有透明角或透明自由形状，默认 `output.transparent_png` 为 `true`。
- 默认生成新变体，不做近似复制。

`reference_plus_text` 模式：
- 第一步从参考图生成 `base_json`。
- 第二步从用户文本生成 `text_overrides`，抽取视觉风格、色彩、外形描述、主体替换、材质、背景、文字、尺寸、透明要求、禁止项。
- 第三步合并为 `final_json`。用户文本明确指定的字段优先级高于参考图；用户文本未指定的字段继续继承参考图。
- 合并后必须检查冲突。例如文本要求“圆形图标”但参考图是圆角方形时，最终 `canvas.shape` 应为 `circle`，并把 `source` 标记为 `user_text`。
- 文本只要求“保持参考图构图”时，只继承布局和层级；文本只要求“使用参考图配色”时，只继承色彩；不要过度继承。

合并优先级：
1. 用户明确文本要求。
2. 参考图可观察事实。
3. 为了成图完整性做出的必要推断。
4. 默认偏好。

不得让默认偏好覆盖用户文本或参考图事实。

## 画布外形与圆角

生成前必须识别并记录参考图的画布外形。这个字段和尺寸一样重要，不能靠默认圆角矩形猜测。

```json
{
  "canvas": {
    "width_px": 94,
    "height_px": 94,
    "aspect_ratio": "1:1",
    "shape": "circle",
    "corner_radius_px": 47,
    "corner_radius_percent": 50,
    "mask": {
      "transparent_outside_shape": true,
      "must_match_reference_shape": true
    },
    "background": {
      "type": "circular_warm_gradient",
      "colors": ["#fbf4df", "#eef7e9"]
    }
  }
}
```

常见取值：
- `circle`：圆形图标，`corner_radius_percent` 必须为 `50`，四角透明或被圆形遮罩裁掉。
- `rounded_square`：宽高接近相等的圆角方形，记录实际 `corner_radius_px` 和百分比。
- `rounded_rectangle`：非正方形圆角矩形，例如横幅卡片，必须记录四角半径。
- `pill`：半径约等于短边一半的胶囊形。
- `full_rectangle`：无圆角或几乎无圆角。
- `transparent_freeform`：没有底座，只有自由形状内容和透明背景。

验收时如果参考图是圆形，输出必须仍为圆形遮罩；不得输出为圆角矩形底座。参考图若是横向圆角矩形，也不得输出为圆形。

## 变体生成规则

重生成不是复刻。默认目标是“语义一致、风格一致、布局接近，但造型和颜色有适度变化”的新图。

必须保持：
- 图标/对象身份，例如金币堆仍是金币堆，垃圾桶仍是垃圾桶。
- 主体数量级和主要关系，例如前景金币仍覆盖金币堆右下方。
- 大体构图、层级、画布外形、透明遮罩、输出尺寸和风格指纹。

必须变化：
- 轮廓细节，例如金币厚度、边缘倒角、符号造型、局部曲线可以不同。
- 局部比例，例如前景元素可稍大/稍小，堆叠高度或间距可微调。
- 次要装饰和材质细节，例如高光形状、阴影软硬、边缘反光可变化。
- 配色，例如在同一色系内调整色相、明度、饱和度，或改用协调的新配色。

禁止：
- 生成与参考图几乎相同的轮廓、颜色和细节。
- 只做缩放、裁切、重采样、轻微锐化或简单换背景。
- 对参考图做近似描摹，导致看起来像同一张图的复制版本。

## 真实透明 PNG

当参考图是 `transparent_freeform` 或包含透明角/透明遮罩时，最终结果必须是真正带 alpha 通道的 PNG。透明预览的棋盘格只是 UI 展示方式，不能被画进图片。

不要要求模型直接生成棋盘格透明预览。生成阶段应使用纯绿幕背景，随后本地去绿幕：

```text
Place the generated object on a solid pure green chroma key background (#00ff00). No checkerboard pattern, no white background, no black background, no shadows cast onto the background.
```

后处理顺序必须是：先去绿幕得到真实透明 PNG，再缩放/裁切到目标尺寸，最后验证尺寸和 alpha。参考图模式的目标尺寸通常是参考图尺寸；纯文本模式只有用户明确指定固定尺寸时才需要缩放。不要先缩放绿幕图，否则绿色背景会被重采样到主体边缘。

第 1 步，去绿幕：

```bash
powershell -ExecutionPolicy Bypass -File scripts/remove_green_screen.ps1 -Source <green-screen-generated-image> -Output <transparent-large-image> -KeyColor "#00ff00"
```

第 2 步，匹配目标尺寸：

```bash
powershell -ExecutionPolicy Bypass -File scripts/match_reference_size.ps1 -Reference <reference-image> -Generated <transparent-large-image> -Output <final-image> -Background "#ffffff00"
```

第 3 步，验收透明度：

```bash
powershell -ExecutionPolicy Bypass -File scripts/check_png_transparency.ps1 -Path <final-image>
```

如果输出文件没有 alpha 通道、没有透明像素，或把白底/黑底/棋盘格/绿幕作为图像内容保存，必须重新生成或重新去绿幕。对于 `transparent_freeform` 图像，不能为了通过透明检查而仅把四角变透明；主体外轮廓之外的大面积背景也必须透明。

绿幕颜色选择要求：
- 默认使用 `#00ff00`。
- 如果主体本身包含大量接近纯绿的区域，改用与主体明显不同的高饱和 key color，并在 JSON 的 `generation_background.color` 中记录。
- 生成提示词必须要求主体不要带绿色溢色，背景不要有阴影、纹理、渐变或棋盘格。

## 风格指纹

生成前必须提炼风格指纹，尤其是 App 图标类参考图。风格指纹要进入 JSON 的 `style` 字段，并在验收时逐项检查。

先判断风格强度：
- `flat_gradient_icon`：平面几何符号和渐变底色，无可见厚度、无真实材质、无接触阴影。
- `soft_gradient_ui_icon`：有柔和渐变、轻微内高光或轻微内阴影，但主体仍是平面 UI 图标，不应生成明显 3D。
- `soft_2.5d_icon`：有轻微浮雕/内凹/外凸暗示，但没有真实三维透视和厚重体积。
- `soft_3d` / `拟物图标`：有明确体积建模、材质高光、厚度、投影或三维对象关系。

只有 `soft_3d` / `拟物图标` 才能使用 `volumetric`、`skeuomorphic`、`material`、`cast shadow`、`3D bevel` 等词。`flat_gradient_icon` 和 `soft_gradient_ui_icon` 必须避免这些词。

简洁音频/视频类 App 图标通常应这样记录：

```json
{
  "style": {
    "rendering": "soft_gradient_ui_icon",
    "style_family": "clean flat UI icon with smooth gradients, not 3D",
    "depth_level": "low",
    "lighting": "subtle top-left highlight only",
    "volume": "no visible 3D thickness; only gentle rounded-corner UI shading",
    "materials": ["flat digital gradient fill"],
    "edge_quality": "clean anti-aliased rounded edges",
    "shadow": "none or very subtle inner shadow only; no cast shadow",
    "forbidden_styles": [
      "soft 3D",
      "skeuomorphic 3D",
      "clay render",
      "glassmorphism block",
      "thick bevel",
      "realistic material",
      "strong cast shadow",
      "volumetric object"
    ]
  }
}
```

```json
{
  "style": {
    "rendering": "soft 3D app icon",
    "style_family": "soft skeuomorphic 3D, not flat SVG",
    "lighting": "top-left warm soft light",
    "materials": ["smooth satin plastic", "soft metallic coin"],
    "volume": "rounded inflated forms with gentle gradients",
    "edges": "soft anti-aliased rounded edges, no hard vector corners",
    "shadow": "soft blurred contact shadow under subject",
    "background_treatment": "warm ivory rounded square with faint diagonal glow",
    "detail_level": "minimal but volumetric, no line-art outlines",
    "forbidden_styles": ["flat SVG", "hard-edge vector illustration", "cartoon sticker", "outline icon", "low-detail clipart"]
  }
}
```

如果参考图是柔和 3D/拟物风格，生成提示词必须优先描述这个风格指纹，再描述对象和位置。确定性绘制只可用于后处理、遮罩、尺寸匹配或补救精确文字/几何，不应作为主要视觉生成方式。

## 图标身份地图

任何包含图标、符号或简化对象的参考图，都要创建这个地图：

```text
Icon 1: <语义身份，例如 car、star、magnifying glass、money bag>
Bounds: x=<左侧%>, y=<顶部%>, w=<宽度%>, h=<高度%>
Required traits: <让该图标可识别的形状定义特征>
Orientation: <朝向、旋转、倾斜或对称性>
Style: <flat/vector/soft 3D/outline/filled/duotone>
Invariance: 必须保持 <相同身份>；不得替换为 <常见错误替代物>
Completeness: <完整可见 | 被 ... 有意遮挡>
```

使用具体名词，不要使用含糊标签。写 `car`，不要写 `blue object`；写 `magnifying glass`，不要写 `circle with line`；写 `five-point star`，不要写 `sparkle`。

## 不变性规则

- 保持语义身份不变。如果参考图包含车，输出必须仍是车，而不是普通胶囊形、公交车、滑板车或抽象交通工具。
- 保持形状定义部件不变。车要保留两个轮子、座舱/车顶、车窗、车身和可见的前后方向。钱袋要保留圆鼓袋身、扎口，以及可见时的货币符号。放大镜要保留镜片和手柄。星星要保留尖角星形。
- 保持关键关系不变。如果钱袋位于车顶，输出中它也必须在车顶，而不能跑到车后、车内或变成盒子。
- 只保留参考图已有的遮挡关系。不得新增隐藏或裁切关键图标，除非参考图本身如此。
- 即使颜色和尺寸匹配，只要图标身份错误，也必须视为生成失败。

## 元素地图格式

生成前创建这个地图：

```text
Canvas: <width>x<height>
Element 1: <名称>
Bounds: x=<左侧%>, y=<顶部%>, w=<宽度%>, h=<高度%>
Layer: <back/middle/front>
Appearance: <填充、描边、渐变、阴影、高光、透明度>
Completeness: <完整可见 | 在 ... 有意裁切>
Role: <background/supporting/key element>
```

对包含文字或 UI 标签的参考图，每个词或主要文字组都要单独记录：

```text
Text: "HOT"
Bounds: x=<左侧%>, y=<顶部%>, w=<宽度%>, h=<高度%>
Typography: bold italic uppercase, white fill, purple stroke
Integrity: 所有字母必须完整可见且可读；顶部、左侧、右侧、底部都不能被裁切
```

## 小徽章示例

对于 `96x48` 的紫粉色 `HOT` UI 标签，生成前应检查到这个粒度：

```text
Canvas: 96x48, transparent background
Element 1: main rounded badge body
Bounds: x=2%, y=4%, w=83%, h=78%
Layer: middle
Appearance: magenta-to-violet horizontal/diagonal gradient, rounded corners, slight slant on right edge
Completeness: fully visible

Element 2: darker purple lower/right shadow body
Bounds: x=14%, y=13%, w=80%, h=83%
Layer: back
Appearance: saturated purple, rounded corners, visible below and to the right of main body
Completeness: fully visible except where hidden behind main body

Element 3: "HOT" text
Bounds: x=3%, y=13%, w=70%, h=67%
Layer: front
Appearance: bold italic uppercase white fill, thick purple outline, slight highlight
Completeness: all letters fully visible; top of H/O/T must not be clipped; text must not overflow the canvas
```

如果输出裁切了文字顶部、丢失阴影、把 `HOT` 改成其他字符串，或把文字放到徽章外，应视为失败并重新生成或确定性重建。

## App 图标示例

对于圆角 App 图标中的汽车和钱袋，要同时保持图形身份和位置：

```text
Canvas: 159x160, rounded square, transparent outside corners
Background: pale warm ivory/green gradient with subtle diagonal light streaks

Icon 1: side-view car
Bounds: x=9%, y=45%, w=84%, h=38%
Required traits: blue rounded car body, right-facing side view, visible roof/cabin, front and rear windows, two visible wheels, rear red light, front yellow light
Orientation: horizontal, facing right
Invariance: must remain a recognizable car; do not simplify into an oval blob, single-wheel object, box, or generic vehicle
Completeness: fully visible

Icon 2: money bag
Bounds: x=48%, y=24%, w=30%, h=48%
Required traits: tan sack body, tied gathered neck, small knot/tie at top, visible dollar sign or currency mark on front
Orientation: upright, sitting on top of the car body
Invariance: must remain a money bag; do not replace with a box, jar, coin stack, plain square, or roof cargo
Completeness: fully visible, may visually overlap the car but must not be hidden behind the car body

Relationship: money bag is placed above the central/right part of the car roof/body and overlaps the car visually in the foreground.
```

这类图标如果出现钱袋变盒子、袋身消失、美元符号缺失、车丢失轮子/车窗，或钱袋被移到车后导致身份不清，都必须判定失败。

## 软 3D 存钱罐示例

对于圆角 App 图标中的粉色存钱罐和金币，必须保持参考图的软 3D/拟物风格，不能重建成扁平 SVG 插画：

```json
{
  "canvas": {
    "width_px": 230,
    "height_px": 230,
    "aspect_ratio": "1:1",
    "background": {
      "type": "rounded_square_warm_gradient",
      "corner_radius_percent": 17,
      "colors": ["#fbf6df", "#eef6e7"],
      "transparent_outside_corners": true,
      "details": ["very subtle diagonal cream light streaks"]
    }
  },
  "style": {
    "rendering": "soft 3D app icon",
    "style_family": "soft skeuomorphic 3D, not flat SVG",
    "lighting": "warm top-left soft studio light",
    "materials": ["smooth satin pink ceramic/plastic piggy bank", "warm metallic gold coins"],
    "volume": "rounded inflated body with subtle gradients and no hard outlines",
    "edges": "soft anti-aliased rounded edges",
    "shadow": "soft blurred oval contact shadow below pig",
    "detail_level": "minimal details but volumetric modeling",
    "forbidden_styles": ["flat SVG", "hard-edge vector clipart", "cartoon sticker", "line-art icon", "solid-color blob"]
  },
  "elements": [
    {
      "id": "piggy_bank",
      "identity": "piggy bank",
      "bounds_percent": {"x": 20, "y": 37, "w": 62, "h": 42},
      "layer": 3,
      "required_traits": ["left-facing pig body", "rounded inflated pink body", "snout on left", "small dark eye", "triangular ear", "four short legs", "curled tail on right", "coin slot on top"],
      "appearance": {"main_colors": ["#f6a2ab", "#e97986"], "surface": "smooth satin gradient"},
      "completeness": "fully visible"
    },
    {
      "id": "gold_coins",
      "identity": "three gold coins",
      "bounds_percent": {"x": 40, "y": 16, "w": 22, "h": 25},
      "layer": 4,
      "required_traits": ["three separate round coins", "gold metallic gradient", "raised rim", "one coin partially inserted near top slot"],
      "appearance": {"main_colors": ["#f4c869", "#b9832c"], "surface": "soft metallic highlight"},
      "completeness": "all coins visible, not merged into one shape"
    },
    {
      "id": "contact_shadow",
      "identity": "soft ground shadow",
      "bounds_percent": {"x": 34, "y": 81, "w": 35, "h": 7},
      "layer": 1,
      "required_traits": ["blurred warm gray oval shadow under pig"],
      "appearance": {"opacity": 0.25},
      "completeness": "visible and soft"
    }
  ],
  "relationships": [
    "gold coins rise from the slot on top of the piggy bank",
    "pig faces left with tail on the right",
    "contact shadow sits directly below the floating pig"
  ],
  "invariants": [
    "Keep the object identity as a piggy bank, not a generic pig or oval blob",
    "Keep exactly the soft 3D app icon style from the reference",
    "Keep coins metallic and separate",
    "Do not add outlines or flat vector color blocks"
  ],
  "failure_criteria": [
    "Piggy bank becomes flat SVG/vector style",
    "Body loses soft 3D volume or satin gradients",
    "Coins merge, disappear, or stop looking metallic",
    "Tail, snout, ear, eye, legs, or slot are missing",
    "Background loses warm rounded app icon treatment"
  ],
  "output": {"final_width_px": 230, "final_height_px": 230, "fit": "cover"}
}
```

这类参考图的主要目标是风格一致性。即使元素位置正确，只要输出像扁平矢量图、硬边插画或普通 SVG，也必须判定失败。

## 圆形翻译图标示例

对于圆形翻译/语言图标，必须把圆形遮罩作为画布外形约束，而不是默认圆角方形：

```json
{
  "canvas": {
    "width_px": 94,
    "height_px": 94,
    "aspect_ratio": "1:1",
    "shape": "circle",
    "corner_radius_px": 47,
    "corner_radius_percent": 50,
    "mask": {
      "transparent_outside_shape": true,
      "must_match_reference_shape": true
    },
    "background": {
      "type": "circular_warm_gradient",
      "colors": ["#fbf2df", "#eef8e9"],
      "transparent_outside_corners": true
    }
  },
  "style": {
    "rendering": "soft 3D app icon",
    "style_family": "soft skeuomorphic 3D, not flat SVG",
    "lighting": "top-left warm soft light",
    "materials": ["soft purple glossy globe", "warm golden speech bubble"],
    "shadow": "subtle soft contact shadows",
    "forbidden_styles": ["rounded square base", "flat SVG", "hard-edge vector clipart"]
  },
  "elements": [
    {
      "id": "globe",
      "identity": "globe",
      "bounds_percent": {"x": 29, "y": 33, "w": 46, "h": 47},
      "layer": 2,
      "required_traits": ["purple sphere", "latitude and longitude grid lines", "soft highlight"],
      "completeness": "fully visible"
    },
    {
      "id": "speech_bubble",
      "identity": "speech bubble",
      "bounds_percent": {"x": 53, "y": 19, "w": 37, "h": 35},
      "layer": 3,
      "required_traits": ["rounded golden rectangle bubble", "small tail", "three small dots"],
      "completeness": "fully visible"
    },
    {
      "id": "gold_dots",
      "identity": "decorative gold dots",
      "bounds_percent": {"x": 5, "y": 10, "w": 84, "h": 75},
      "layer": 1,
      "required_traits": ["small scattered golden circular dots"],
      "completeness": "visible but secondary"
    }
  ],
  "invariants": [
    "Keep the canvas as a circle with transparent corners",
    "Do not generate a rounded square or rounded rectangle base",
    "Keep globe and speech bubble identities unchanged"
  ],
  "failure_criteria": [
    "Canvas becomes rounded square or rounded rectangle",
    "Circle mask is missing",
    "Globe grid is missing",
    "Speech bubble or three dots are missing"
  ],
  "output": {"final_width_px": 94, "final_height_px": 94, "fit": "cover"}
}
```

## 盾牌扫帚 JSON 示例

对于包含盾牌、扫帚和 `2026` 角标的圆角 App 图标，生成前应提炼到如下 JSON 粒度：

```json
{
  "canvas": {
    "width_px": 273,
    "height_px": 273,
    "aspect_ratio": "1:1",
    "background": {
      "type": "rounded_square_gradient",
      "corner_radius_percent": 12,
      "colors": ["#55a8f4", "#44e2d1"],
      "transparent_outside_corners": true,
      "details": ["soft green-yellow glow in lower-left", "subtle diagonal light streaks"]
    }
  },
  "style": {
    "rendering": "soft vector app icon",
    "lighting": "top-left highlight",
    "depth": "gentle bevels, soft shadows, glossy edges",
    "edge_quality": "clean rounded icon shapes"
  },
  "elements": [
    {
      "id": "shield",
      "identity": "shield",
      "bounds_percent": {"x": 14, "y": 16, "w": 46, "h": 58},
      "layer": 2,
      "required_traits": ["upright shield silhouette", "wide top shoulders", "pointed lower tip", "light outer border", "blue inner panel", "central vertical facet"],
      "appearance": {"main_colors": ["#c8e1ff", "#4b83f1"], "opacity": 0.9},
      "completeness": "mostly visible; only right side may be overlapped by broom"
    },
    {
      "id": "broom_handle",
      "identity": "broom handle",
      "bounds_percent": {"x": 57, "y": 6, "w": 24, "h": 45},
      "layer": 4,
      "required_traits": ["long blue diagonal handle", "rounded top", "small dark oval hole near top"],
      "orientation": "diagonal from lower-left to upper-right",
      "appearance": {"main_colors": ["#1469df", "#0b46b6"], "highlight": "cyan edge highlight"},
      "completeness": "fully visible"
    },
    {
      "id": "broom_collar",
      "identity": "broom collar",
      "bounds_percent": {"x": 41, "y": 36, "w": 29, "h": 16},
      "layer": 5,
      "required_traits": ["rounded blue ferrule", "wraps over top of bristles", "slightly tilted"],
      "appearance": {"main_colors": ["#1fc9ff", "#0c5dde"]},
      "completeness": "fully visible"
    },
    {
      "id": "broom_bristles",
      "identity": "broom bristles",
      "bounds_percent": {"x": 25, "y": 47, "w": 44, "h": 35},
      "layer": 4,
      "required_traits": ["yellow-orange fan of bristles", "multiple separated curved bristle segments", "rounded sweeping lower edge", "attached under blue collar"],
      "orientation": "fan opens downward-left",
      "appearance": {"main_colors": ["#ffe944", "#f39a16"], "separators": "orange curved lines"},
      "completeness": "fully visible"
    },
    {
      "id": "blue_shards",
      "identity": "flying blue shards",
      "bounds_percent": {"x": 30, "y": 55, "w": 55, "h": 36},
      "layer": 3,
      "required_traits": ["small angular blue fragments", "scattered around broom sweep"],
      "appearance": {"main_colors": ["#2e9ff0", "#53c9ff"]},
      "completeness": "visible but secondary"
    },
    {
      "id": "year_ribbon",
      "identity": "corner ribbon with year text",
      "bounds_percent": {"x": 70, "y": 55, "w": 30, "h": 45},
      "layer": 6,
      "required_traits": ["purple curved lower-right corner wedge", "white rotated text 2026", "thin blue highlight curve above ribbon"],
      "appearance": {"main_colors": ["#7a25f2", "#9b2df3"], "text": "2026"},
      "completeness": "anchored to lower-right corner; text fully readable"
    }
  ],
  "relationships": [
    "shield sits behind broom",
    "broom collar overlaps bristles",
    "broom handle connects visually to collar",
    "bristles sweep toward lower-left",
    "year ribbon stays in lower-right corner and does not cover the broom"
  ],
  "invariants": [
    "Keep shield recognizable as a shield, not a generic polygon",
    "Keep broom recognizable as a broom with handle, collar, and bristles, not a paint brush or fan",
    "Keep the text exactly 2026",
    "Keep all major objects inside the rounded square canvas"
  ],
  "failure_criteria": [
    "Broom loses handle, collar, or separated bristles",
    "Shield is missing or no longer shield-shaped",
    "2026 is missing, clipped, changed, or unreadable",
    "Purple corner ribbon is missing or placed away from lower-right corner",
    "Layer order changes so shield covers the broom"
  ],
  "output": {"final_width_px": 273, "final_height_px": 273, "fit": "cover"}
}
```

## 生成提示词模板

只在提炼 JSON 之后使用这个模板。生成提示词应概括 JSON，但不得丢失约束：

```text
Generate an image from this structured JSON prompt. Preserve every element identity, bounds, layer order, required trait, relationship, invariant, and failure criterion. Do not invent substitute icons. Keep exact required text.

JSON prompt:
<paste compact JSON here>
```

## 脚本

`scripts/match_reference_size.ps1` 会读取图像尺寸，并把生成图调整为与参考图一致。该脚本在 Windows 上运行，不依赖 Python 图像库。

- `-Info -Paths "<image>[,<image>...]"`：打印一个或多个图像的尺寸。
- `-Fit cover`：缩放并居中裁切，使生成图填满参考画布。
- `-Fit contain`：缩放到参考画布内，并用背景色补边。
- `-Fit stretch`：强制拉伸到精确尺寸；只有允许变形时才使用。

`scripts/check_png_transparency.ps1` 会检查 PNG 是否有 alpha 像素格式和透明像素。需要真实透明背景时必须运行它。

`scripts/remove_green_screen.ps1` 会把纯色绿幕背景转换为 alpha 透明，并做简单 despill。生成阶段使用绿幕背景时必须运行它。

