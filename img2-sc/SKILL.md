---
name: img2-sc-all
description: 根据文本描述、参考图，或参考图结合文本描述生成图像。使用时先判定输入模式：纯文本生图时，将用户文本拆解成结构化 JSON 提示词，再依据 JSON 生成新图像，并特别检查用户是否明确要求固定尺寸或透明 PNG；参考图生图时，从参考图提炼结构化 JSON 提示词，记录画布、画布外形/圆角类型与大小、透明遮罩、风格指纹、可见元素、图标/形状身份、位置、层级、不变性约束、允许变化范围和失败标准；对横向/纵向组合资源或 sprite strip，识别整体透明画布、每个子图块的真实像素尺寸、正方形或非正方形圆角矩形形状、圆角、间距、徽标叠加和逐块不变性；多张同尺寸参考图疑似帧动画资源时，识别序列帧、静态底图、运动元素、帧序号、位移轨迹和逐帧不变性；参考图结合文本描述生图时，先提炼参考图 JSON，再从文本中提取关键语义（视觉风格、色彩、外形描述、主体替换、材质、背景、尺寸、透明要求等）并合并/替换到 JSON。之后使用 image_generation 工具并指定 gpt-image-2 模型，根据最终 JSON 生成新图像；如果需要透明背景，必须先本地去绿幕得到真实 alpha PNG，再把透明 PNG 调整为目标尺寸。适用于文本生图、参考图重生成、复刻构图、横向 sprite/组合图资源识别、帧动画图片资源识别、参考图+文字改写、生成相似但不雷同的图、保持内容元素/布局/风格/图标身份/画布外形/尺寸一致且输出透明 PNG 的任务。
---

# img2-sc-all

## 概述

使用这个 skill 时，先把用户输入转成结构化 JSON 提示词，再依据 JSON 生成新图像。输入可能是纯文本、参考图，或参考图结合文本描述。生成过程必须保持 JSON 中定义的关键语义、图标身份、元素位置、元素完整性、视觉风格、画布外形和输出要求。对参考图任务，默认生成“语义一致、风格一致、布局接近，但造型和颜色有较明显变化”的新变体，而不是近似复制；对纯文本任务，默认以用户描述为准，不强制继承参考图尺寸或透明背景，除非用户明确要求。

## 默认意图判定

- 当用户消息只包含图片、附件路径、`Files mentioned by the user` 中的图片资源，或图片加极少量上下文，而没有写“只分析 / 只输出 JSON / 不要生成 / 先别生成”时，必须判定为 `reference_only` 重生成请求。
- `reference_only` 的默认目标是“语义一致、风格一致、布局接近，但造型和颜色有较明显变化”的新图，并默认匹配参考图的像素尺寸、画布外形、透明遮罩和主要图标身份。
- 不要因为用户没有额外文字目标而追问“想做哪种处理”。不要回复可选项列表。直接读取参考图、提炼 JSON、生成新变体、后处理并验证。
- 如果连续收到多张单独图片，每一张都按新的 `reference_only` 任务处理；除非用户明确说明它们属于同一组、同一序列帧、或要合并参考。
- 只有在参考图路径不可读、附件缺失、生成工具不可用、触发政策限制，或用户明确要求仅分析时，才可以停下来说明原因或询问下一步。

## 工作流

1. 判定输入模式。
   - `text_only`：用户只提供文本描述，没有参考图。必须把文本拆解为结构化 JSON 提示词，再依据 JSON 生成新图像。
   - `reference_only`：用户提供参考图，没有额外改写文本，或只贴图/只列出图片文件路径。必须自动把参考图提炼成结构化 JSON 提示词，再依据 JSON 直接生成语义一致但不雷同的新变体；不得停在分析、不得列出处理选项、不得要求用户再补充文字描述，除非参考图无法读取或政策/工具限制导致不能生成。
   - `reference_plus_text`：用户同时提供参考图和文本描述。必须先从参考图提炼基础 JSON，再从文本中提取关键语义并合并/替换到基础 JSON，最后依据合并后的 JSON 生成新图像。
   - 对任何模式，都要检查用户是否明确要求固定尺寸、透明 PNG、圆角/遮罩、输出格式、背景颜色、文字内容或主体数量。只有明确要求或参考图本身约束时，才强制这些输出条件。

2. 如果存在参考图，先检查参考图。
   - 使用可用的视觉检查工具识别主体、构图、视角、光照、色彩、背景、文字、材质和所有显著对象。
   - 记录参考图像素尺寸。如果无法直接读取元数据，运行 `scripts/match_reference_size.ps1 -Info -Paths <reference-image>`。
   - 识别画布外形和透明遮罩。必须判断参考图是 `circle`、`rounded_square`、`rounded_rectangle`、`pill`、`full_rectangle`、`transparent_freeform` 还是其他形状。
   - 检测参考图 alpha 通道。必须区分 `fully_transparent` 区域、`semi_transparent` 区域和 `opaque` 区域，并把透明区域的位置、alpha 范围、用途和约束写入 `transparency_analysis`。不要只写“透明背景”。
   - 对低 alpha 底座/面板上的同色高 alpha 图形，必须查看 alpha 通道轮廓或阈值分割结果。不要只看 RGB 或普通预览；如果白色半透明面板里还有更高 alpha 的白色箭头、下载符号、循环箭头、加号、文字或线形图标，必须把这些高 alpha 图形作为独立前景元素记录。
   - 如果 `A > base_alpha` 或 `A > 240` 的高 alpha 区域 bbox 明显大于肉眼识别出的彩色小图形 bbox，必须生成或 mentally inspect alpha 放大/阈值预览，并继续分割其中的隐藏同色符号。禁止只保留彩色前景而漏掉同色高 alpha 图标层。
   - 记录圆角类型与大小：圆形写 `shape: circle`、`corner_radius_percent: 50`；圆角矩形写实际半径百分比和像素估计值；胶囊形写 `shape: pill`；透明自由形状写 `shape: transparent_freeform` 并描述可见内容边界。
   - 检查四角像素/透明区域。如果四角透明且可见区域为圆形，生成图必须使用圆形遮罩，不能生成圆角矩形底座。
   - 如果参考图是横向或纵向排列的多个子图块，先判断是否为 `sprite_strip` 或 `composite_asset`。不要把整体横向画布误判为单个宽圆角矩形；必须识别每个子图块的独立尺寸、形状、间距、透明背景和叠加徽标。
   - 对 `sprite_strip`，必须先用透明间隔、外部圆角矩形轮廓、alpha 连通区域和可见裁切边界确定 `item_count`，再分析每个 item 内部内容。不要用人物数量、徽标数量、墙上相框、背景照片、室内物件、脸部数量或内部构图细节来增加子图块数量。卡片内部的小照片/相框/背景画面只能记录为该卡片的 `content_detail` 或 `secondary_elements`，不能拆成独立 tile。
   - 对卡片式 `sprite_strip` / `composite_asset`，提炼 JSON 时必须先生成 `card_inventory`：逐项回答 `card_count`、`cards_same_shape`、`cards_same_size`、统一或各自的 `shape_kind`、`bounds_px`、`bounds_percent`、`corner_radius_px`、`gap_px`、`background_alpha`，再逐卡记录 `primary_content`、`foreground_subjects`、`background_subjects`、`status_badge`、`internal_secondary_elements`、`forbidden_as_extra_cards`。不要只写“几张头像卡片”或整体一句话描述。
   - 每张卡片必须有独立元素清单。人物卡片要记录人物数量、相对位置、远近层次、裁切方式、是否为特写/半身/全身；徽标要记录颜色、形状、符号、位置、层级和是否覆盖卡片边缘；背景中的相框、屏幕、窗户、植物、室内物件等必须标记为 `internal_secondary_elements`，并列入 `forbidden_as_extra_cards`。
   - 如果提供了多张参考图，先判断它们是独立参考、同一对象的候选变体，还是同一资源的帧动画序列。默认选择主参考图决定最终尺寸，除非用户另有说明。
   - 当多张参考图尺寸一致、文件名带递增编号、主体轮廓/画布/底色基本一致，只有高光、扫光、阴影、粒子、局部亮度或小装饰的位置变化时，必须标记为 `frame_animation_sequence`，不能当作多张独立图标或互相冲突的设计。
   - 对帧动画序列，必须记录静态底图、不变主体、运动元素、每帧索引、运动方向、起止位置、缓动/速度感、循环方式，以及哪些像素/元素允许逐帧变化。
   - 生成元素地图。对每个可见元素记录相对边界框：`x`、`y`、`w`、`h`，单位为画布宽高百分比，同时记录层级、颜色，以及该元素是否被画布裁切。
   - 对组合符号必须继续拆分到“图形构成”级别。不要把一个内部图标笼统写成 `photo icon`、`star icon` 或 `blue symbol`；要分别记录底座、内框、描边、实心填充、镂空、半透明区域、文字/符号和它们的前后层级。
   - 每个元素必须记录 `fill`、`stroke`、`stroke_width_px`、`opacity/alpha`、`shape_kind`、`corner_radius_px`、`is_hollow` 和 `relationship_to_parent` 中适用的字段。若参考图里某个部件是描边而不是实心填充，生成图也必须保持为描边；若某个部件是半透明底座，不能改成不透明纯白圆。
   - 对半透明叠层图标，必须区分“PNG 背景透明”和“图标内部半透明形状”。记录每个内部半透明图层的颜色、alpha/opacity、相对位置、层级和遮挡关系，不得把不同 alpha 的图层合并成单一实心形状。
   - 生成图标身份地图。对每个可识别的图形符号或对象标注具体类别，例如 `star`、`car`、`money bag`、`magnifying glass`、`shield`、`calendar`、`arrow`、`coin`、`chart`、`person`、`document`、`text label`。
   - 对每个图标身份记录不能改变的形状定义特征。例如：车必须有车身、车顶/座舱、前后方向、车轮、车窗和车灯；放大镜必须有圆形镜片和手柄；星星必须有尖角；钱袋在可见时必须有扎口和货币符号。
   - 当参考图使用非常规/抽象化的符号外形表达常见语义时，必须同时记录 `observed_form` 和 `semantic_identity`。生成新变体时可以使用更常规的图标形态表达同一语义，但必须保留关键语义、状态徽标、层级和透明/填充关系。例如非常规白色扇形 Wi-Fi 可转译为常规 Wi-Fi 弧线/扇形，但不能丢失 Wi-Fi/无网络身份、红色错误圆徽标和白色叉号。
   - 对文字记录精确可见字符串、字符数量、基线角度、字重、填充色、描边色、阴影/高光，以及每个字符是否完整位于画布内。
   - 生成风格指纹。记录参考图是 `flat_gradient_icon`、`soft_gradient_ui_icon`、`soft_2.5d_icon`、`soft_3d`、`拟物图标`、`扁平矢量`、`线性图标`、`像素风`、`照片感` 还是 `手绘插画`；记录渐变方式、边缘硬度、圆角、内外阴影、高光、厚度感、投影、材质和整体饱和度。
   - 必须先判断风格强度，不得把所有 App 图标默认归为 3D。只有参考图同时具有明显厚度/体积建模、真实材质高光、可见接触阴影或三维透视时，才可标记为 `soft_3d` 或 `拟物图标`。
   - 如果参考图只是简洁几何图形、平面图标符号、柔和线性渐变、轻微内阴影或轻微高光，应标记为 `soft_gradient_ui_icon` 或 `flat_gradient_icon`，并在 JSON 中明确禁止生成额外厚重 3D、立体凸起、真实材质、复杂投影或明显景深。
   - 判断参考图是否具有明显的柔和 3D/拟物渲染。如果有，JSON 中必须明确禁止生成成扁平 SVG/vector clipart 风格；如果没有，禁止在提示词中加入 `volumetric forms`、`3D bevels`、`skeuomorphic`、`realistic material` 等会增强立体感的词。
   - 生成变化指令。记录哪些内容必须保持不变，哪些内容必须变化。默认要求保持图标身份、数量级、主布局、层级关系、透明遮罩和风格；同时让造型和颜色出现较明显变化，避免只做轻微描摹、微调颜色或局部挪动。
   - 必须识别主要元素与次要元素。主要元素决定语义身份和可读性，变化要受控；次要元素用于风格、装饰、氛围或状态增强，可有更大的随机性、形状变化、颜色变化、位置微调或替换，但不能遮挡/破坏主要元素。

3. 判断是否适合直接使用图像生成。
   - 只有在参考图本身就是扁平矢量、线性图标、几何徽章、文字标牌，或必须严格保证精确文字/几何时，才优先使用确定性 SVG/canvas/vector 重建后导出位图。
   - 如果使用确定性 SVG/canvas/vector 重建，仍必须遵守 `transparency_analysis` 和 `alpha_layers`。绘制前必须采样参考图主体和边缘 alpha，把半透明填充、半透明描边、抗锯齿边缘和内部半透明层写进绘制参数；禁止为了几何精确而默认使用 `alpha=255` 的实心填充替代参考图半透明填充。
   - 对 alpha 通道中才清晰可见的同色符号，例如白色下载箭头、白色循环箭头、白色线性图标，优先使用 alpha-mask 提取、轮廓追踪或从 alpha 阈值拟合出的几何参数。不要用手写 arc/line/path 粗略猜测，除非已经验证箭头头部、开口方向、中心点、bbox 和 alpha debug 预览都匹配 JSON。
   - 如果确定性重建后的 alpha debug 与参考图 alpha debug 的关键语义图形不一致，例如箭头头部错位、开口方向错误、弧线不环绕中心或符号变成团块，必须判定该输出失败，并改用 alpha-mask 提取/轮廓追踪或重新拟合几何。
   - 如果参考图是柔和 3D、拟物图标、渐变体积、粘土质感、半写实插画、柔焦阴影或照片感，优先使用 `gpt-image-2` 复现风格；不要用确定性矢量绘制替代，否则会变成扁平 SVG 插画。
   - 如果参考图是 `flat_gradient_icon` 或 `soft_gradient_ui_icon`，仍可使用 `gpt-image-2` 生成变体，但提示词必须强调“平面 UI 图标、柔和渐变、轻微高光、无明显 3D 厚度”，不要要求真实体积、厚重倒角、接触阴影或拟物材质。
   - `gpt-image-2` 更适合新鲜视觉渲染、纹理、插画、照片感或绘画风格输出。不要只依赖 `gpt-image-2` 来保证精确排版、微小可读文字或严格图标几何。
   - 如果用户明确要求必须使用 `gpt-image-2`，提示词中必须加入完整性约束，并拒绝任何裁切、遗漏、错层、替换或扭曲关键元素的结果。

4. 提炼结构化 JSON 提示词。
   - 在调用任何生成工具前，必须根据 `JSON 提示词契约` 生成一个 JSON 对象。
   - 对 `reference_only` 和 `reference_plus_text`，必须先显式产出 `final_json`，并在后续生成/确定性绘制/验收中逐项引用这个 JSON。不能只在脑内概括参考图后直接绘制或生成。
   - 如果使用确定性 SVG/canvas/vector 重建，必须先写出同一份 JSON，再从 JSON 的 `bounds_percent`、`layer`、`shape_kind`、`stroke/fill`、`alpha`、`required_traits` 和 `failure_criteria` 推导绘制参数。禁止跳过 JSON 直接凭肉眼画图。
   - 如果参考图包含同色低 alpha 底座和同色高 alpha 符号，JSON 中必须包含 `alpha_threshold_analysis`，记录 `base_alpha`、高 alpha bbox、彩色前景 bbox、隐藏符号身份，以及为什么这些元素必须独立绘制。
   - `text_only` 模式：必须从用户文本中提取主体、动作、场景、构图、视觉风格、色彩、材质、光照、背景、文字、画布比例、尺寸、透明背景、输出格式和禁止项。不要臆造用户没有要求的固定尺寸或透明背景；如果用户没有指定尺寸，使用模型支持的合理比例并在 `output.final_width_px/final_height_px` 中留空或标记为 `null`。
   - `reference_only` 模式：必须把参考图翻译为明确 JSON 属性，不要使用 `same as reference` 这类模糊值。提炼 JSON 后必须继续进入生成步骤，不能只返回 JSON、询问用户是否要生成，或回复“你想做哪种处理/可以选择生成相似图、重生成尺寸、改颜色、提取提示词”等选项。
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
   - JSON 中必须加入透明 PNG 约束：如果参考图是 `transparent_freeform`、有透明角/透明遮罩、透明外边距、透明间距，或 `composite_layout.transparent_between_items` 为 `true`，`output.transparent_png` 必须为 `true`。生成阶段使用纯色绿幕背景辅助分离，后处理本地去绿幕生成真实 alpha PNG；禁止白底、黑底、棋盘格底和把透明预览格子画进图里。
   - JSON 中必须加入半透明约束：如果参考图存在 `semi_transparent` 区域或内部半透明图层，必须记录为 `transparency_analysis.semi_transparent_regions` 或 `alpha_layers.layers`。重新生成时必须保留半透明区域的 alpha 层级，不得把它们变成实色填充、纯白不透明、纯黑不透明或完全透明。
   - 对涉及身份敏感或版权相关的元素，只在用户请求和政策允许时保留；否则应泛化为非识别性的视觉描述。

5. 根据 JSON 提示词生成。
   - 必须优先使用 `image_generation` 工具，并在工具/API 支持模型参数时明确指定 `gpt-image-2` 模型。
   - 在 `reference_only` 模式下，完成参考图 JSON 提炼后必须立即调用生成工具生成默认新变体；只有参考图不可读、生成工具不可用、触发政策限制或用户明确要求“只分析/只输出 JSON/不要生成”时，才可以不生成。不要先向用户展示可选操作按钮、建议列表或二次确认话术。
   - 如果当前环境只暴露封装后的图像生成工具，则在提示词和调用说明中明确写明目标模型为 `gpt-image-2`。
   - 如果工具/API 支持图像输入，把参考图作为视觉上下文传入。
   - 可以把 JSON 转为简洁的生成提示词，但不能丢弃任何 `style_fingerprint`、`required_traits`、`bounds_percent`、`layer`、`relationship`、`invariants` 或 `failure_criteria`。
   - 生成提示词必须先描述风格，再描述元素。风格描述必须来自 JSON 的 `style.rendering` 和 `style.depth_level`，不得套用固定 3D 模板。
   - 对拟物/软 3D 参考图，才可明确要求 `soft 3D app icon rendering, smooth gradients, rounded volumetric forms, soft blurred contact shadow, subtle highlights, no flat vector SVG look`。
   - 对平面或轻渐变 UI 图标，应明确要求 `flat/soft gradient UI app icon, clean geometric shapes, smooth color transitions, subtle inner highlight only, no obvious 3D thickness, no heavy bevel, no realistic material, no cast shadow`。
   - 生成提示词必须明确变化要求。例如：`create a new variation, not a near copy; keep main element identity, required traits, and recognizable silhouette; allow small main-element rotation/scale/position shifts within JSON limits; make noticeable changes mainly through color hue/brightness/saturation, gradient direction, rendering details, and secondary decorative elements; allow wider variation for secondary elements`。
   - 按 JSON 中的 `canvas.aspect_ratio` 请求最接近的支持比例。精确像素尺寸由后处理完成。
   - 生成提示词必须明确画布外形。例如：`circular icon mask with transparent corners, not a rounded square` 或 `wide rounded rectangle banner with 44px corner radius`。
   - 对 `composite_asset` 或 `sprite_strip`，生成提示词必须同时描述整体画布和每个子图块。整体画布可以是横向透明 PNG，但每个子图块必须按参考图真实宽高描述；如果是正方形圆角矩形，明确 `each item is a square rounded rectangle`；如果是非正方形圆角矩形，明确 `each item is a 99x74 rounded rectangle` 这类真实尺寸，不能只写 `wide rounded rectangle` 或套用正方形模板。
   - 生成提示词必须显式写入 `exactly N separate tiles/cards`，其中 `N` 必须来自 JSON 的 `composite_layout.item_count`。如果参考图只有 3 张卡片，提示词中必须写 `exactly three separate non-square rounded-rectangle cards` 和 `do not add a fourth card`。禁止把某张卡片内部的背景相框、室内照片、人物局部或装饰元素生成成额外卡片。
   - 对同尺寸 sprite strip，生成提示词必须显式写入 `all cards have identical width, identical height, identical aspect ratio, and aligned top/bottom edges`，并逐卡重复相同 `bounds_px` 或等价的 `same card size` 约束。禁止只写 `about 99x74`、`left/center/right third` 或 `similar cards` 这类弱约束。
   - 对 `card_inventory.applies: true` 的资源，生成提示词必须按卡片编号逐段写出 `Card 1 / Card 2 / Card 3 ...`，每段包含该卡片的形状尺寸、主内容、前景主体、背景主体、徽标和禁止误拆元素。不得只写“three portrait cards”或“each card follows the reference”；不得把逐卡元素合并成整体描述。
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
   - 禁止通过裁掉生成图自身透明边距、套参考 alpha mask、拉伸、挤压或二次拼接来伪装符合参考尺寸。如果生成图的子图块数量、子图块宽高比、子图块外形或关键内容结构已经错误，必须判定失败并回到 JSON/提示词重新生成，而不是用后处理补救。
   - 对 `composite_asset`、`sprite_strip` 或序列帧资源，也必须先对完整原始绿幕生成图去绿幕，再从大尺寸透明 PNG 中裁切/缩放各子图块或帧。禁止先把绿幕图裁成小图、拼成目标尺寸后再去绿幕。
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
   - 对照 `composite_layout`。如果参考图是组合资源或 sprite strip，必须检查整体尺寸、子图块数量、每个子图块的真实像素尺寸、宽高比例、圆角、间距、透明背景和叠加徽标。整体尺寸正确但子图块比例错误、正方形误生成成长方形、非正方形误生成成正方形、间距不透明、卡片外背景不透明或徽标丢失，都必须判定失败。
   - 对 `composite_layout.same_item_size: true` 的资源，必须在进入尺寸匹配前检查候选生成图里每个外层卡片 bbox 的宽度、高度、宽高比、顶部 y、底部 y 是否在容差内一致。任一卡片变宽、变窄、变高、变矮、顶部/底部不齐、或因内容不同导致外框比例变化，都必须判定失败并重新生成；不得通过裁边、拉伸、挤压或缩放让它看起来符合参考尺寸。
   - 对照 `alpha_layers`。如果参考图内部包含半透明白色/灰色/彩色叠片，必须检查每个叠片的 alpha 层级、前后关系和可见轮廓。把半透明叠片变成实心白、把多层叠片合并成云朵、丢失灰阶层次或改变前后层级，都必须判定失败。
   - 对照 `transparency_analysis`。输出必须保留参考图要求的全透明区域和半透明区域：全透明区域 alpha 必须为 `0`，半透明区域 alpha 必须保持在记录的范围或层级附近。把全透明背景填成颜色、把半透明边缘/叠片变成实色、或把半透明区域误删成全透明，都必须判定失败。
   - 对照 `animation`。如果输入或输出是帧动画序列，所有帧必须尺寸一致、静态底图一致、帧顺序正确、运动元素轨迹连续；不能出现某一帧底图变形、圆角变化、颜色跳变、透明遮罩变化、光带倒退或运动元素消失。
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
  "transparency_analysis": {
    "has_alpha_channel": true,
    "fully_transparent_regions": [
      {
        "id": "transparent_background",
        "bounds_percent": {"x": 0, "y": 0, "w": 100, "h": 100},
        "alpha": 0,
        "role": "outside icon shape or between separated elements",
        "preserve_as_fully_transparent": true
      }
    ],
    "semi_transparent_regions": [
      {
        "id": "anti_aliased_edge_or_internal_layer",
        "bounds_percent": {"x": null, "y": null, "w": null, "h": null},
        "alpha_range": [1, 254],
        "role": "soft edge, shadow, glow, translucent panel, or layered shape",
        "preserve_as_semi_transparent": true,
        "forbidden_conversions": ["opaque fill", "solid white", "solid black", "fully transparent deletion"]
      }
    ],
    "opaque_regions": [],
    "alpha_sampling_notes": "Record representative alpha samples for important edges and internal translucent layers."
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
    "goal": "semantic identity and style remain consistent; layout stays close; shapes and colors change noticeably; not a near copy",
    "preserve": ["semantic identities", "main layout", "layer order", "style family", "canvas shape", "final dimensions"],
    "must_change": ["color palette hue/brightness/saturation", "gradient direction", "secondary decorations", "minor main-element proportion or detail adjustments"],
    "color_shift": "noticeable; keep harmony and style but avoid matching the reference colors too closely",
    "shape_shift": "main elements subtle and controlled; secondary elements can change noticeably",
    "main_elements": {
      "definition": "elements that define semantic identity, required icon meaning, readable text, count, state badges, or critical relationships",
      "variation_range": "conservative; preserve recognizable silhouette and required traits; prefer color hue/brightness/saturation, gradient direction, small proportion changes, minor curvature/detail refinements, rendering details, small rotation, and small size changes over large shape changes",
      "allowed_geometry_shift": {
        "rotation_degrees": "usually -8..8 for symmetric/simple icons; -5..5 for direction-sensitive icons/text; 0 if rotation would change meaning",
        "scale_percent": "usually 90..110; tighter if text readability, exact badge alignment, or icon identity would suffer",
        "position_shift_percent": "usually within 5% of canvas width/height"
      },
      "randomness": "low"
    },
    "secondary_elements": {
      "definition": "decorations, sparkles, highlights, shadows, texture details, small supporting symbols, background accents, non-critical particles, optional ornamentation",
      "variation_range": "wide; may change count within reason, size, position, shape, color, opacity, rhythm, texture, or be substituted with semantically compatible decoration",
      "randomness": "medium_to_high",
      "constraints": "must not cover, replace, crop, or confuse main elements"
    },
    "similarity_limit": "do not look like a direct copy, recolor, resize, or lightly edited version of the reference"
  },
  "composite_layout": {
    "is_composite_asset": false,
    "layout_type": null,
    "item_count": null,
    "item_shape": null,
    "same_item_size": false,
    "same_item_size_tolerance_px": 2,
    "same_item_alignment": {
      "same_top_y": false,
      "same_bottom_y": false,
      "same_corner_radius": false
    },
    "item_width_px": null,
    "item_height_px": null,
    "gap_px": null,
    "transparent_between_items": false,
    "items": []
  },
  "card_inventory": {
    "applies": false,
    "card_count": null,
    "cards_same_shape": null,
    "cards_same_size": null,
    "shared_card_shape": null,
    "shared_card_width_px": null,
    "shared_card_height_px": null,
    "shared_card_aspect_ratio": null,
    "shared_corner_radius_px": null,
    "shared_gap_px": null,
    "cards": [
      {
        "index": 1,
        "bounds_px": {"x": null, "y": null, "w": null, "h": null},
        "bounds_percent": {"x": null, "y": null, "w": null, "h": null},
        "shape_kind": "rounded_rectangle",
        "corner_radius_px": null,
        "primary_content": "what this card mainly depicts",
        "foreground_subjects": [],
        "background_subjects": [],
        "status_badge": {
          "exists": false,
          "shape": null,
          "fill_color": null,
          "symbol": null,
          "position": null,
          "layer": null
        },
        "internal_secondary_elements": [],
        "forbidden_as_extra_cards": []
      }
    ],
    "failure_criteria": []
  },
  "alpha_layers": {
    "has_internal_translucent_layers": false,
    "layers": []
  },
  "animation": {
    "is_frame_animation": false,
    "sequence_type": null,
    "frame_count": null,
    "frame_order_source": null,
    "static_base": null,
    "animated_elements": [],
    "per_frame_changes": [],
    "invariants_across_frames": [],
    "looping": null
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
- 如果参考图有透明角、透明外边距、透明间距或透明自由形状，默认 `output.transparent_png` 为 `true`。
- 默认自动生成新变体，不做近似复制。不要把“是否生成”作为澄清问题问用户；用户只给参考图就是生成请求。
- 最终回复应包含生成结果路径或生成失败原因，不能只给参考图分析、JSON 草稿或下一步建议。
- 禁止响应模板：不要说“我看到了参考图，你想对它做哪种处理？”、“可以选择：生成相似图/重生成尺寸/改颜色/提取 JSON 提示词”、“请告诉我你想怎么处理”。正确行为是直接开始生成，例如“我会按参考图生成一个相似但不雷同的新变体，并保持尺寸/透明遮罩”。

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

## 组合资源与 Sprite Strip

当参考图是一个透明画布上排列多个 UI 子图块时，必须识别为 `composite_asset` 或 `sprite_strip`，不要把整体画布当作单一横向图标。

识别条件：
- 整体画布宽高比很宽或很高，但内部由多个重复尺寸的子图块组成。
- 子图块之间有透明间距，或整体四周/间隙存在 alpha 透明像素。
- 每个子图块有自己的圆角、裁切、内容和叠加元素，例如头像、状态徽标、角标、按钮状态、表情状态。
- 子图块尺寸必须按参考图真实像素记录。接近正方形时，记录为 `item_shape: rounded_square`；明显非正方形时，记录为 `item_shape: rounded_rectangle`，并写出真实 `item_width_px`、`item_height_px` 和 `item_aspect_ratio`。不能因为整体画布是横向就把子图块生成成长方形，也不能因为上一张示例是正方形就把所有子图块生成成正方形。
- 如果参考图的子图块同尺寸，必须写 `same_item_size: true`，并记录统一的 `item_width_px`、`item_height_px`、`item_aspect_ratio`、`item_corner_radius_px`、`same_top_y` 和 `same_bottom_y`。每个 `items[i].bounds_px` 的 `w/h` 必须相同或在像素容差内，不能因为内部人物数量、构图或主体大小不同而改变卡片外框尺寸。
- 子图块数量必须由透明间隔和每个外部圆角卡片轮廓决定。先数外层卡片，再分析每张卡片内部内容。内部墙面相框、小照片、手机屏幕、背景人物、局部脸部、徽标图形或室内物件不是新的子图块，只能作为所属卡片的 `content_detail` 或 `secondary_elements`。

JSON 必须记录：
- `composite_layout.is_composite_asset: true`。
- `layout_type`，例如 `horizontal_sprite_strip`、`vertical_sprite_strip`、`grid_sprite_sheet`、`multi_state_asset`。
- `item_count`、`same_item_size`、`same_item_size_tolerance_px`、`item_width_px`、`item_height_px`、`gap_px`、`item_shape`、`item_corner_radius_px`。
- `transparent_between_items: true`，当子图块之间或外边距为透明时必须开启 `output.transparent_png: true`。
- `items` 中逐个记录每个子图块的 `bounds_px` 和 `bounds_percent`、图片内容、状态徽标、层级、裁切方式、是否完整可见。
- `card_inventory.applies: true`，并逐卡记录卡片形状、尺寸、位置、主内容、前景主体、背景主体、状态徽标、内部次要元素和禁止误拆成额外卡片的元素。生成提示词必须逐卡引用 `card_inventory.cards[i]`，不能只引用整体 `composite_layout`。
- 如果 `card_inventory.cards_same_shape` 或 `card_inventory.cards_same_size` 为 `true`，提示词和失败标准必须明确“所有卡片形状/尺寸一致”；如果为 `false`，必须逐卡写出每张卡片不同的形状、尺寸和原因。

对于 `313x74` 的三头像示例资源，必须识别为：
- 整体画布：`313x74`，透明背景，不是单个不透明横幅。
- 子图块：3 个 `99x74` 非正方形圆角矩形头像卡片，横向排列，约 `8px` 透明间距。
- `same_item_size: true`，三张卡片必须同宽、同高、同宽高比、同圆角，顶部和底部对齐；不得因为第 2 张是多人合照或第 3 张有远近两个人物而改变卡片宽度或高度。
- 每个头像卡片保持 `99x74` 横向圆角矩形，不得生成成 `72x72`、`99x99` 或任何正方形卡片。
- 第 1 个卡片是双人头像并带左下角蓝色圆形勾选徽标；第 2 个卡片是多人合照并带左下角红色圆形叉号徽标；第 3 个卡片是两个人物构成的照片卡片并带左下角红色圆形叉号徽标。
- 第 3 个卡片必须记录为“两个人物层次”：近处人物是右侧/前景的大头特写或半脸特写，远处人物是左侧/背景中较小的全身照或接近全身的人物。远处人物不是墙上相框、不是额外子图块、不是独立第 4 张卡片。
- 卡片外和卡片之间必须透明，徽标可覆盖卡片边缘但必须保持位置、颜色、语义和完整可见。
- 失败标准：生成 4 个卡片、三张卡片不是相同外框尺寸、某张卡片因内容变宽/变窄/变高/变矮、顶部或底部不对齐、把远处人物误识别为墙上相框/背景照片、把内部内容拆成独立卡片、把三张非正方形卡片改成正方形或四张卡片、或输出提示词没有写明 `exactly three separate non-square rounded-rectangle cards, all cards have identical width and height, do not add a fourth card, preserve card 3 as two people with a foreground close-up and a distant full-body person`，都必须判定失败。

对于 `312x72` 的四头像示例资源，必须识别为：
- 整体画布：`312x72`，透明背景，不是单个不透明横幅。
- 子图块：4 个 `72x72` 正方形圆角矩形头像卡片，横向排列，约 `8px` 透明间距。
- 每个头像卡片保持正方形，不得生成成长方形、竖向矩形或不同尺寸卡片。
- 每个卡片内部人物照片按圆角方形裁切；卡片外和卡片之间必须透明。
- 第 1、2 个卡片左下角有蓝色圆形勾选徽标；第 3、4 个卡片左下角有红色圆形叉号徽标。徽标可覆盖卡片边缘但必须保持位置、颜色、语义和完整可见。

生成提示词必须明确写入：`transparent canvas containing four separate square rounded-rectangle tiles, not one wide rounded rectangle; keep transparent gaps between tiles; preserve alpha outside and between tiles`。如果输出把四个正方形卡片变成长方形、丢失透明间距、背景变白/黑/不透明、徽标位置或语义错误，必须判定失败并重新生成或做确定性后处理。

## 半透明图层结构与叠片

当参考图内部有多个半透明图形层时，必须把它们当作独立视觉元素记录到 `alpha_layers`，不要只按最终合成后的明暗/颜色轮廓理解。这些图层可能是同色不同透明度，也可能是不同颜色不同透明度，或不同颜色叠加后形成的混合色。

识别要求：
- 分开记录 PNG 背景透明区域和图标内部半透明区域。背景 alpha 为 `0` 不等于内部半透明图层。
- 对每个半透明图层记录 `id`、`bounds_percent`、`layer`、`shape_kind`、`color_rgb`、`opacity` 或采样 alpha、混合方式、圆角、渐变、与前景元素的遮挡关系。
- 如果同一颜色有多个 alpha 层级，例如白色 `A≈90`、`A≈166`、`A=255`，必须分别记录为不同层。
- 如果不同颜色有不同 alpha 层级，例如半透明白色底座、半透明蓝色高光、半透明紫色阴影、半透明灰色侧翼，也必须分别记录为不同层，不能合并成单个“半透明区域”。
- 如果两个半透明层相互重叠形成新的视觉颜色，必须记录 `overlap_regions` 或在各层 `relationship` 中说明叠加关系；不要把重叠后的颜色误判为单独实心图形。
- 半透明区域通常承载形状边缘、遮罩轮廓、柔化过渡或内部层级信息。生成时不得为了“看起来更干净”把这些区域改成全色实心填充；如果半透明边缘/扇形/弧线被填成实心块而导致图标特征丢失，必须判定失败。
- 生成提示词中明确“preserve separate translucent layers with their own colors and opacity levels”，不要写成“white cloud shape”“solid background blob”“single translucent overlay”。
- 验收时在深色、浅色和中性背景上预览，也要确认不同颜色和不同透明度的半透明层次仍然可见；不能只检查有无 alpha 通道。

## 底座容器与内部图形构成

当参考图是底座容器内含小图标的 UI 资源时，必须把底座和内部符号拆成独立图层，而不是合并成一个简单 glyph。底座容器不一定是圆形，也可能是圆角矩形、胶囊、方形、自由形遮罩、半透明面板或渐变色块。

识别要求：
- `base_container`：记录底座的尺寸、中心点、`shape_kind`、圆角/半径、填充色、alpha/opacity、渐变、描边、边缘抗锯齿和透明外部区域。`shape_kind` 必须从实际参考图判断，可为 `circle`、`rounded_square`、`rounded_rectangle`、`pill`、`full_rectangle`、`freeform_blob`、`masked_panel` 或其他明确形态。
- 不要把所有底座默认写成圆形。半透明白色圆形底座必须写成 `semi-transparent white circular base`；半透明圆角矩形底座必须写成 `semi-transparent white rounded-rectangle base`；胶囊底座必须写成 `semi-transparent pill base`。不得把它们统一泛化成 `white background` 或 `opaque white circle`。
- `inner_icon_container`：如果内部图标存在图片框、卡片框、圆角矩形框、描边框或镂空框，必须单独记录。尤其要区分 `white stroke rounded rectangle` 和 `solid filled rectangle`。
- `inner_symbol`：把中心语义图形拆成决定性部件。例如图片图标必须包含“圆角矩形图片框/相框”和“山形/图片内容符号”；星光必须保持尖角星形，不能变成圆点、加号或模糊光斑。
- 对每个内部部件记录 `fill`、`stroke`、`stroke_width_px`、`opacity`、`bounds_percent`、`layer` 和 `relationship_to_container`。如果部件没有描边，写 `stroke: none`；如果只有描边没有填充，写 `fill: none`。
- 生成提示词中必须明确底座形态以及哪些部件是实心填充、描边、镂空、半透明或渐变，不能只写“small blue photo icon in a white circle”。
- 验收时如果底座形态错误（圆形变圆角矩形、圆角矩形变圆形、胶囊变普通矩形等）、内部白色描边框丢失、被改成实心白块、被替换成只有蓝色三角形、底座透明度被改成不透明纯色、星光身份错误或层级反转，必须判定失败。

对于 `144x144` 的 `change_photo` 图标示例，必须识别为：
- 整体画布：`144x144`，透明四角，主体是居中的圆形底座。
- 底座：圆形白色半透明底座，边缘有 alpha 抗锯齿；它不是纯不透明白色实心圆，也不是方形或圆角矩形按钮。
- 内部图片框：底座内部居中偏下有一个代表图片的白色描边圆角矩形/相框，描边为白色，内部不应被白色实心填满。该相框是图片语义的一部分，即使很淡或局部被蓝色山形覆盖，也必须在 JSON 中记录。
- 山形符号：相框内部有浅蓝色实心山形/图片内容符号，通常为三角山峰或简化图片山形，`fill` 为浅蓝，`stroke: none`。
- 星光符号：山形左上附近有浅蓝色小尖角星光，位于相框/山形上方图层，必须保持星形尖角身份。
- 层级顺序：全透明背景 < 半透明圆形底座 < 白色描边图片框 < 浅蓝山形实心符号 < 浅蓝小星光。
- 生成提示词必须直接写入：`semi-transparent white circular base with transparent outside corners; inside it, a small white stroke rounded-rectangle photo frame, not a filled rectangle; inside the frame is a solid light-blue mountain/image symbol; a small light-blue pointed sparkle above-left; preserve fill versus stroke and opacity layers`。
- 禁止把内部结构简化成只有蓝色三角形和星星；禁止丢失白色描边图片框；禁止把底座变成不透明实心白圆；禁止把图片框描边变成蓝色或实心填充；禁止把星光变成圆点、十字或模糊光。

`change_photo` 图标的 JSON 应提炼到这个粒度：

```json
{
  "elements": [
    {
      "id": "base_container",
      "identity": "semi-transparent circular button base",
      "bounds_percent": {"x": 0, "y": 0, "w": 100, "h": 100},
      "layer": 1,
      "shape_kind": "circle",
      "corner_radius_percent": 50,
      "fill": {"color": "#ffffff", "opacity": 0.86},
      "stroke": "none",
      "edge": "anti-aliased alpha edge",
      "relationship_to_canvas": "centered, transparent outside circle"
    },
    {
      "id": "photo_frame",
      "identity": "rounded-rectangle photo frame",
      "bounds_percent": {"x": 39, "y": 43, "w": 25, "h": 22},
      "layer": 2,
      "shape_kind": "rounded_rectangle",
      "corner_radius_px": 2,
      "fill": "none",
      "stroke": {"color": "#ffffff", "opacity": 1.0, "stroke_width_px": 3},
      "is_hollow": true,
      "relationship_to_parent": "inside base_container behind mountain_symbol"
    },
    {
      "id": "mountain_symbol",
      "identity": "solid mountain/image content symbol",
      "bounds_percent": {"x": 42, "y": 48, "w": 22, "h": 21},
      "layer": 3,
      "shape_kind": "filled_triangle_mountain",
      "fill": {"color": "#6bbfff", "opacity": 1.0},
      "stroke": "none",
      "relationship_to_parent": "inside photo_frame"
    },
    {
      "id": "sparkle",
      "identity": "small pointed sparkle star",
      "bounds_percent": {"x": 39, "y": 36, "w": 10, "h": 10},
      "layer": 4,
      "shape_kind": "four_point_sparkle",
      "fill": {"color": "#6bbfff", "opacity": 1.0},
      "stroke": "none",
      "relationship_to_parent": "above-left of mountain_symbol"
    }
  ],
  "failure_criteria": [
    "Base container shape changes from the reference shape",
    "Base container becomes an opaque solid shape instead of preserving the reference opacity",
    "The white stroke rounded-rectangle photo frame is missing",
    "The photo frame is generated as a filled white rectangle instead of a hollow stroked frame",
    "The icon is simplified to only a blue triangle and sparkle",
    "The mountain/image symbol is no longer inside the photo frame",
    "The sparkle loses pointed star identity or changes into a dot, plus sign, or blurred glow",
    "Fill/stroke/opacity roles are swapped between elements"
  ]
}
```

## 非常规图标形态与语义转译

当参考图用非常规几何形态表达常见图标语义时，必须区分“观察到的外形”和“要保持的语义身份”：
- `observed_form`：参考图真实外观，例如非标准白色眼形/扇形 Wi-Fi、抽象三角图片符号、简化盾牌等。
- `semantic_identity`：用户和应用中真正需要表达的意义，例如 `no_network_wifi`、`change_photo`、`security_scan`。
- `allowed_semantic_translation`：生成新变体时允许使用更常规、更清晰的图标形态表达同一语义，例如把非常规 Wi-Fi 扇形转译为常规三段 Wi-Fi 弧线加中心点。
- `must_preserve_status_badge`：如果参考图有红色错误徽标、蓝色勾选徽标、角标、数字、状态点等，必须保持徽标语义、颜色、相对位置、前后层级和完整可见。

允许变化：
- 非常规 Wi-Fi 外形可以变成常规 Wi-Fi 图标，例如 2-3 段白色弧线和底部圆点，或标准 Wi-Fi 扇形。
- 非常规图片/相册/设置/网络等符号可以转译成该语义下更清晰的常规图标结构。

禁止变化：
- 不得把半透明或抗锯齿区域填成纯色大块，导致 Wi-Fi 弧线、扇形开口、图片框、镂空或其他决定性特征消失。
- 不得只保留状态徽标而丢失主图标语义。
- 不得把状态徽标从前景改成背景、从圆形改成任意贴片，或丢失叉号/勾号等内部符号。

对于 `80x80` 的 `no_network` 图标示例，必须识别为：
- 整体画布：`80x80`，透明背景，主体位于上半部到中部。
- 语义身份：`no_network_wifi` / `wifi_unavailable`，不是眼睛、雨伞、普通警告、隐藏可见性或关闭按钮。
- 观察外形：参考图主图标是非常规白色 Wi-Fi/信号扇形，形状接近上弧宽、下方收束的眼形/扇形，边缘包含透明/半透明抗锯齿。它不是简单实心三角形，也不是必须逐像素复制的唯一合法 Wi-Fi 外形。
- 状态徽标：中心偏上有红色圆形错误徽标，位于白色 Wi-Fi 主体前方；徽标内有白色 `x` 叉号，叉号必须完整可见。
- 允许转译：生成新图时可以使用常规 Wi-Fi 图标形态表达 `no_network_wifi`，例如白色 2-3 段 Wi-Fi 弧线加底部点，再叠加红色圆形叉号徽标。
- 透明/填充约束：白色 Wi-Fi 主体的边缘透明/半透明像素必须保留抗锯齿和轮廓信息；不得把半透明扇形区域填成不透明白色块，导致 Wi-Fi 特征性丢失。
- 层级顺序：透明背景 < 白色 Wi-Fi 主体/弧线 < 红色错误圆徽标 < 白色叉号。
- 生成提示词必须直接写入：`no-network Wi-Fi icon on transparent background; preserve semantic identity as Wi-Fi unavailable; white Wi-Fi signal may use a conventional Wi-Fi arcs shape instead of the reference's unusual fan shape; keep a red circular error badge in front with a white x; preserve antialiased translucent edges, do not fill translucent Wi-Fi regions into solid blobs`。
- 禁止把图标生成成眼睛、警告三角、普通关闭按钮、云朵、电话信号、蓝牙或无意义白色实心块；禁止丢失红色圆徽标或白色叉号；禁止把红色徽标放到 Wi-Fi 图标后面。

`no_network` 图标的 JSON 应提炼到这个粒度：

```json
{
  "icon_identity": {
    "semantic_identity": "no_network_wifi",
    "observed_form": "unusual white Wi-Fi fan/eye-like signal shape with antialiased translucent edge",
    "allowed_semantic_translation": ["conventional white Wi-Fi arcs with bottom dot", "standard white Wi-Fi fan"],
    "forbidden_identities": ["eye", "umbrella", "warning triangle", "close button only", "bluetooth", "cellular signal"]
  },
  "elements": [
    {
      "id": "wifi_signal",
      "identity": "Wi-Fi signal",
      "bounds_percent": {"x": 0, "y": 20, "w": 100, "h": 58},
      "layer": 1,
      "shape_kind": "unusual_fan_or_conventional_wifi_arcs",
      "fill": {"color": "#ffffff", "opacity": 1.0},
      "edge": "anti-aliased translucent edge",
      "allowed_shape_variation": "may become conventional Wi-Fi arcs if semantic identity remains clear"
    },
    {
      "id": "error_badge",
      "identity": "red circular error badge",
      "bounds_percent": {"x": 32, "y": 26, "w": 36, "h": 36},
      "layer": 2,
      "shape_kind": "circle",
      "fill": {"color": "#ff5252", "opacity": 1.0},
      "relationship_to_parent": "front center overlay on Wi-Fi signal"
    },
    {
      "id": "x_mark",
      "identity": "white x mark",
      "bounds_percent": {"x": 42, "y": 36, "w": 16, "h": 16},
      "layer": 3,
      "shape_kind": "two crossing rounded strokes",
      "fill": "none",
      "stroke": {"color": "#ffffff", "opacity": 1.0, "stroke_width_px": 2}
    }
  ],
  "failure_criteria": [
    "Wi-Fi semantic identity is lost",
    "The white Wi-Fi signal is filled into an unrecognizable solid blob",
    "The icon becomes an eye, umbrella, warning triangle, close button only, Bluetooth, or cellular signal",
    "The red circular error badge is missing, moved behind the Wi-Fi signal, or no longer circular",
    "The white x mark is missing or unreadable",
    "Antialiased translucent edges are replaced by jagged or fully opaque block edges"
  ]
}
```

对于 `240x240` 的 `dialog_notsave` 图标示例，必须识别为：
- 整体画布：`240x240`，透明背景。
- 底座容器：左下主体是大圆角矩形卡片/面板，白色低 alpha 半透明填充，约 `A≈25`；不是不透明纯白卡片。
- 内部下载符号：卡片内部有白色高 alpha 下载箭头，包含竖向圆角线段、左右斜向箭头臂和向下箭头尖；它位于卡片前景层，必须独立记录为 `download_arrow`。不要因为颜色同为白色或普通预览里不明显而漏掉。
- 状态徽标：右上角红色圆形告警徽标覆盖在卡片和下载箭头前方；内部有白色感叹号，感叹号由竖向圆角条和圆点组成。
- 层级顺序：透明背景 < 半透明白色卡片 < 高 alpha 白色下载箭头 < 红色告警圆徽标 < 白色感叹号。
- 检测要求：必须通过 alpha 分层识别低 alpha 卡片和高 alpha 下载箭头。仅采样卡片主体 alpha 或只看 RGB 预览是不够的。
- 生成提示词必须直接写入：`transparent 240x240 icon; large low-alpha semi-transparent white rounded-rectangle card; centered high-alpha white download arrow on the card; red circular warning badge at the top-right in front; white exclamation mark inside the badge; preserve alpha layer separation, do not omit the download arrow`。
- 禁止把半透明卡片改成不透明白色；禁止漏掉下载箭头；禁止把下载箭头和卡片合并成一个白色块；禁止把右上徽标放到卡片后方；禁止把感叹号改成叉号或点。

`dialog_notsave` 图标的 JSON 应提炼到这个粒度：

```json
{
  "elements": [
    {
      "id": "card_panel",
      "identity": "semi-transparent rounded-rectangle card",
      "bounds_percent": {"x": 10, "y": 12, "w": 79, "h": 78},
      "layer": 1,
      "shape_kind": "rounded_rectangle",
      "corner_radius_px": 31,
      "fill": {"color": "#ffffff", "alpha_estimate": 25, "opacity": 0.10},
      "stroke": "none"
    },
    {
      "id": "download_arrow",
      "identity": "download arrow",
      "bounds_percent": {"x": 35, "y": 31, "w": 30, "h": 36},
      "layer": 2,
      "shape_kind": "rounded_stroke_down_arrow",
      "stroke": {"color": "#ffffff", "alpha_estimate": 255, "stroke_width_px": 12, "linecap": "round"},
      "required_traits": ["vertical stem", "downward arrow head", "two diagonal arms", "rounded stroke caps"],
      "detection_note": "visible through alpha thresholding against the low-alpha card"
    },
    {
      "id": "warning_badge",
      "identity": "red circular warning badge",
      "bounds_percent": {"x": 68, "y": 8, "w": 26, "h": 26},
      "layer": 3,
      "shape_kind": "circle",
      "fill": {"color": "#ff4f52", "opacity": 1.0},
      "relationship_to_parent": "overlaps top-right of card_panel"
    },
    {
      "id": "exclamation_mark",
      "identity": "white exclamation mark",
      "bounds_percent": {"x": 78, "y": 14, "w": 5, "h": 15},
      "layer": 4,
      "shape_kind": "rounded vertical bar plus dot",
      "fill": {"color": "#ffffff", "opacity": 1.0}
    }
  ],
  "failure_criteria": [
    "The download arrow is missing",
    "The card panel is opaque white instead of low-alpha semi-transparent white",
    "The download arrow is merged into the card and no longer readable",
    "The warning badge is missing or behind the card",
    "The white exclamation mark is missing or changed to an x"
  ]
}
```

对于 `144x144` 的 `regenerate` 图标示例，必须识别为：
- 整体画布：`144x144`，透明背景。
- 底座容器：居中的圆形低 alpha 白色底座，主 alpha 约 `A≈51`，不是不透明白圆。
- 隐藏/同色前景符号：底座内部存在高 alpha 白色循环箭头/重生成箭头，普通预览中容易被半透明白色底座掩盖；必须通过 alpha 阈值识别。其 bbox 约覆盖中心大半区域，不能只识别中心蓝色星光。
- 中心星光：浅蓝色实心四角星/魔法星光，位于循环箭头前方或中心区域，表示重新生成/魔法效果。
- 层级顺序：透明背景 < 半透明白色圆形底座 < 高 alpha 白色循环箭头 < 浅蓝色星光。
- 结构定位：循环箭头应围绕画布中心形成近圆形运动轨迹，圆心约在 `(50%, 50%)`，外接 bbox 约 `x=25..76%, y=24..76%`；弧线开口在左下到下方区域，箭头头部位于左上/左侧附近，表示重新开始/重新生成的环形运动。星光必须位于环形箭头中心附近，不应把环形箭头挤偏到上方、右侧或底部。
- 重建方式：优先从参考图 alpha 阈值提取 `regenerate_arrow` 的真实 mask 或轮廓，再生成变体；如果改用矢量拟合，必须用 alpha debug 对比确认箭头头部和弧线开口位置与参考 JSON 一致。
- 生成提示词必须直接写入：`transparent 144x144 icon; low-alpha semi-transparent white circular base; high-alpha white circular regenerate arrow inside the base; solid light-blue sparkle at center; preserve alpha layer separation, do not omit the white regenerate arrow`。
- 禁止只生成蓝色星光和圆形底座；禁止漏掉白色循环箭头；禁止把圆形底座改成不透明白色；禁止把循环箭头合并到底座里导致不可读。

`regenerate` 图标的 JSON 应提炼到这个粒度：

```json
{
  "alpha_threshold_analysis": {
    "base_alpha_estimate": 51,
    "high_alpha_threshold": 240,
    "high_alpha_bbox_percent": {"x": 25, "y": 24, "w": 51, "h": 52},
    "blue_sparkle_bbox_percent": {"x": 42, "y": 42, "w": 17, "h": 17},
    "conclusion": "high-alpha bbox is much larger than the blue sparkle, so a hidden white regenerate arrow must be extracted as an independent element"
  },
  "elements": [
    {
      "id": "base_circle",
      "identity": "low-alpha circular base",
      "bounds_percent": {"x": 0, "y": 0, "w": 100, "h": 100},
      "layer": 1,
      "shape_kind": "circle",
      "fill": {"color": "#ffffff", "alpha_estimate": 51, "opacity": 0.20},
      "stroke": "none"
    },
    {
      "id": "regenerate_arrow",
      "identity": "circular regenerate arrow",
      "bounds_percent": {"x": 25, "y": 24, "w": 51, "h": 52},
      "layer": 2,
      "shape_kind": "alpha_mask_extracted_circular_arrow_or_traced_contour",
      "stroke": {"color": "#ffffff", "alpha_estimate": 255, "stroke_width_px": 10, "linecap": "round"},
      "geometry": {
        "center_percent": {"x": 50, "y": 50},
        "outer_radius_percent": 25,
        "arc_sweep_degrees": 260,
        "open_gap_position": "lower-left to bottom",
        "arrow_head_position": "left or upper-left end of the circular arc",
        "must_wrap_around_center_sparkle": true
      },
      "required_traits": ["curved circular arrow", "visible arrow head", "open circular motion path", "centered around the blue sparkle"],
      "detection_note": "must be detected from high-alpha threshold; may be hard to see in plain preview",
      "reconstruction_preference": "extract alpha mask or trace contour before approximating with vector arcs"
    },
    {
      "id": "center_sparkle",
      "identity": "light-blue magic sparkle",
      "bounds_percent": {"x": 42, "y": 42, "w": 17, "h": 17},
      "layer": 3,
      "shape_kind": "four_point_sparkle",
      "fill": {"color": "#6dc2ff", "opacity": 1.0},
      "stroke": "none"
    }
  ],
  "failure_criteria": [
    "The white regenerate arrow is missing",
    "The output contains only the blue sparkle and circular base",
    "The base circle becomes opaque white instead of low-alpha semi-transparent white",
    "The regenerate arrow is merged into the base and no longer readable",
    "The regenerate arrow is off-center or no longer wraps around the sparkle",
    "The arrow head is missing or placed so the icon no longer reads as restart/regenerate",
    "The alpha debug preview does not match the reference arrow head/open-gap relationship",
    "The blue sparkle loses pointed star identity"
  ]
}
```

对于 `240x240` 的 `5` 图标示例，必须识别为：
- 整体画布：`240x240`，透明背景，主体居中，四周必须保留透明边距。
- 语义身份：`five_overlapping_cards`，代表 5 张重叠卡片，不是手机、云朵、文件夹、胶囊、白色耳朵或普通白色底座。数字 `5` 是数量语义的一部分，不能只当装饰文字。
- 中心前景卡片：位于画布中心，是一块竖向圆角矩形卡片；外层是实心白色粗描边/边框，内部是镂空区域，预览在深色背景时呈黑色圆角矩形内区。必须记录为 `front_card_frame` 和 `front_card_inner_cutout`，并明确“white outlined hollow rounded rectangle”。不要描述成手机、屏幕、设备或实心黑色面板。
- 左右侧翼卡片：左侧 2 张、右侧 2 张半露出的圆角矩形卡片，均位于中心前景卡片后方。它们是卡片，不是连续背景；每一张都要有独立圆角、独立半透明白色填充、独立 bounds 和独立遮挡关系。每侧内层卡片 alpha 较高、外层卡片 alpha 较低，形成“5 张卡片叠放”的层级；侧翼只露出外侧半边，不能变成连续云朵轮廓。
- 文本：蓝色数字 `5` 位于中心卡片内部中央偏上，表示卡片数量，必须保持可读且在中心卡片内。
- 层级顺序必须是：最外侧低 alpha 侧翼卡片 < 内侧较高 alpha 侧翼卡片 < 中心白色描边卡片 < 中心镂空内部/数字。左右必须大体对称，且所有后层卡片必须被中心卡片遮挡一部分。
- 生成提示词必须直接写入：`five overlapping rounded cards icon; center card is a white outlined hollow rounded rectangle with a dark inner cutout; two semi-transparent white rounded cards peek from the left and two semi-transparent white rounded cards peek from the right; preserve separate opacity levels and alpha transparency; transparent background`。
- 禁止把左右两侧半透明卡片合并成实心白色云朵、纯白外轮廓、单一不透明底座或耳朵形状；禁止让侧翼覆盖中心白色描边或黑色内部；禁止把半透明侧翼改成不透明白色；禁止丢失中心内部镂空；禁止丢失“左右各两张半透明卡片”的数量和透明度层级。

`5` 图标的 JSON 应提炼到这个粒度：

```json
{
  "elements": [
    {
      "id": "left_outer_card",
      "identity": "rear overlapping card",
      "bounds_percent": {"x": 0, "y": 28, "w": 23, "h": 45},
      "layer": 1,
      "shape": "rounded_rectangle, half-visible from left",
      "appearance": {"color": "#ffffff", "alpha_estimate": 0.35},
      "occlusion": "behind left_inner_card and front_card_frame",
      "completeness": "intentionally half hidden; only the left outer half is visible"
    },
    {
      "id": "left_inner_card",
      "identity": "rear overlapping card",
      "bounds_percent": {"x": 10, "y": 21, "w": 26, "h": 59},
      "layer": 2,
      "shape": "rounded_rectangle, partially visible",
      "appearance": {"color": "#ffffff", "alpha_estimate": 0.65},
      "occlusion": "behind front_card_frame; only the left side remains visible"
    },
    {
      "id": "right_inner_card",
      "identity": "rear overlapping card",
      "bounds_percent": {"x": 64, "y": 21, "w": 26, "h": 59},
      "layer": 2,
      "shape": "rounded_rectangle, partially visible",
      "appearance": {"color": "#ffffff", "alpha_estimate": 0.65},
      "occlusion": "behind front_card_frame; only the right side remains visible"
    },
    {
      "id": "right_outer_card",
      "identity": "rear overlapping card",
      "bounds_percent": {"x": 77, "y": 28, "w": 23, "h": 45},
      "layer": 1,
      "shape": "rounded_rectangle, half-visible from right",
      "appearance": {"color": "#ffffff", "alpha_estimate": 0.35},
      "occlusion": "behind right_inner_card and front_card_frame",
      "completeness": "intentionally half hidden; only the right outer half is visible"
    },
    {
      "id": "front_card_frame",
      "identity": "front overlapping card frame",
      "bounds_percent": {"x": 27, "y": 10, "w": 46, "h": 81},
      "layer": 3,
      "shape": "vertical rounded rectangle with thick white outline and hollow center",
      "appearance": {"frame_color": "#ffffff", "alpha": 1.0},
      "role": "front card, not phone"
    },
    {
      "id": "front_card_inner_cutout",
      "identity": "inner hollow cutout",
      "bounds_percent": {"x": 34, "y": 17, "w": 32, "h": 67},
      "layer": 4,
      "shape": "rounded rectangular opening inside the white frame",
      "appearance": {"type": "cutout_or_dark_preview_area", "preview_color_on_dark_background": "#000000"},
      "must_remain_hollow": true
    },
    {
      "id": "number_5",
      "identity": "count text",
      "bounds_percent": {"x": 41, "y": 39, "w": 20, "h": 24},
      "layer": 5,
      "text": "5",
      "appearance": {"color": "#5dbaff", "alpha": 1.0}
    }
  ],
  "alpha_layers": {
    "has_internal_translucent_layers": true,
    "layers": [
      {
        "id": "left_outer_card",
        "color": "#ffffff",
        "alpha_estimate": 0.35,
        "bounds_percent": {"x": 0, "y": 28, "w": 23, "h": 45},
        "layer": 1,
        "preserve_as": "semi-transparent rear card"
      },
      {
        "id": "left_inner_card",
        "color": "#ffffff",
        "alpha_estimate": 0.65,
        "bounds_percent": {"x": 10, "y": 21, "w": 26, "h": 59},
        "layer": 2,
        "preserve_as": "semi-transparent rear card"
      },
      {
        "id": "right_inner_card",
        "color": "#ffffff",
        "alpha_estimate": 0.65,
        "bounds_percent": {"x": 64, "y": 21, "w": 26, "h": 59},
        "layer": 2,
        "preserve_as": "semi-transparent rear card"
      },
      {
        "id": "right_outer_card",
        "color": "#ffffff",
        "alpha_estimate": 0.35,
        "bounds_percent": {"x": 77, "y": 28, "w": 23, "h": 45},
        "layer": 1,
        "preserve_as": "semi-transparent rear card"
      }
    ]
  },
  "failure_criteria": [
    "Center object is described or generated as a phone instead of the front card in a 5-card stack",
    "Left or right side has fewer than two visible rear card layers",
    "Rear card layers merge into a cloud-like blob or solid white shape",
    "Rear cards become opaque or lose separate alpha levels",
    "The white front frame is filled solid instead of having a black inner cutout",
    "The blue number 5 is missing, unreadable, or outside the front card"
  ]
}
```

## 帧动画资源识别

当用户提供多张同类图片资源时，先判断是否为帧动画序列，而不是直接当作独立参考图。

识别为 `frame_animation_sequence` 的典型条件：
- 所有帧尺寸一致，画布外形、透明区域、主体边界和主色基本一致。
- 文件名包含递增编号、帧号、序号或同一资源名前缀，例如 `*_1.png`、`*_6.png`、`*_20.png`。
- 多帧之间只有高光、扫光、阴影、发光、粒子、局部遮罩、进度、按钮按压状态或小装饰发生位置/透明度/亮度变化。
- 变化区域形成可解释运动轨迹，例如从左到右扫过、由浅到深呼吸、由小到大扩散、沿路径移动。

帧动画 JSON 必须记录：
- `animation.is_frame_animation: true`。
- `animation.sequence_type`，例如 `sweep_highlight_button`、`shine_pass`、`loading_progress`、`breathing_glow`、`particle_motion`、`pressed_state_transition`。
- `static_base`：跨帧保持不变的底图、画布形状、圆角、渐变、描边和透明遮罩。
- `animated_elements`：逐帧变化的元素。记录类型、颜色、透明度、模糊、混合方式、相对边界框和运动方向。
- `per_frame_changes`：每帧的编号、文件名、运动元素位置、透明度和亮度变化。
- `invariants_across_frames`：每帧必须完全一致的尺寸、主体轮廓、圆角半径、透明遮罩、底色渐变、文字和图标身份。

对于横向胶囊按钮扫光帧，例如三张 `616x88` 蓝色渐变按钮：静态底图是左右全圆角的蓝色 pill 按钮；动画元素是半透明浅蓝白斜向光带；帧序列表现为光带从左侧进入，经过中间，再向右侧移动。必须保持按钮尺寸、圆角、蓝色渐变和透明外角不变，只允许光带的位置、宽度、透明度和边缘模糊逐帧变化。

如果用户要求重生成这类资源，优先保持帧数、尺寸和帧顺序一致；每一帧必须是同一动画的连续状态，不能生成成互不相关的三个按钮。若用户要求补帧或扩展帧数，依据已有运动轨迹插值或外推，不要改变静态底图。

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

重生成不是复刻。默认目标是“语义一致、风格一致、布局接近，但造型和颜色有较明显变化”的新图。输出不应像参考图的重采样、描摹、轻微改色或局部微调版本。

生成前必须把元素分成：
- `main_elements`：决定语义身份、功能含义、文本可读性、数量关系、状态徽标、关键遮挡关系或主体轮廓的元素。例如 T 字主体、下载箭头、循环箭头、红色错误徽标、数字 `5`、车辆主体、钱袋。
- `secondary_elements`：装饰、星光、高光、阴影、纹理、背景点缀、非关键粒子、小型辅助符号、可选角标或不影响语义的材质细节。

必须保持：
- 所有 `main_elements` 的图标/对象身份，例如金币堆仍是金币堆，垃圾桶仍是垃圾桶，循环箭头仍表示重新生成。
- `main_elements` 的数量级、可读性、主要关系和层级，例如前景金币仍覆盖金币堆右下方，状态徽标仍覆盖主图标前方。
- 大体构图、画布外形、透明遮罩、输出尺寸和风格指纹。

必须变化：
- `main_elements` 的变化范围要保守。优先调整色相、明暗、饱和度、渐变方向、轻微比例、边缘圆角、局部高光/阴影和材质细节；也可以加入小幅旋转、轻微放大/缩小和小范围位置微调。主体外轮廓、决定性部件和可读性只能小幅变化。
- `main_elements` 的几何扰动必须在 JSON 中记录上限：通常旋转 `-8..8` 度、缩放 `90..110%`、位置偏移不超过画布宽高约 `5%`；方向敏感图标、文字、箭头、车辆朝向、状态徽标等要收紧范围，必要时禁止旋转。
- `secondary_elements` 应承担更大的变化和随机性：可改变数量、尺寸、位置、形状、颜色、透明度、节奏、分布或替换为语义兼容的装饰。
- 配色应有较明显变化：可以在同一风格下改用协调的新色组，不要只做几乎不可察觉的色值漂移。
- 当主元素变化空间有限时，优先通过颜色系统体现新变体，例如色相、明暗、饱和度、冷暖关系、渐变方向、渐变停靠点、边缘高光和阴影强度。
- 如果参考图次要元素很少，也要优先在配色、渐变方向、次要高光/阴影、背景/底座色彩和装饰细节上体现新变体，而不是大幅改变主元素轮廓。

禁止：
- 生成与参考图几乎相同的轮廓、颜色和细节。
- 只做缩放、裁切、重采样、轻微锐化或简单换背景。
- 对参考图做近似描摹，导致看起来像同一张图的复制版本。
- 让 `secondary_elements` 的随机变化遮挡、替换、裁切、弱化或混淆 `main_elements`。
- 为了追求差异而让 `main_elements` 失去识别性，例如铃铛变成水滴/灯泡/袋子，环形箭头变成普通弧线，车辆变成无轮块状物。

## 真实透明 PNG

当参考图是 `transparent_freeform`、包含透明角/透明遮罩、透明外边距、透明间距，或组合资源中子图块之间透明时，最终结果必须是真正带 alpha 通道的 PNG。透明预览的棋盘格只是 UI 展示方式，不能被画进图片。

## 全透明与半透明区域

生成前必须检测参考图中的 alpha 区域，并写入 `transparency_analysis`。不要只用“有透明背景”概括。

检测分类：
- `fully_transparent`：alpha 为 `0` 的区域，例如图标外部背景、圆形图标四角、sprite 子图块间距、自由形状外轮廓之外。生成后这些区域必须仍为 alpha `0`。
- `semi_transparent`：alpha 在 `1..254` 的区域，例如抗锯齿边缘、柔光、阴影、玻璃/渐变叠层、半透明侧翼、半透明遮罩。生成后这些区域必须仍为半透明，不得变成实色填充。
- `opaque`：alpha 为 `255` 的主体、文字、实心图形或前景元素。

结构化 JSON 必须记录：
- `fully_transparent_regions`：位置、形状、用途、是否必须保持 alpha `0`。
- `semi_transparent_regions`：位置、形状、颜色、`alpha_range`、代表性采样点、层级和用途。
- `alpha_layers.layers`：内部半透明图层的独立元素列表。对同色不同透明度的图层，必须分层记录。

生成提示词必须明确区分：
- `fully transparent outside/background/gaps after chroma-key removal`
- `semi-transparent internal layers/soft edges must remain translucent`

禁止：
- 把半透明区域生成成纯白、纯黑、纯色不透明或实心填充。
- 把半透明区域误删成完全透明。
- 把全透明背景填成白底、黑底、绿底、棋盘格或任何不透明颜色。
- 只为了通过透明检查而让四角透明，却丢失主体边缘、阴影、叠片或内部半透明层次。

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

- 保持语义身份不变。为每个主体写清 `identity`、`required_traits` 和 `forbidden_substitutes`。如果参考图包含车，输出必须仍是车，而不是普通胶囊形、公交车、滑板车、抽象交通工具或无轮子的装饰块。
- 保持形状定义部件不变。只允许改变轮廓细节、比例、色相、材质细节和装饰纹理，不允许删除决定身份的部件。车要保留两个轮子、座舱/车顶、车窗、车身和可见前后方向；钱袋要保留圆鼓袋身、扎口、顶部褶皱/结扣，以及可见时的货币符号；放大镜要保留封闭镜片和手柄；星星要保留明确尖角。
- 保持关键关系不变。记录主体之间的相对锚点、接触/重叠关系、前后层级和方向。如果钱袋位于车顶，输出中它也必须位于车顶上方并与车发生相同类型的视觉重叠，不能跑到车后、车内、车旁或变成车顶盒。
- 保持数量和可见性不变。参考图中可数的关键对象必须保持相同数量或用户明确要求的数量；不得把两个轮子合成一个轮子、把三枚金币合成一坨、把一个文字标签拆成多个错误标签。
- 只保留参考图已有的遮挡关系。不得新增隐藏、裁切、遮挡或画布外溢，除非参考图本身如此；如果参考图中元素完整可见，输出中也必须完整可见。
- 将允许变化和禁止变化分开写入 JSON。允许变化包括局部比例、轮廓细节、辅色、轻微姿态和装饰；禁止变化包括身份替换、关键部件缺失、关系错位、层级反转、方向翻转和新增遮挡。
- 即使颜色、尺寸、透明度和大致位置匹配，只要图标身份错误、决定性部件缺失、关键关系错误或文字/主体被裁切，也必须视为生成失败。

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



