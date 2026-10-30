# B01 UI 与字体工程契约

候选：`B01-ui-1`；核查日期：2026-10-28；任务：`P0-06`。本文是源码核查和接入要求，不表示 Android 工程、字体资源或运行效果已通过验收。B00 的人工接受不代替 B01 的人工接受。

## 1. 固定依据与状态

| 项目 | 依据 | 本次结论 |
|---|---|---|
| Miuix 候选版本 | `v0.9.4` | 本文只使用这个 tag 的源码；构建验证后才可锁定为项目依赖 |
| tag 对应提交 | `39c40f99844227b853f0049a0933b1f3ae6c00ba` | GitHub tag ref API 当次回读确认 |
| 既有 main 调研快照 | `bb7bde3109605b4c98065b53030ba429c39baea9` | 与 release 分开，不能混抄 API |
| jsCanvas | 用户指定的交互参考 | 页面部署未绑定到本次 tag，不作为版本一致性证据 |
| 字体家族 | MiSans | 用户已确认；本次未下载字体，工程内没有可核验的字体二进制或 SHA-256 |
| 材质与系统 | Android 12 简化材质；API 33+ 增强路径另验 | 本文不证明单 APK 安装、启动或 GPU 效果 |

后续若更换候选依赖版本，必须重新核对本表、组件签名、AAR 元数据、字体注入与低版本运行；不能仅修改版本号。

固定源码链接的公共前缀为：

```text
https://github.com/compose-miuix-ui/miuix/blob/39c40f99844227b853f0049a0933b1f3ae6c00ba/
```

以下所有 Miuix 路径均相对于该提交的仓库根目录。版本、路径和下列参数片段一起使用；参数片段有意省略默认值及无关参数，不能直接当作完整 Kotlin 声明复制。

## 2. 已核实的关键入口

### 2.1 主题与全局壳体

| 路径 | 已存在的入口及关键参数 |
|---|---|
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/theme/MiuixTheme.kt` | `MiuixTheme(controller: ThemeController, textStyles: TextStyles, content)`；另有 `MiuixTheme(colors: Colors, textStyles: TextStyles, content)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/theme/TextStyles.kt` | `defaultTextStyles(...) : TextStyles` 与 `TextStyles.copy(...)`；`MiuixTheme` 没有已核实的 `fontFamily` 参数 |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/Scaffold.kt` | `Scaffold(topBar, bottomBar, popupHost, contentWindowInsets, content: (PaddingValues) -> Unit, ...)`；默认 popup host 为 `MiuixPopupHost()` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/NavigationBar.kt` | `FloatingNavigationBar(..., content)`；`FloatingNavigationBarItem(selected: Boolean, onClick: () -> Unit, icon: ImageVector, label: String, ...)` |
| `miuix-nav/src/commonMain/kotlin/top/yukonga/miuix/kmp/nav/core/NavDisplay.kt` | `NavDisplay(backStack: NavBackStack, ..., onBack, transition, effects, content: NavEntryBuilder.() -> Unit)`；另有 `navController: NavController` 重载 |
| `miuix-nav/src/commonMain/kotlin/top/yukonga/miuix/kmp/nav/transition/NavTransitions.kt` | `NavTransitions.MiuixDefault`、`NavTransitions.Modal`、`NavTransitions.None` |

三个全局目的地沿用“配餐 / 食谱 / 设置”；默认选择食谱。库内“食材”属于类别层级。各 Tab 的状态、草稿、返回保护由应用负责，不由导航动画隐式保存。不得把内部 `route.pattern` 原样当作已实现的上游导航 API。

`Scaffold` 的内容 padding 必须被消费一次；不得既忽略安全区也在多层重复叠加。键盘、三键导航、手势返回和弹层嵌套须在 B02/P1 实测。保存后离开必须等本地事务成功；动画完成不能作为保存成功的条件。

### 2.2 输入、滑块与弹层

| 路径 | 已存在的入口及关键参数 |
|---|---|
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/SearchBar.kt` | `SearchBar(inputField: @Composable () -> Unit, onExpandedChange: (Boolean) -> Unit, ..., expanded: Boolean, content)`；`InputField(query: String, onQueryChange: (String) -> Unit, onSearch: (String) -> Unit, expanded: Boolean, onExpandedChange: (Boolean) -> Unit, ...)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/TextField.kt` | `TextField(state: TextFieldState, ..., inputTransformation, textStyle, keyboardOptions, onKeyboardAction, ...)`；另有 `value: TextFieldValue` 和 `value: String` 重载 |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/Slider.kt` | `Slider(value: Float, onValueChange: (Float) -> Unit, ..., enabled: Boolean, valueRange: ClosedFloatingPointRange<Float>, steps: Int, onValueChangeFinished: (() -> Unit)?, ...)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/overlay/OverlayDialog.kt` | `OverlayDialog(show: Boolean, ..., title: String?, summary: String?, onDismissRequest: (() -> Unit)?, renderInRootScaffold: Boolean, content)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/overlay/OverlayListPopup.kt` | `OverlayListPopup(show: Boolean, ..., onDismissRequest: (() -> Unit)?, renderInRootScaffold: Boolean, content)` |

`InputField` 的公开回调传递 `String`，单独消费此回调不能证明应用能识别 IME composition。S03 的适配必须保留组合态；可在 `SearchBar.inputField` 插槽使用同版本支持 `TextFieldValue` 或 `TextFieldState` 的输入适配，保留 Miuix 视觉，并在实际锁定的 Compose 版本核对 composition 读取方式。不得按每次字符串变化立即查询或保存历史，也不得修改基础控件的视觉体系来规避问题。

S12 滑块的 domain 值来自数量契约；UI 的 `Float` 只是控件桥接，不是持久化或营养计算精度。固定原始锚点 ±100g、0≤重量<1g 红框与 ≥1g 保存守卫均由 domain 校验。上游滑块要求 `valueRange.start < valueRange.endInclusive`；可达范围退化为单值时应用显示该结果并禁用可调交互，不能向组件传入相等端点造成异常。不可达、缺失营养和份数删除不得依靠颜色或滑块自己修正。

### 2.3 内容与设置

| 路径 | 已存在的入口及关键参数 |
|---|---|
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/Card.kt` | `Card(..., content: ColumnScope.() -> Unit)`；另有 `onClick`、`onLongPress`、`pressFeedbackType` 重载 |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/Component.kt` | `BasicComponent(title, summary, startAction, endActions, bottomAction, onClick, enabled, ...)`；另有自定义内容重载 |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/Button.kt` | `Button(onClick, ..., enabled, content: RowScope.() -> Unit)`；`TextButton(text, onClick, ..., textStyle, ...)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/Switch.kt` | `Switch(checked: Boolean, onCheckedChange: ((Boolean) -> Unit)?, ..., enabled: Boolean)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/TabRow.kt` | `TabRow(tabs: List<String>, selectedTabIndex: Int, onTabSelected: (Int) -> Unit, ...)` |
| `miuix-ui/src/commonMain/kotlin/top/yukonga/miuix/kmp/basic/ProgressIndicator.kt` | `LinearProgressIndicator(..., progress: Float?, ...)` 与 `CircularProgressIndicator(..., progress: Float?, ...)` |
| `miuix-preference/src/commonMain/kotlin/top/yukonga/miuix/kmp/preference/ArrowPreference.kt` | `ArrowPreference(title: String, ..., summary: String?, startAction, endActions, bottomAction, onClick, enabled, ...)` |

公开食谱卡、配餐快照卡和独立食材行使用不同的状态模型。框架的 Card 只是表面，不应把页面分组包成多层嵌套卡片。数据表、冲突差异、营养汇总、日历和导入摘要是应用业务组合，不能声明上游存在同名组件。

## 3. 33 个 UX 角色的映射

“业务组合”表示应用要实现的组合，不是上游类名；最终 API 绑定在构建锁定后落到代码。所有角色使用同一字体和语义状态，并保留 UX 的原 screen/flow ID。

| UX 角色 ID | 上游基础或应用组合 | 接入重点 |
|---|---|---|
| `app_shell` | `Scaffold`、`FloatingNavigationBar`、`NavDisplay` | 三 Tab、默认入口、返回及状态恢复 |
| `loading_feedback` | `CircularProgressIndicator` + 业务组合 | 首载与刷新分开，不遮挡可用内容 |
| `recipe_card` | `Card` + 业务内容 | 图片、标题、单位、来源与缺失状态 |
| `status_feedback` | 业务组合；Miuix 文字与按钮 | 空、错、离线、失败、冲突语义分开 |
| `search_input` | `SearchBar` + 保留 composition 的输入适配 | ≥2 字、IME、有效提交历史 |
| `history_chip` | 业务组合 | 最多 5 行、换行实测、超出清理 |
| `confirm_dialog` | `OverlayDialog` | 确认、取消、失败与草稿保护 |
| `filter_group` | `OverlayListPopup` + 业务选项 | 保留 Figma 已确认分档与 OR/AND |
| `choice_control` | 业务选择状态 + 适用基础控件 | 单多选与取消不提交 |
| `modal_surface` | `OverlayDialog` / `OverlayListPopup` | 遮罩、返回、滚动及安全区 |
| `detail_image` | 应用图片适配 | 兜底图片与失败不阻塞内容 |
| `nutrition_summary` | 业务组合 | actual/goal/null/单位与状态 |
| `ingredient_row` | `BasicComponent` + 业务展开 | 生熟口径及来源 |
| `primary_action` | `Button` / `TextButton` | 执行中防重复、禁用原因 |
| `day_summary` | 业务组合 | 只合计当前日期的有效保存记录 |
| `meal_slot_card` | `Card` + 业务组合 | 日期餐次唯一、空餐次与历史 |
| `calendar_control` | 业务日历组合 | 本地日期、无餐日期可选 |
| `context_readonly` | 业务只读内容 | 日期餐次不被路由或键盘误改 |
| `nutrition_table` | 业务组合 | 大字体纵向排列、未知不中和为 0 |
| `entry_card` | `Card` + 配餐条目状态 | xN、聚合量、减一份与锁定 |
| `weight_control` | `Slider` + domain 适配 | 固定锚点、无效值与单值范围 |
| `toggle_control` | `Switch` | 事务成功后才呈最终状态 |
| `sticky_action` | 应用布局 + `Button` | 键盘和系统栏以上可达 |
| `form_input` | `TextField` + 校验适配 | 单位、错误、隐藏字段不参与校验 |
| `ingredient_diff` | 业务组合 | 原始与实际用量、不可达偏差 |
| `more_menu` | `OverlayListPopup` | 锁定、删除、取消及失败 |
| `settings_group` | 业务分组 + Miuix 内容基础 | 非重复卡片嵌套，统一层级 |
| `settings_row` | `ArrowPreference` / `BasicComponent` | 标题摘要及尾部行为 |
| `comparison_panel` | 业务差异组合 | 双方副本保留，大字体上下比较 |
| `import_summary` | 业务组合 | 有效/无效计数、逐项原因、零写入预览 |
| `progress_feedback` | `LinearProgressIndicator` + 取消操作 | 完成进度不冒充实际提交成功 |
| `release_summary` | 业务组合 | 版本、完整性和安装结果分开 |
| `context_picker` | `OverlayDialog` + 业务日期/餐次组合 | 选择后复核已有记录及锁定 |

此表未将任何 `componentRoles` 对象改成已实现；`screen-contracts.json` 继续保留原角色 ID。该 JSON 的 `upstreamApi=null` 表示尚无已构建绑定，不是本次源码核查失败。

## 4. MiSans 工程安排

### 4.1 官方资料已核实的范围

- 官方网站提供 MiSans 家族与下载入口，简体中文对应 MiSans；网站区分 MiSans、MiSans Latin、MiSans TC 和 MiSans L3，不把多个不同家族混称为一个已安装文件。
- 官方 FAQ 明确允许软件嵌入，并要求在软件中特别注明使用 MiSans。嵌入说明与具体下载包条款都要留档；官网“免费商用”描述不能替代字体文件的许可审阅。
- 官方 FAQ 对字体外观修改有约束。本项目不在未核验下载包条款前进行字形修改、子集化或字体格式再分发。
- 本轮没有下载字体包、接受下载协议、写入字体资产或获取字体文件 hash。许可包内容、文件版本、字体内部 family/style 名称与实际字符覆盖均为 `not_run`。

### 4.2 B02 字体接入的完成条件

1. 从官方入口取得所需字体和随附条款，记录下载地址、日期、包版本或可用版本标识、文件名、SHA-256、许可文件路径。临时下载物使用 `tmp_` 规则，正式字体是产品资产，不改成临时文件名。
2. 检查实际字体元数据：family、style、字重、可变轴及取值范围。不得根据文件名假设 `MiSans VF` 与静态文件可互换；不伪造不存在的 Medium/Semibold/Bold。
3. 在项目资源定义统一 `FontFamily`，显式匹配经核验的字重。优先使用 APK 内字体以支持首次离线使用，不依赖 vivo 系统安装 MiSans，也不要求设备升级 HyperOS。
4. 对 `TextStyles` 的全部 14 个角色设置同一字体家族：`main`、`paragraph`、`body1`、`body2`、`button`、`footnote1`、`footnote2`、`headline1`、`headline2`、`subtitle`、`title1`、`title2`、`title3`、`title4`。保留固定版本 Miuix 的字号、行高及语义字重，在字重文件不齐时停止视觉定稿，不能让部分角色静默回到另一字体。
5. 检查按钮、输入、占位、弹窗、导航和基础控件的默认/内部 textStyle 是否读取统一主题；必要的适配应集中在 `core/design`，不在各页面散落重设字阶。emoji 或系统安装器等系统界面不视为应用字体的一部分。
6. 完成字体说明的页面入口与用户可见文案确认。可以沿用已存在的第三方许可入口，但不能擅自新建未确认的名称或直接发布内部占位。

### 4.3 缺字与显示验证

- 产品名称中的 `の`、中文食谱名、拼音、ASCII、`g / mg / kcal`、百分号、小数、`± / × / ≤ / ≥` 和长数字必须建立字符覆盖检查，不凭“中文字体”推定全部存在。
- 正常中文、数字与单位使用 MiSans；仅遇缺字允许系统字体解析器提供字形兜底，不能把这一点扩大成日常混用字体的设计规范。核心文案发生缺字时必须先报告并补齐已授权的覆盖方案。
- 稀有字、emoji、字体缩放、斜体合成和可变字体轴行为需在实际 Compose/JDK/Android 组合核验；本轮没有证明任一设备的回退结果。
- 字体缩放至少检查 1.0、1.3、2.0；同时检查深色、长标题、两行按钮、营养数值、中文键盘及安全区。不得为适配控件宽度而把字体缩到不可读。

## 5. 材质、动画与运行关卡

API 31/32 的路径保持清晰、可读的 Miuix 表面。当前没有本项目的 `miuix-blur` 接入证明；上游 minSdk 和高版本类引用仍按 [Android兼容与验证方案](../Android兼容与验证方案.md) 审计。API 33+ 增强材质不能成为核心交互、保存、导航或字体加载的前置条件。

减弱动画采用经锁定版本核验的可用入口或应用适配。`NavTransitions.None` 是源码中存在的无动画预设，但切换它之前仍须验证草稿保护、返回和状态恢复。不得因动画关闭跳过业务校验，也不自创一套与 Miuix 冲突的全局弹簧参数。

| 阶段 | 必须保留的证据 |
|---|---|
| B01 当前 | 固定提交与已核实签名、字体待落地项、33 角色覆盖、内部命名与已确认文案边界 |
| B02 | 依赖锁定、编译、字体资源/许可/hash、API 31/32/33 安装冷启动、增强/简化路径 |
| B04/P1 | 代表组件与三 Tab、暗色/大字/IME/安全区、退出草稿保护、统一字体实际截图 |
| 发布前 | 字体许可与归属说明、正式包压缩后行为、设备性能与缺字回归 |

未完成 B02 的字体和 API 验证，不得把 D10 改成全部解决。未确认新增可见文案，不得将 `VISIBLE_NAME_PENDING_*`、screen ID 或本文业务注释放入发布字符串。

## 6. 一手来源

- MiSans 官方首页：<https://hyperos.mi.com/font/zh/>
- MiSans 官方下载入口：<https://hyperos.mi.com/font/zh/download/>
- MiSans 官方 FAQ（本次成功读取其页面内官方中文数据）：<https://hyperos.mi.com/font/zh/faq/>
- Compose 官方字体说明：<https://developer.android.com/develop/ui/compose/text/fonts>
- Miuix tag ref：<https://api.github.com/repos/compose-miuix-ui/miuix/git/ref/tags/v0.9.4>
- Miuix release：<https://github.com/compose-miuix-ui/miuix/releases/tag/v0.9.4>
- 固定提交源码树：<https://github.com/compose-miuix-ui/miuix/tree/39c40f99844227b853f0049a0933b1f3ae6c00ba>
- 用户指定交互参考：<https://compose-miuix-ui.github.io/miuix-jsCanvas/>

源码读取采用上述固定提交的 `raw.githubusercontent.com` 文件。在线官方文档可能随 main 更新，因此真实参数以本次固定源码路径为准。本文没有使用非官方字体镜像，没有读取凭据，没有操作 Figma 或云端用户数据。
