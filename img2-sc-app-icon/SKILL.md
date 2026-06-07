---
name: img2-sc-app-icon
description: 使用 gpt-image-2 根据文本描述、移动端 App 主图标参考图，或参考图结合文本改写生成 iOS/Android 应用主 icon。适用于 App logo、launcher icon、store icon、圆角方形主图标、参考图重生成、构图复刻、风格变体、主体替换、固定尺寸输出、透明 PNG，以及将新图拆分为透明前景层和完整背景层；必须先生成结构化 JSON，保持图标身份、主构图、层级、风格、画布外形与尺寸约束，前景层通过绿幕转为真实 alpha PNG，背景层必须填满前景透明区域。
---

# img2-sc-app-icon

## 核心目标

生成可作为移动端 App 应用主 icon 的单张 1:1 图像。未指定尺寸时，最终输出默认使用 `512×512`。主 icon 必须在小尺寸下清晰可辨，拥有一个明确视觉中心，避免像普通 UI 功能图标、插画海报或复杂场景。

始终先判定输入模式并构建结构化 JSON，再调用图像生成工具并明确指定 `gpt-image-2`。详细 JSON 字段与检查清单见 `references/app-icon-schema.md`。

## 输入模式

1. `text_only`
   - 仅有文字描述。
   - 将文字拆解为 App icon 专用结构化 JSON。
   - 仅在用户明确要求时固定像素尺寸、透明 PNG、圆角遮罩或平台规范。

2. `reference_only`
   - 用户仅提供参考图，或没有提出明确改写要求。
   - 先提炼参考图 JSON，再生成语义、风格和主构图一致但不雷同的新变体。
   - 默认匹配参考图画布外形、透明遮罩和主要图标身份；最终尺寸仍默认为 `512×512`，仅在用户明确要求时匹配参考图原尺寸。
   - 默认让主图元素产生适度姿态差异：可增加轻到中度旋转、俯仰、偏航或三分之四透视，减少与参考图的雷同性；必须保持语义方向、关键部件、层级关系、小尺寸可读性和安全区。
   - 默认对主体元素的辅助性配色做适度调整，例如点缀色、端帽、局部高光、内侧阴影或小型装饰色；必须保持主体主色身份、明暗层级、材质关系和整体对比。

3. `reference_plus_text`
   - 同时提供参考图和改写文本。
   - 先提炼参考图 JSON，再从文本提取替换项并合并。
   - 用户明确要求优先；未被改写的参考图约束继续保持。

除非用户明确说“只分析”“只输出 JSON”或“不要生成”，不要停在分析阶段。

## 工作流

### 1. 收集输出约束

记录以下要求：

- 平台：`ios`、`android`、`cross_platform` 或未指定。
- 用途：应用主 icon、launcher icon、App Store/Play Store icon 或设计母版。
- 最终尺寸：用户明确指定时使用指定尺寸；否则默认 `512×512`。仅当用户明确要求匹配参考图尺寸时，才使用参考图原尺寸。
- 输出格式：PNG、透明 PNG 或其他格式。
- 输出模式：单张合成图 `composite`，或拆分为前景层与背景层 `foreground_background_pair`。
- 派生图标：是否需要根据透明前景层生成极简白色负形透明图标 `white_negative_icon`。
- 画布：必须为 1:1；记录方形、圆角方形、圆形或透明自由形状。
- 遮罩策略：图中自带圆角，还是由操作系统/商店应用遮罩。

平台未指定时，默认生成高分辨率 1:1 设计母版。不要擅自添加圆角或透明角；移动端平台通常会自行应用主 icon 遮罩。只有用户或参考图明确要求时，才把圆角/透明角烘焙进图像。

### 2. 检查参考图

存在参考图时，必须读取并记录：

- 像素宽高、alpha 通道、透明/半透明/不透明区域。
- 画布外形、圆角类型和半径、透明角、内部安全区。
- 主体身份、决定身份的必要部件、朝向、数量和可见性。
- 区分 `semantic_orientation` 与 `visual_pose`：前者表示左右朝向、上下状态、入口/出口方向等不可随意改变的语义；后者表示允许调整的旋转、俯仰、偏航和透视。
- 元素边界框 `x/y/w/h` 百分比、前后层级、遮挡关系。
- 背景、色彩、光照、材质、阴影、描边、渐变和风格指纹。
- 区分主体 `primary_colors` 与 `accent_colors`：主色决定身份与整体观感，辅助色用于端帽、边缘、局部内层、高光、阴影、小徽标或装饰。
- 允许变化、不允许变化和失败标准。

使用视觉检查工具查看参考图。需要读取尺寸时运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/match_reference_size.ps1 -Info -Paths "<reference-image>"
```

### 3. 建立 App icon 结构化 JSON

按 `references/app-icon-schema.md` 构建 JSON。至少包含：

- `input_mode`
- `canvas`
- `platform_intent`
- `app_identity`
- `style`
- `elements`
- `relationships`
- `pose_variation`
- `accent_color_variation`
- `invariants`
- `allowed_changes`
- `forbidden_changes`
- `failure_criteria`
- `output`
- `layer_split`
- `white_negative_icon`

每个主要元素必须有具体 `identity`、`bounds_percent`、`layer`、`required_traits` 和 `completeness`。不要使用“蓝色物体”“漂亮符号”之类含糊标签。

### 4. 可选双层拆分输出

当用户要求拆分前景层和背景层时，将 `output.mode` 设为 `foreground_background_pair`，并在生成前建立 `layer_split`：

- `foreground_elements`：主元素，以及必须随主元素移动的接触高光、局部光效或前景装饰。
- `background_elements`：背景渐变、云雾、纹理、远景、环境粒子，以及被主元素遮挡区域的合理延续内容。
- `foreground_exclusions`：背景、地面、环境雾和不应随主元素移动的投影。
- `background_exclusions`：主元素、主体轮廓残影、主元素专属高光和重复前景装饰。

双层输出必须生成两张独立图片：

1. **前景层**
   - 保持与最终图完全相同的画布尺寸、主元素位置、比例、姿态和安全区。
   - 仅包含 `foreground_elements`，背景必须为均匀纯色键幕布。不要固定使用绿色；根据主体及半透明元素选择色彩距离最大的键色。
   - 推荐键色：蓝色/青色主体优先 `#ff00ff` 洋红幕；紫红/暖色主体优先 `#00ff00` 绿幕；绿色主体优先 `#ff00ff` 或 `#0000ff`；只有主体不存在相近颜色时才使用对应键色。
   - 主元素及其边缘、高光、阴影、发光和粒子不得使用接近键幕的颜色。
   - 必须先在生成图原始尺寸上使用 `remove_green_screen.ps1` 去绿幕，得到真实透明 PNG；之后才能缩放到最终尺寸。
   - 禁止先缩放色键图再去幕。缩放会把键色混入抗锯齿边缘、半透明高光、发光和阴影，导致污染无法干净删除。
   - 去幕必须处理半透明元素：使用键色优势估算 alpha、反混合键幕颜色并执行通用 despill；将全透明和极低 alpha 像素的隐藏 RGB 清零，避免后续缩放把不可见键色重新插值到边缘；完成后检查边缘、高光、发光和半透明阴影是否残留键色。
   - 尽量不要把大面积半透明环境光、雾、拖尾和粒子放入前景层。若它们不需要随主体移动，应归入背景层；若必须随主体移动，应使用与其颜色完全冲突的键幕。

2. **背景层**
   - 保持与前景层完全相同的画布尺寸。
   - 不得包含主元素、主体残影、空洞或透明区域。
   - 必须合理绘制并填满原本被主元素遮挡的区域，使移除前景层后背景仍为连续、完整、全不透明图像。
   - 必须先在生成图原始尺寸上填充所有透明/半透明区域并得到全不透明背景，再缩放到最终尺寸。
   - 禁止先缩放带透明区域的背景再填充，否则缩放后的半透明边缘会形成暗边、空洞或污染色。
   - 保持最终合成图所需的背景构图、色彩、光照方向和环境氛围。

优先先生成背景层，再基于相同 JSON 生成绿幕前景层。生成前景层时禁止重新构图或改变主元素位置。双层后处理顺序不可颠倒：

1. 前景：选择反差键色 -> 原始色键图 -> 去幕/清理半透明键色污染 -> 透明 PNG -> 缩放到最终尺寸。
2. 背景：原始背景图 -> 填充透明区域为全不透明背景 -> 缩放到最终尺寸。
3. 两层验证尺寸与透明度 -> 生成合成预览。

### 5. 可选极简白色负形透明图标

当用户要求根据前景图生成极简白色负形图标时，将 `white_negative_icon.enabled` 设为 `true`。使用已经去幕并缩放完成的透明前景 PNG 作为语义与轮廓参考，不要使用背景层或合成图。

目标视觉规则：

- 整体为极简单色图标，所有可见像素只能是纯白色 `#ffffff`。
- 背景必须真实透明。
- 禁止描边、阴影、渐变、灰色、彩色、发光、纹理、半透明填充和 3D 材质。
- 外轮廓保持主体最重要的识别特征，但允许简化细碎结构。
- 内部层级通过透明镂空负形表达，例如孔洞、部件间隙、关键分隔和身份定义结构。
- 负形必须足够宽，缩小到目标尺寸后仍可辨识；不要保留会消失的细线或碎孔。
- 不得把整张前景直接填成无内部结构的白色实心块，除非主体本身没有必要的内部识别细节。

生成流程：

1. 分析透明前景的主体外轮廓、必要部件与内部身份特征。
2. 创建负形设计 JSON，明确 `white_fill_regions`、`transparent_negative_regions`、最小负形宽度和禁止删除的身份特征。
3. 使用图像生成工具生成“纯白主体 + 透明负形孔洞”的极简版本。若生成工具无法可靠直接输出 alpha，可使用与白色完全冲突的色键幕，再去幕。
4. 使用 `normalize_white_alpha_icon.ps1` 将所有可见像素强制规范为纯白并保留 alpha。
5. 使用 `check_white_alpha_icon.ps1` 验证只有纯白可见像素和透明像素。

`normalize_white_alpha_icon.ps1` 只负责颜色规范化，不负责创造负形结构。禁止直接对原始彩色前景运行该脚本后交付；如果输入 alpha 中没有必要的内部孔洞，输出会退化为白色实心块，必须先生成或构造负形 alpha 蒙版。

规范化与验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/normalize_white_alpha_icon.ps1 -Source "<negative-icon-alpha>" -Output "<white-negative-icon>"
powershell -ExecutionPolicy Bypass -File scripts/check_white_alpha_icon.ps1 -Path "<white-negative-icon>"
```

### 6. 应用主 icon 设计约束

- 保持 1:1 画布和单一明确视觉焦点。
- 主体应占据足够面积，并在约 48px 缩略图下仍可识别。
- 将关键主体放在中央安全区；除非参考图明确如此，不要让关键部件贴边或被裁切。
- 优先使用 1 个主要符号和少量辅助元素，避免复杂背景、微小装饰、长文本和多个同权重主体。
- 保持主体语义身份。若主体是盾牌、相机、火箭或动物，其决定身份的部件不得缺失或被替换。
- 在 `reference_only` 模式中，默认对主图元素执行可辨识的姿态变化：通常允许约 `8-25°` 平面旋转、轻度俯仰/偏航或从正视变为轻微三分之四视角。变化幅度应足以降低雷同性，但不能造成结构变形、部件遮挡、重心失衡或安全区溢出。
- 姿态变化不得改变语义方向。右箭头不能变成左箭头，向上火箭不能变成向下，车辆行驶方向、扫帚刷头与手柄连接关系、动物头尾方向等必须保持。
- 对文字、数字、品牌标志、旗帜、方向箭头、严格对称徽章和几何精确图形，默认禁止透视扭曲；仅在用户明确要求时旋转。
- 在 `reference_only` 模式中，默认适度改变主体辅助色。优先调整色相邻近或功能相容的点缀色、局部高光色、内侧阴影色和小装饰色，使新图与参考图产生可辨识但协调的配色差异。
- 辅助色变化不得改变主体主色身份。例如蓝色主体仍应以蓝色为主，白色主体仍应以白色为主；不得让点缀色面积或饱和度超过主色并抢占视觉中心。
- 保持材质和明暗语义：高光应比基色更亮，阴影应比基色更暗；金属、玻璃、塑料或织物的辅助色变化不能破坏其材质可读性。
- 对品牌规定色、国旗色、交通/状态语义色和用户明确指定的精确颜色，禁止默认调整。
- 严格保持参考图风格强度。扁平图标不得擅自变为厚重 3D；软 3D 图标不得退化为扁平 SVG。
- 不要生成手机截图、应用界面、icon 网格、商店展示图、设备 mockup、文字说明或外部边框。
- 未明确要求时避免文字。明确要求文字时，记录精确字符串并验证可读性。

### 7. 合并文本改写

在 `reference_plus_text` 模式中，将文本意图分类为：

- `replace`：主体、图形身份、文字或材质替换。
- `modify`：色彩、风格、光照、背景、圆角、尺寸或透明要求调整。
- `preserve`：未被文本覆盖的参考图约束。

替换主体时同步更新 `identity`、`required_traits`、`invariants` 和 `failure_criteria`，避免旧主体规则残留。

### 8. 使用 gpt-image-2 生成

调用可用的图像生成工具，明确指定模型 `gpt-image-2`。将最终 JSON 作为主要提示词依据，并强调：

```text
Generate one mobile App primary icon from this structured JSON.
Preserve every identity, required trait, relationship, invariant, canvas rule,
and failure criterion. Produce a single centered 1:1 icon only.
Do not create UI screens, icon grids, device mockups, or explanatory text.
```

在 `reference_only` 模式中追加：`Create a visibly new pose using moderate rotation or perspective variation, and moderately vary secondary accent colors while preserving primary color identity, semantic orientation, required parts, material hierarchy, contrast, and readability.`

需要透明背景时，不要依赖模型直接输出可靠 alpha。先分析主体 `primary_colors`、`accent_colors`、高光、发光和阴影，再从绿、洋红、蓝、红、黄、青等候选中选择与所有前景颜色距离最大的纯色键幕。蓝青主体通常优先洋红；若同时含紫色/洋红配件，则优先黄色 `#ffff00`，不要使用与任一半透明效果接近的键色。

去幕策略按可靠性排序：

1. 将不需要随主体移动的半透明雾、光晕、拖尾和粒子放入背景层，只对较实心的主体做色键提取。
2. 对主体选择自适应反差键色，并在原始尺寸去幕、反混合、despill、清空透明像素隐藏 RGB 后再缩放。
3. 若本地存在可靠的分割/抠图模型或人工 alpha 蒙版，优先使用蒙版抠图；色键仅作为后备方案。
4. 如果主体与所有候选键色均有大面积重叠，停止使用单色幕，改为蒙版抠图或重新规划前景/背景元素。

双层输出时分别使用以下生成提示约束：

```text
Foreground pass: render only the declared foreground elements on a perfectly uniform selected chroma-key background. Use the exact key color specified in layer_split.key_color. Keep exact canvas, pose, scale, bounds, and lighting. Do not render any background scenery.

Background pass: render a complete fully opaque background with all areas behind the foreground plausibly filled. Do not render the primary subject, its silhouette, ghost, cutout hole, or duplicated foreground decorations.
```

### 9. 后处理

透明 PNG：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remove_green_screen.ps1 -Source "<original-keyed-output>" -Output "<alpha-original-size>" -KeyColor "<selected-key-color>"
powershell -ExecutionPolicy Bypass -File scripts/check_png_transparency.ps1 -Path "<alpha-original-size>"
powershell -ExecutionPolicy Bypass -File scripts/resize_image.ps1 -Source "<alpha-original-size>" -Output "<foreground-512>" -Width 512 -Height 512 -Fit contain -Background "#00000000"
```

背景层先填充再缩放：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/flatten_background.ps1 -Source "<original-background>" -Output "<opaque-original-size>" -FillColor "#ffffff"
powershell -ExecutionPolicy Bypass -File scripts/resize_image.ps1 -Source "<opaque-original-size>" -Output "<background-512>" -Width 512 -Height 512 -Fit cover -Background "#ffffffff"
```

验证双层并生成合成预览：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/compose_layer_pair.ps1 -Foreground "<alpha-foreground>" -Background "<background>" -Output "<composite-preview>"
```

匹配参考图尺寸：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/match_reference_size.ps1 -Reference "<reference>" -Generated "<generated>" -Output "<final>" -Fit cover -Background "#00000000"
```

若用户未指定尺寸，使用 `512×512`。保持 1:1，不得拉伸主体。

### 10. 验证并迭代

最终检查：

- 仅有一个 App 主 icon，不是多图拼贴。
- 最终尺寸、格式、透明度和画布外形符合要求。
- 主体身份、必要部件、数量、方向、层级和关系正确。
- `reference_only` 输出相较参考图具有可辨识的姿态或视角差异，且没有因旋转/透视导致部件缺失、遮挡、变形或裁切。
- 主体辅助色相较参考图具有协调的适度差异；主色身份、材质层级和视觉焦点没有被破坏。
- 缩略图下仍清晰，主视觉没有被裁切或贴边。
- 风格、材质、光照和背景符合 JSON。
- 不含意外文字、水印、设备框、UI 页面或额外 icon。
- 双层输出时，前景层具有真实透明像素，背景层完全不透明，两层尺寸完全一致。
- 前景必须证明是先去幕再缩放；半透明高光、发光、抗锯齿边缘和阴影不得残留明显键色。
- 背景必须证明是先填充再缩放；最终背景不得包含透明或半透明像素。
- 移除前景后，背景没有透明洞、主体残影或被遮挡区域的明显缺失；重新合成后主体位置、边缘和整体观感正确。
- 极简白色负形图标只包含纯白可见像素和真实透明像素；无描边、阴影、渐变、灰色或其他颜色；负形孔洞清晰且主体身份可识别。

任一 `failure_criteria` 命中即判定失败，重新生成或后处理，不能把不合格结果直接交付。

## 脚本

- `scripts/match_reference_size.ps1`：读取尺寸并匹配参考图宽高。
- `scripts/remove_green_screen.ps1`：将绿、洋红、蓝或红色键幕转换为真实 alpha PNG，并清理半透明键色污染。
- `scripts/check_png_transparency.ps1`：验证 PNG 是否具有 alpha 格式和透明像素。
- `scripts/compose_layer_pair.ps1`：验证前景/背景层尺寸与透明度，并生成合成预览。
- `scripts/flatten_background.ps1`：在缩放前将背景透明区域填充为全不透明图像。
- `scripts/resize_image.ps1`：按显式尺寸缩放图像，默认参数为 `512×512`。
- `scripts/normalize_white_alpha_icon.ps1`：将负形图标所有可见像素强制规范为纯白并保留 alpha。
- `scripts/check_white_alpha_icon.ps1`：验证负形图标只包含纯白可见像素与透明像素。
