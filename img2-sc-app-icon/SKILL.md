---
name: img2-sc-app-icon
description: 使用 gpt-image-2 根据文本描述、移动端 App 主图标参考图，或参考图结合文本改写生成 iOS/Android 应用主 icon。适用于 App logo、launcher icon、store icon、圆角方形主图标、参考图重生成、构图参考与变体重组、风格变体、主体替换、固定尺寸输出、透明 PNG，以及将新图拆分为透明前景层、完整背景层和白色负形透明图标；必须先生成结构化 JSON，保持图标身份、语义层级、风格、画布外形与尺寸约束，但 reference_only 默认必须明显重组构图并降低雷同性。拆分输出时从结构化 JSON 中分别提取主要元素和背景信息：先生成带绿幕的主体变体层，本地去绿幕后将主要元素缩小至 70% 并输出 512×512 透明前景层；再生成新的变体背景层并输出 512×512；白色负形图标根据带绿幕的前景层生成，本地去绿幕后输出 72×72 透明 PNG。
---

# img2-sc-app-icon

## 核心目标

生成可作为移动端 App 应用主 icon 的单张 1:1 图像。未指定尺寸时，最终输出默认使用 `512×512`。主 icon 必须在小尺寸下清晰可辨，拥有一个明确视觉中心，避免像普通 UI 功能图标、插画海报或复杂场景。

始终先判定输入模式并构建结构化 JSON，再调用图像生成工具并明确指定 `gpt-image-2`。详细 JSON 字段与检查清单见 `references/app-icon-schema.md`。

## 输入模式

默认意图：只要用户提供了参考图、图片附件、图片路径或 `Files mentioned by the user` 中的图片资源，并且没有明确说“只分析”“只输出 JSON”“不要生成”或“先别生成”，就默认按参考图生成新的 App icon。不要追问用户想做什么，不要只给分析结论或处理选项。

1. `text_only`
   - 仅有文字描述。
   - 将文字拆解为 App icon 专用结构化 JSON。
   - 仅在用户明确要求时固定像素尺寸、透明 PNG、圆角遮罩或平台规范。

2. `reference_only`
   - 用户仅提供参考图，或没有提出明确改写要求。
   - 默认任务是生成新的 App icon：先提炼参考图 JSON，再生成语义身份、风格强度和主次层级一致，但构图、姿态、位置关系、局部造型、配色和装饰布局明显不同的新变体。不要默认保持参考图主构图。
   - 图片-only、附件-only、路径-only 的输入都属于生成请求；除非用户明确禁止生成，不要停在分析、不要列处理选项、不要要求用户补充描述。
   - 默认匹配参考图画布外形、透明遮罩和主要图标身份；最终尺寸仍默认为 `512×512`，仅在用户明确要求时匹配参考图原尺寸。
   - 默认根据主体数量生成明显变体：单主体元素要在保持识别性的前提下产生明显造型、姿态、随机方向角度旋转、大小缩放、重心移动和配色变化；多元素主体要在保持主元素识别性的前提下，对元素位置关系、方向角度、大小比例、重叠顺序、主辅距离和配色做明显重组。
   - 每次生成都必须按规则随机抽取一组变化参数，并写入 `composition_variation.randomization`：至少同时包含角度、缩放、位置/重心、配色、装饰布局中的 3 项变化。不要复用上一次生成的构图参数，也不要输出与参考图近似的默认姿态。
   - 默认对主体元素和辅助元素做可辨识但受控的配色变化，例如点缀色、端帽、局部高光、内侧阴影、小型装饰色或辅助元素主色；必须保持主元素身份、明暗层级、材质关系和整体对比。
   - 默认对装饰性点缀做随机变换，例如 sparkle、光点、星芒、小徽标、粒子、局部高光、背景小装饰、扫光碎片等；可随机调整数量、位置、大小、角度、透明度、亮度和配色，但不能抢占主视觉或改变图标语义。

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
- 单张合成图 `composite` 默认背景必须填满整个 1:1 画布，并且最终图像应为全不透明背景；不要留下透明角、透明洞、空白边或未绘制区域，除非用户明确要求透明 PNG 或参考图本身必须保留透明遮罩。
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

脚本路径必须相对 `img2-sc-app-icon` skill 目录解析；如果当前工作目录是仓库根目录，使用 `img2-sc-app-icon/scripts/match_reference_size.ps1`。当参考图是 WebP 或 `System.Drawing` 不支持的格式时，允许用 ImageMagick `magick identify` 或其他结构化图像库读取尺寸，不要把本地元数据读取失败当作生图阻塞。

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
- `decorative_variation`
- `invariants`
- `allowed_changes`
- `forbidden_changes`
- `failure_criteria`
- `output`
- `layer_split`
- `white_negative_icon`

每个主要元素必须有具体 `identity`、`bounds_percent`、`layer`、`required_traits` 和 `completeness`。不要使用“蓝色物体”“漂亮符号”之类含糊标签。

必须判断主体结构是 `single_primary_element` 还是 `multiple_elements`，并写入 `composition_variation`。单主体强调造型、姿态、旋转、缩放和配色差异；多元素强调主元素可识别，同时允许元素之间的位置、角度、大小和配色重新组织。每次生成必须在 JSON 中写入本次随机选择的变化参数，不得省略。

必须识别装饰性点缀并写入 `decorative_variation`。点缀包括但不限于星芒、sparkle、光点、粒子、小型状态徽标、背景亮斑、边缘高光、扫光碎片和非语义装饰。它们可以随机变化，但必须保持为辅助层。

参考图提炼 JSON 时必须先完成前景/背景元素划分，并写入 `layer_split.foreground_elements`、`layer_split.background_elements`、`foreground_exclusions` 和 `background_exclusions`。后续前景图和背景图必须严格遵守 JSON 中的元素归属；同一元素不得同时出现在最终前景层和背景层。若星光、白色炫光、扫光碎片或徽标已归入前景层，背景层不得再次生成或保留这些元素；若泡泡、环境光点、环形光带已归入背景层，前景层不得包含它们。

### 4. 可选双层拆分输出

当用户要求拆分前景层和背景层时，将 `output.mode` 设为 `foreground_background_pair`，并在生成前建立 `layer_split`。拆分输出不再从合层图裁切主体，而是从结构化 JSON 中分别提取主要元素和背景信息，按同一套身份、风格、光照和变体参数生成可组合的独立层。

前景层必须来自结构化 JSON 中的 `foreground_elements` / 主要元素定义，生成时使用均匀纯色绿幕/键幕背景，得到 `foreground_keyed_source`。背景层必须来自结构化 JSON 中的 `background_elements` / 背景信息，生成新的变体背景层，不能包含主要元素、主体残影或主体形状空洞。

生成前必须核对 `foreground_elements` 与 `background_elements` 没有重复元素。若发现同一 sparkle、bubble、glint、sweep、shadow、badge、主件或辅助件同时被列入前景与背景，必须先修正 JSON 再生成。

严禁用本地粗略 mask、手绘多边形遮罩、简单抠原参考图、局部旋转/缩放参考图等方式冒充“主体变体层”。如果图像生成工具不可用，必须停止并说明无法生成，不得交付本地粗处理 fallback。

- `foreground_elements`：主元素，以及必须随主元素移动的接触高光、局部光效或前景装饰。
- `background_elements`：背景渐变、云雾、纹理、远景、环境粒子，以及被主元素遮挡区域的合理延续内容。
- `foreground_exclusions`：背景、地面、环境雾和不应随主元素移动的投影。
- `background_exclusions`：主元素、主体轮廓残影、主元素专属高光和重复前景装饰。

双层输出必须产出三类文件：带绿幕主体变体层、透明前景图、完整背景图；如果要求负形图标，再产出白色负形透明图标。

1. **前景层**
   - 必须从结构化 JSON 中提取主要元素、主辅关系、姿态、材质、边缘、高光、阴影和点缀规则，生成一个带绿幕/键幕背景的主体变体层 `foreground_keyed_source`。
   - `foreground_keyed_source` 必须是干净的主体变体渲染：主体边缘连续、无硬切多边形边、无原背景色块、无棋盘格、无矩形残片、无被 mask 吃掉的部件；绿幕/键幕必须只出现在背景区域。
   - `foreground_keyed_source` 中主要元素内部不得把键幕色当作占位空洞。文件夹开口、盒内空间、卡片之间的可见缝隙、徽章内凹槽、工具部件间隙等，只要不是 JSON 明确标记为透明负形/真实镂空，就必须由主体自己的内侧颜色、背面颜色、阴影或遮挡后的合理内容填满。生成提示中必须明确：key color may appear only outside the foreground subject, never inside subject holes or folder/card openings unless explicitly declared transparent.
   - 键色不要固定使用绿色；根据主体及半透明元素选择色彩距离最大的键色。推荐键色：蓝色/青色主体优先 `#ff00ff` 洋红幕；紫红/暖色主体优先 `#00ff00` 绿幕；绿色主体优先 `#ff00ff` 或 `#0000ff`；只有主体不存在相近颜色时才使用对应键色。若用户明确要求“绿幕”，优先使用 `#00ff00`，但必须检查主体中没有大面积近似绿色。
   - 必须先在原始生成尺寸上本地去绿幕/去键色，得到真实透明 PNG；之后将主要元素整体缩小至 70% 大小并居中放入透明画布，再将整体画布缩放/规范为最终 `512×512`。
   - 禁止先缩放色键图再去幕。缩放会把键色混入抗锯齿边缘、半透明高光、发光和阴影，导致污染无法干净删除。
   - 去幕必须先判断哪些部分本身应该不透明。盾牌、扫帚、刷毛、手柄、主体徽章等实心/玻璃拟物主体通常应保持原有实度，不要因为键幕背景而把整件主体反混合成半透明。只有明确应为半透明的炫光、发光、抗锯齿边缘、柔和扫光或阴影才使用键色优势估算 alpha、反混合键幕颜色并执行 despill。
   - 对主体不透明、只有星星/白色炫光边缘污染的前景图，优先使用结构化图像库在原始尺寸清除键幕：从画布边缘 flood-fill 识别与键色相连的背景区域并置透明，同时把所有未被 JSON 声明为主体材质的断开 key-like 色块也置透明。夹在卡片、箭头、文件夹、徽章等独立前景部件之间的紫色/洋红/绿幕区域属于背景窗口，不属于主体内部材质，最终必须透明；随后仅对可见的洋红/绿幕溢色边缘做局部去溢色，不要全局降低主体 alpha。
   - 区分“断开的键幕色块”和“主体内部材质”：文件夹内壁、卡片背面、箭头内侧、徽章凹槽等若在 JSON 中属于主体结构，必须在 keyed source 中用主体颜色、内侧阴影或合理遮挡内容填满，不得使用键色占位；如果它们意外变透明，必须回到原始尺寸修复/填色再缩放。若主体真实需要紫色/洋红材质，必须选择其他键色并在 JSON 中声明该材质，不得继续使用相近键色。
   - 去幕后必须检查主体内部是否出现透明洞或被键色误删的空白区。若文件夹内部、卡片背后、箭头内侧、徽章凹槽等应为主体材质/内侧阴影的区域变成透明，必须先在原始尺寸修复/填色，再缩放到最终前景层；不得把内部透明洞交付为前景层。
   - 若可用，优先使用 Pillow 或等价结构化图像库完成上述连通键幕清除、局部 despill、透明 PNG 输出和 checker 预览；PowerShell 逐像素脚本可作为后备，但大尺寸 keyed source 可能较慢。
   - 将全透明和极低 alpha 像素的隐藏 RGB 清零，避免后续缩放把不可见键色重新插值到边缘；完成后检查星星周围、白色炫光、玻璃边缘和扫光是否残留键色。
   - 前景最终文件必须为真实透明背景，主要元素相对画布约为 70% 大小，并本地验证尺寸为 `512×512`。如果尺寸不是 `512×512`，必须本地缩放后再验证。
   - 前景透明层不得残留键幕颜色、参考图背景色块、粗糙遮罩边、断裂手柄、缺失盾牌/刷头/关键部件或不连续 alpha 边缘。最终透明 PNG 中只要仍存在未声明为主体材质的可见紫色/洋红/绿幕 key-like 像素，即判定失败，必须重新清理或重新生成 keyed source。

2. **背景层**
   - 必须从结构化 JSON 中提取背景信息、背景颜色、渐变、纹理、环境光、粒子和装饰规则，生成新的变体背景层。
   - 背景层必须像完整 App icon 背景，而不是临时占位渐变、空白色块或随意圆点；背景装饰必须来自 JSON 的 `background_elements` / `decorative_variation`，并与前景风格统一。
   - 保持与前景层完全相同的画布尺寸和对齐方式。
   - 不得包含主元素、主体残影、主体形状空洞或透明区域。
   - 背景必须是完整、连续、全不透明图像，且填满整个 1:1 画布。
   - 必须先在原始生成尺寸上得到完整不透明背景，再缩放到最终 `512×512`。
   - 保持最终合成图所需的背景风格、色彩体系、光照逻辑和环境氛围；`reference_only` 下背景光带、粒子、泡泡、glint 等布局也应可见变化，不要默认保持参考图背景构图或机械复制装饰位置。
   - 背景最终文件必须本地验证为 `512×512` 且完全不透明。

双层后处理顺序不可颠倒：

1. 建立结构化 JSON，明确 `foreground_elements`、`background_elements`、`composition_variation`、`decorative_variation` 和输出尺寸。
2. 前景：从 JSON 提取主要元素 -> 生成带绿幕/键幕的主体变体层 `foreground_keyed_source` -> 原始尺寸本地去幕/清理键色污染并输出透明 PNG -> 将透明 PNG 的主要元素缩小至 70% 并居中放入透明画布 -> 缩放/规范到 `512×512` -> 验证尺寸和 alpha。不得先缩放 keyed source 再去幕。
3. 背景：从 JSON 提取背景信息 -> 生成新的变体背景层 -> 缩放/规范到 `512×512` -> 验证尺寸和不透明度。
4. 两层验证尺寸与透明度 -> 生成合成预览。

### 5. 可选极简白色负形透明图标

当用户要求根据前景图生成极简白色负形图标时，将 `white_negative_icon.enabled` 设为 `true`。必须根据带绿幕的前景层 `foreground_keyed_source` 生成极简白色负形图标：保留主要元素轮廓和必要内部负形结构，使用纯白主体置于均匀键幕背景上，再本地去绿幕/去键色变成透明背景，最后将整张图像画布缩放到 `72×72`。

目标视觉规则：

- 整体为极简单色图标，所有可见像素只能是纯白色 `#ffffff`。
- 背景必须真实透明。
- 禁止描边、阴影、渐变、灰色、彩色、发光、纹理、半透明填充和 3D 材质。
- 外轮廓保持主体最重要的识别特征，但允许简化细碎结构。
- 内部层级通过透明镂空负形表达，例如孔洞、部件间隙、关键分隔和身份定义结构。
- 负形必须足够宽，缩小到目标尺寸后仍可辨识；不要保留会消失的细线或碎孔。
- 负形图必须保留可识别的内部特征负形结构。对于盾牌+扫帚/刷子图标，至少应保留盾牌内外层分隔、刷头/手柄连接分隔、刷毛组分隔或等价身份特征；不得只交付没有内部透明结构的白色外轮廓。
- 负形图最终尺寸规则不同于前景层：对规范化后的负形图整张画布直接缩放到 `72×72`，主要元素不再额外缩小，不做 `70%` 缩放，不做 trim 后缩小主体再居中加边距。若源负形图主体大小不合适，必须回到负形生成/规范化阶段调整构图，而不是在最终 72 输出前额外缩小主体。
- 不得把整张前景直接填成无内部结构的白色实心块，除非主体本身没有必要的内部识别细节。

生成流程：

1. 分析透明前景的主体外轮廓、必要部件与内部身份特征。
2. 创建负形设计 JSON，明确 `white_fill_regions`、`transparent_negative_regions`、最小负形宽度和禁止删除的身份特征。
3. 使用图像生成工具基于 `foreground_keyed_source` 生成“纯白主体 + 负形孔洞 + 均匀键幕背景”的极简版本，不直接依赖模型输出 alpha。
4. 使用 `normalize_white_alpha_icon.ps1` 将所有可见像素强制规范为纯白并保留 alpha。
5. 将规范化后的整张负形图像画布缩放到 `72×72`，不裁切主体后再缩小，不添加额外安全边距。
6. 使用 `check_white_alpha_icon.ps1` 验证只有纯白可见像素和透明像素，并验证背景真实透明。

`normalize_white_alpha_icon.ps1` 只负责颜色规范化，不负责创造负形结构。禁止直接对原始彩色前景运行该脚本后交付；如果输入 alpha 中没有必要的内部孔洞，输出会退化为白色实心块，必须先生成或构造负形 alpha 蒙版。
禁止把前景 alpha 直接填充成白色后当作负形图标交付。白色负形图必须保留足够的内部透明负形结构，例如盾牌内外层分隔、扫帚刷头/手柄分隔、垃圾桶桶身槽线等决定身份的结构；如果 72×72 下变成白色土豆块或无法识别，判定失败。

规范化与验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/normalize_white_alpha_icon.ps1 -Source "<negative-icon-alpha>" -Output "<white-negative-icon>"
powershell -ExecutionPolicy Bypass -File scripts/check_white_alpha_icon.ps1 -Path "<white-negative-icon>"
```

### 6. 应用主 icon 设计约束

- 保持 1:1 画布和单一明确视觉焦点。
- 单张合成图默认使用完整背景填满整个画布。背景可以是纯色、渐变或插画化背景，但必须覆盖到四边，不得透明、留白、破洞或只围绕主体局部绘制。
- 主体应占据足够面积，并在约 48px 缩略图下仍可识别。
- 将关键主体放在中央安全区；除非参考图明确如此，不要让关键部件贴边或被裁切。
- 优先使用 1 个主要符号和少量辅助元素，避免复杂背景、微小装饰、长文本和多个同权重主体。
- 保持主体语义身份。若主体是盾牌、相机、火箭或动物，其决定身份的部件不得缺失或被替换。
- 在 `reference_only` 模式中，默认对主图元素执行可辨识且明显的变体变化。单主体元素必须改变至少 3 个维度：轮廓/局部造型、姿态/视角、方向角度、大小比例、重心位置、配色或装饰布局。通常要求 `18-42°` 平面旋转或中度俯仰/偏航，允许三分之四视角，缩放约 `0.78-1.25x`，重心移动约 `6-16%` 安全区内距离；仅做 `12°` 以内旋转、轻微缩放或换几个高光位置视为变化不足。
- 多元素主体必须先识别主元素和辅助元素。保持主元素身份、必要部件、语义方向和小尺寸可读性；必须明显重组各元素之间的位置关系、距离、重叠程度、方向角度、大小比例和配色。通常要求主元素约 `12-32°` 旋转，辅助元素约 `18-48°` 旋转，元素约 `0.72-1.28x` 缩放，主辅距离或重叠面积变化至少 `15%`，并在安全区内产生可见的相对位置重排。
- 每次 `reference_only` 生成都必须随机化上述参数。即使同一参考图连续生成多次，也应得到不同的角度、位置、缩放、重叠、局部造型、背景布局或配色组合；禁止使用固定模板姿态。仅重绘材质、提高精度、轻微调整颜色或照搬参考图元素位置不算合格变体。
- 变化幅度应足以让缩略图下也能看出不是同一张图，但不能造成结构变形、关键部件遮挡、主次关系混乱、重心失衡或安全区溢出。
- 姿态变化不得改变语义方向。右箭头不能变成左箭头，向上火箭不能变成向下，车辆行驶方向、扫帚刷头与手柄连接关系、动物头尾方向等必须保持。
- 对文字、数字、品牌标志、旗帜、方向箭头、严格对称徽章和几何精确图形，默认禁止透视扭曲；仅在用户明确要求时旋转。
- 在 `reference_only` 模式中，默认改变主体和辅助元素的配色。优先调整色相邻近或功能相容的点缀色、局部高光色、内侧阴影色、小装饰色、辅助元素主色或背景色，使新图与参考图产生明显但协调的配色差异。
- 辅助色变化不得改变主体主色身份。例如蓝色主体仍应以蓝色为主，白色主体仍应以白色为主；不得让点缀色面积或饱和度超过主色并抢占视觉中心。
- 装饰性点缀默认随机变化。可调整点缀数量、位置、大小、旋转角度、透明度、亮度、颜色、形状细节和层级，但必须服务于主体可读性。点缀不得遮挡主元素、不得变成新的主元素、不得新增文字或误导性符号。
- 如果参考图里已有 sparkle、光点或小粒子，不要机械复制原位置；至少随机改变其中一部分点缀的位置、大小、角度或亮度。也可以在不破坏简洁性的前提下添加少量同风格点缀或删除部分非关键点缀。
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

首次调用不要把完整 schema、长篇检查清单或无关说明整段塞进生图提示词；提示词应只包含结构化 JSON 中对本次结果真正生效的部分：app 身份、画布与输出、主要元素、层级关系、随机变体参数、不变性和失败标准。如果服务端因长提示或解析问题失败，允许重试一次精简提示，但必须保留同一套身份、主辅关系、随机变化、尺寸、安全区、背景填满、不含文字/设备 mockup 等硬约束，并在交付时说明使用了精简提示。

```text
Generate one mobile App primary icon from this structured JSON.
Preserve every identity, required trait, relationship, invariant, canvas rule,
and failure criterion. Produce a single centered 1:1 icon only.
Do not create UI screens, icon grids, device mockups, or explanatory text.
```

在 `reference_only` 模式中追加：`Create a visibly new App icon variant, not a cleaned-up copy. Preserve semantic identity, style family, required parts, hierarchy, material readability, contrast, safe-area fit, and small-size recognition, but do not preserve the reference composition by default. Randomly sample a fresh set of variation parameters for this generation; do not reuse the reference pose or any previous default template. Change at least three of these dimensions in a visible way: silhouette/local shape, pose/view angle, rotation, scale, center of mass, relative element positions, overlap order, accent colors, background layout, and decorative layout. If the subject is a single primary element, introduce clear but readable shape, pose, random direction-angle rotation, scale, center-shift, and color variation. If the subject has multiple elements, preserve the main element identity while visibly reorganizing element positions, direction angles, scale relationships, overlap, spacing, and colors. Randomly vary decorative accents such as sparkles, light dots, particles, badges, small highlights, background glints, and shine fragments by changing their count, position, scale, angle, opacity, brightness, color, or shape details while keeping them secondary. Reject a result that only makes minor color/highlight changes or keeps the same silhouette, pose, overlap, and element placement as the reference. For composite output, fill the entire 1:1 canvas with an opaque background unless transparent PNG is explicitly requested. Preserve semantic orientation and required parts.`

需要透明背景时，不要依赖模型直接输出可靠 alpha。先分析主体 `primary_colors`、`accent_colors`、高光、发光和阴影，再从绿、洋红、蓝、红、黄、青等候选中选择与所有前景颜色距离最大的纯色键幕。蓝青主体通常优先洋红；若同时含紫色/洋红配件，则优先黄色 `#ffff00`，不要使用与任一半透明效果接近的键色。

去幕策略按可靠性排序：

1. 将不需要随主体移动的半透明雾、光晕、拖尾和粒子放入背景层，只对较实心的主体做色键提取。
2. 对主体选择自适应反差键色，并在原始尺寸去幕、反混合、despill、清空透明像素隐藏 RGB 后再缩放；默认移除所有 key-like 像素，包括不与画布边缘连通但未被 JSON 声明为主体材质的断开色块。
3. 若本地存在可靠的分割/抠图模型或人工 alpha 蒙版，优先使用蒙版抠图；色键仅作为后备方案。
4. 如果主体与所有候选键色均有大面积重叠，停止使用单色幕，改为蒙版抠图或重新规划前景/背景元素。

双层输出时分别使用以下生成提示约束：

```text
Foreground pass: extract the declared primary foreground elements from the structured JSON and render a new subject variant on a perfectly uniform selected chroma-key background. Use the exact key color specified in layer_split.key_color. Do not render any background scenery. The key color may appear only in background gaps outside the declared foreground elements. Do not use the key color as a placeholder inside subject materials, folder openings, card backs, badge grooves, or tool part gaps unless JSON explicitly marks that region as transparent. Preserve subject identity, required traits, semantic orientation, material readability, and decorative rules.

Background pass: extract the background description from the structured JSON and render a new complete fully opaque background variant. Do not render the primary subject, its silhouette, ghost, cutout hole, or duplicated foreground decorations.

White negative icon pass: use the foreground keyed source as the visual reference and render a minimal pure-white negative-space icon on a perfectly uniform selected chroma-key background. Preserve the subject silhouette and essential internal negative-space identity features. Do not render shadows, gradients, gray pixels, texture, glow, or 3D material.
```

### 9. 后处理

透明 PNG：

```powershell
& "D:\SD\Python\python.exe" scripts/clean_keyed_opaque_foreground.py --source "<original-keyed-output>" --output "<alpha-original-size>" --preview "<checker-preview>" --key "<selected-key-color>"
powershell -ExecutionPolicy Bypass -File scripts/remove_green_screen.ps1 -Source "<original-keyed-output>" -Output "<alpha-original-size>" -KeyColor "<selected-key-color>"
powershell -ExecutionPolicy Bypass -File scripts/check_png_transparency.ps1 -Path "<alpha-original-size>"
powershell -ExecutionPolicy Bypass -File scripts/resize_image.ps1 -Source "<alpha-original-size>" -Output "<foreground-70pct-512>" -Width 512 -Height 512 -Fit contain -ScalePercent 70 -Background "#00000000"
& "D:\SD\Python\python.exe" scripts/clean_keyed_opaque_foreground.py --source "<foreground-70pct-512>" --output "<foreground-70pct-512-clean>" --preview "<foreground-clean-checker-preview>" --key "<selected-key-color>" --alpha-input
```

若有 Pillow 可用，并且前景主体应保持不透明，只是星星/白色炫光周围存在键色污染，则使用“边缘连通键幕清除 + 断开 key-like 色块清除 + 局部去溢色”的 Pillow 流程替代全局半透明反混合：先从原始 keyed source 输出 `<alpha-original-size>`，再对这个透明 PNG 裁切/缩放到 `<foreground-70pct-512>`。不要对缩放后的 keyed source 做去幕，也不要把盾牌、扫帚、文件夹、卡片、箭头等主体整体变成半透明；未声明为主体材质的紫色/洋红 key-like 像素必须在透明 PNG 中变为透明。
缩放可能把不可见或低 alpha key 色重新插值到边缘；因此缩放后的 `512×512` 前景层也必须用 `--alpha-input` 模式再次清除可见 key-like 像素，并重新验证。

背景层先填充再缩放：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/flatten_background.ps1 -Source "<original-background>" -Output "<opaque-original-size>" -FillColor "#ffffff"
powershell -ExecutionPolicy Bypass -File scripts/resize_image.ps1 -Source "<opaque-original-size>" -Output "<background-512>" -Width 512 -Height 512 -Fit cover -Background "#ffffffff"
```

白色负形图标先去幕再缩放到 `72×72`：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remove_green_screen.ps1 -Source "<white-negative-keyed>" -Output "<white-negative-alpha-original-size>" -KeyColor "<selected-key-color>"
powershell -ExecutionPolicy Bypass -File scripts/normalize_white_alpha_icon.ps1 -Source "<white-negative-alpha-original-size>" -Output "<white-negative-normalized>"
powershell -ExecutionPolicy Bypass -File scripts/resize_image.ps1 -Source "<white-negative-normalized>" -Output "<white-negative-72>" -Width 72 -Height 72 -Fit stretch -Background "#00000000"
powershell -ExecutionPolicy Bypass -File scripts/check_white_alpha_icon.ps1 -Path "<white-negative-72>"
```

负形图禁止使用 `-ScalePercent`，也禁止先 `trim` 主体再缩小到小于整张画布的尺寸。最终输出是整张图像缩放到 `72×72`，不是把主要元素缩小后放入 `72×72` 画布。

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
- 单张合成图背景必须填满整个画布并覆盖到四边；除非用户明确要求透明，否则不得出现透明区域、空白边、透明洞或局部未绘制背景。
- 主体身份、必要部件、数量、方向、层级和关系正确。
- `reference_only` 输出相较参考图具有可辨识的造型、姿态、角度、缩放、位置或配色差异，且没有因变化导致部件缺失、遮挡、变形、裁切或主次关系混乱。
- 本次生成的随机变化参数已体现在结果中；如果角度、位置、缩放、重叠和配色都接近参考图或上一次输出，判定失败。
- `reference_only` 必须至少体现 3 个独立变化维度。若只做轻微换色、重绘材质、调整高光、增加少量点缀，或主体轮廓/姿态/重叠/位置关系仍接近参考图，判定失败。
- 单主体元素的造型/姿态/角度/缩放/配色变化足够明显但仍可识别；多元素主体的主元素仍明确，辅助元素的位置、方向、大小或配色变化没有破坏语义关系。
- 主体和辅助元素配色相较参考图具有协调的可辨识差异；主元素身份、材质层级和视觉焦点没有被破坏。
- 装饰性点缀相较参考图存在可见随机变化，例如数量、位置、大小、角度、透明度、亮度或配色变化；但点缀不得遮挡主元素、抢占视觉中心或改变图标语义。
- 缩略图下仍清晰，主视觉没有被裁切或贴边。
- 风格、材质、光照和背景符合 JSON。
- 不含意外文字、水印、设备框、UI 页面或额外 icon。
- 双层输出时，前景层具有真实透明像素，背景层完全不透明，两层尺寸完全一致。
- 双层输出时，前景层和背景层必须严格遵守 JSON 元素划分；同一元素不得同时出现在两层。若前景已包含星光、白色炫光、扫光碎片、徽标或主体附着效果，背景层重复出现即判定失败。
- 双层输出时，前景层必须来自结构化 JSON 的主要元素定义，并能说明 `structured_json.foreground_elements -> foreground_keyed_source -> local_key_removed_alpha -> foreground_70pct_512` 的来源链路。
- 前景必须证明是先在原始/工作分辨率去幕，再将主要元素缩小至 70% 并输出 `512×512` 透明 PNG；半透明高光、发光、抗锯齿边缘和阴影不得残留明显键色。
- 前景主要元素内部不得出现由键幕误删导致的透明洞。文件夹开口、盒内区域、卡片背后、箭头内侧、徽章凹槽等未被 JSON 标记为透明负形的区域必须有合理填色或内侧阴影；出现内部透明空洞即判定失败。
- 前景不得出现手绘多边形 mask 痕迹、原参考图背景残片、矩形色块、主体断裂、主体缺件、明显锯齿硬边或局部被错误透明化；出现任一项即失败。
- 背景必须证明来自结构化 JSON 的背景信息，并生成新的完整变体背景层；最终背景尺寸为 `512×512`，不得包含透明或半透明像素、主体残影、主体形状空洞或重复前景装饰。
- 背景不得是无设计含义的占位渐变或随机圆点；必须和 JSON 中的背景风格、光照、配色及装饰规则一致。
- 背景层没有透明洞、主体残影、主体形状空洞或被遮挡区域的明显缺失；与前景重新合成后主体位置、边缘和整体观感正确。
- 极简白色负形图标基于带绿幕前景层生成，先本地去幕变成透明背景，再将整张图像画布缩放到 `72×72`；只包含纯白可见像素和真实透明像素；无描边、阴影、渐变、灰色或其他颜色；负形孔洞清晰且主体身份可识别。
- 极简白色负形图标不得只是前景 alpha 的白色实心轮廓；必须包含足够大的透明负形孔洞/分隔结构，并保留可识别的内部特征。若看起来像白色土豆块、主体身份不可读、盾牌/工具/刷毛等内部身份结构缺失，判定失败。
- 极简白色负形图标不得在最终输出前额外缩小主要元素。若对主体做 trim、thumbnail、ScalePercent 或额外留白，导致主体比整张 `72×72` 画布明显偏小，判定失败。

任一 `failure_criteria` 命中即判定失败，重新生成或后处理，不能把不合格结果直接交付。

## 脚本

- `scripts/match_reference_size.ps1`：读取尺寸并匹配参考图宽高。
- `scripts/clean_keyed_opaque_foreground.py`：Pillow 前景去幕流程；适合主体应保持不透明、只有星星/白色炫光边缘残留键色或部件间存在断开 key-like 色块的情况；应从原始 keyed source 清除边缘连通键幕和未声明为主体材质的断开 key-like 色块，局部去溢色，先输出原始尺寸透明 PNG，再缩放。
- `scripts/remove_green_screen.ps1`：将绿、洋红、蓝或红色键幕转换为真实 alpha PNG，并清理半透明键色污染；适合主体确实带有半透明边缘/发光的情况。
- `scripts/check_png_transparency.ps1`：验证 PNG 是否具有 alpha 格式和透明像素。
- `scripts/compose_layer_pair.ps1`：验证前景/背景层尺寸与透明度，并生成合成预览。
- `scripts/flatten_background.ps1`：在缩放前将背景透明区域填充为全不透明图像。
- `scripts/resize_image.ps1`：按显式尺寸缩放图像，默认参数为 `512×512`，支持 `-ScalePercent 70` 将主体缩小后居中放入目标画布。
- `scripts/normalize_white_alpha_icon.ps1`：将负形图标所有可见像素强制规范为纯白并保留 alpha。
- `scripts/check_white_alpha_icon.ps1`：验证负形图标只包含纯白可见像素与透明像素。
