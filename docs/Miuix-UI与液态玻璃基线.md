# Miuix UI 与液态玻璃基线

> 2026-10-28，按用户指定的两项来源核查。本文件是现有 Figma、UI 交接与 Android 实现的共同依据。这里的“上游”指 compose-miuix-ui 项目，不等同小米官方系统实现。

## 1. 已确定的设计依据

- [jsCanvas 交互示例](https://compose-miuix-ui.github.io/miuix-jsCanvas/)：基础控件、分组、主题与交互表现的参照。
- [Miuix 仓库](https://github.com/compose-miuix-ui/miuix)：实现行为与 API 的依据。
- [组件文档](https://compose-miuix-ui.github.io/miuix/components/index)、[导航动效](https://compose-miuix-ui.github.io/miuix/guide/miuix-nav)、[背景与玻璃底座](https://compose-miuix-ui.github.io/miuix/guide/blur)：对应能力说明。

全部 UI 遵循这一套组件语言与动效体系。优先级为：用户明确的产品行为 > 选定 Miuix 版本的外观与交互基线 > 本项目业务组合与品牌资产。现有 Figma 与旧稿自拟参数需要服从这次基线更新。

这不意味着全屏每一层都加折射。列表、营养数据、表单、设置等仍按 Miuix 的内容层级；玻璃用于对应悬浮表面，并通过具体示例验证。保留应用品牌蓝和碗叶占位，颜色通过主题角色配置。

## 2. 本次核查的版本与范围

| 项目 | 核查结果 |
|---|---|
| 仓库 main 源码快照 | bb7bde3109605b4c98065b53030ba429c39baea9 |
| 本项目固定正式 Release | [v0.9.4](https://github.com/compose-miuix-ui/miuix/releases/tag/v0.9.4)，提交 `39c40f99844227b853f0049a0933b1f3ae6c00ba`；B02 已构建锁定，不随 main 自动升级 |
| jsCanvas 实际页面 | 已打开首页与设置页；可见基础控件、主题/模糊设置及 Miuix 转场选项 |
| 示例设置的样式区分 | FloatingNavigationBar Style 含 Default 与 iOS-like；Transition Style 含 Miuix 与 AOSP |
| 版本注意 | main 比正式 Release 更新；网页示例应用版本不等于依赖版本，也不能证明其部署自本次 main 提交 |
| 本项目状态 | 2026-10-30 B02 candidate-3沿用Figma代表布局／MiSans，修正底栏居中和折射采样；当前APK、几何与像素证据见[B02](reviews/B02/README.md)。vivo解析失败原因及Android17真机新效果待复核，完整业务和G3未验收 |

Release、main、网页部署必须分别记录。不能照 main 抄 API，却直接声称正式发布版具有完全相同的示例与实现。

## 3. 页面与组件映射

| 食谱软件区域 | Miuix 依据 | 项目应做的工作 |
|---|---|---|
| 主题、字阶、色彩 | MiuixTheme 与上游主题系统 | 绑定语义角色；不沿用散落的自定色值与字号 |
| 卡片、按钮、输入、开关、滑块 | miuix-ui 基础组件与 jsCanvas 对应示例 | 复用组件行为，保留业务文案和数据 |
| 设置分组与编辑入口 | miuix-preference；示例 SettingsPage | 对齐行高、留白、标题/摘要/尾部关系 |
| 搜索、筛选、菜单、对话框、底部弹层 | 对应上游组件及示例 | 复用展开、关闭、按压与返回行为；不发明另一套弹簧 |
| 底部三目的地导航 | Miuix 默认浮动导航及其示例 | 保留配餐/食谱/设置的业务目的地；适配显示模式与安全区 |
| 页面转场与返回 | miuix-nav 的 MiuixDefault、Modal 等预设 | 选适合的页面角色，验证手势冲突和状态恢复 |
| 连续圆角 | miuix-squircle 与上游表面实现 | Figma 对齐轮廓，不能只机械增加普通圆角半径 |
| 背景采样、模糊、颜色混合、高光 | miuix-blur；底层 miuix-shader | 正确提供 backdrop；验证滚动、主题及采样坐标 |
| 透镜折射、色散与交互形变 | 仓库 example 的液态玻璃实现 | 作为受版本约束的示例代码适配，区分 iOS-like 外观 |
| 营养表、配餐卡、目标编辑器 | 上述基础控件组合 | 添加业务结构和状态，不改变基础交互语言 |

Figma 后续逐项记录：现有组件 ID、上游组件/源码路径、所用版本、差异、是否已对齐。当前仅完成依据与任务更新，未把全部 Figma 组件重新绘制或验收。

## 4. 液态玻璃：现有能力与边界

上游已提供背景采样、模糊、颜色调整、高光和 Shader 运行底座。已核对以下 main 源码：

- [LiquidGlassNavigationBar.kt](https://github.com/compose-miuix-ui/miuix/blob/bb7bde3109605b4c98065b53030ba429c39baea9/example/shared/src/commonMain/kotlin/component/liquid/LiquidGlassNavigationBar.kt)：其中完整透镜导航入口名为 IosLiquidGlassNavigationBar；包含拖动、按压、受限形变、背景与高光组合。
- [Lens.kt](https://github.com/compose-miuix-ui/miuix/blob/bb7bde3109605b4c98065b53030ba429c39baea9/example/shared/src/commonMain/kotlin/component/liquid/Lens.kt)：包含折射、深度和可选色散的 Shader 效果，并在不支持 RuntimeShader 时退出。
- [SettingsPage.kt](https://github.com/compose-miuix-ui/miuix/blob/bb7bde3109605b4c98065b53030ba429c39baea9/example/shared/src/commonMain/kotlin/SettingsPage.kt)：明确区分 Default 与 iOS-like 导航样式。
- [RuntimeShader.android.kt](https://github.com/compose-miuix-ui/miuix/blob/bb7bde3109605b4c98065b53030ba429c39baea9/miuix-shader/src/androidMain/kotlin/top/yukonga/miuix/kmp/shader/RuntimeShader.android.kt)：按 API 33 判断 RuntimeShader 支持。

因此可以说“有可适配的开源液态玻璃实现”，不能说“本项目的 HyperOS 4 液态玻璃已经完成”，也不能把示例中的 iOS-like 透镜外观当成 HyperOS 4 官方视觉或系统组件。

以 Miuix 默认组件语言为全局基线；参考示例折射能力时保留清晰的适配记录，避免让整个应用变成另一套系统风格。若希望和特定 HyperOS 4 真机系统界面逐像素相同，还需要对应系统版本与设备的实际参照和比对，本轮未作这种验证。

## 5. Android 能力边界

当前官方 blur 文档和 Shader 源码均将 RuntimeShader 效果门槛设为 Android 13 / API 33。不能继续沿用旧稿“API 31 即完整玻璃、API 33 才加折射”的笼统保证。

- API 33+：进入完整 Shader 原型验证；API 满足不等于所有 GPU 和场景均已验收。
- API 33 以下：按锁定依赖的最低系统与 manifest 合并结果决定能否支持；运行时能力门控并提供简化材质。门控本身不能证明低版本 APK 一定可安装。
- 最低可安装系统与最低完整材质系统是两个独立决策。当前不因视觉调研擅自提高产品 minSdk，也不承诺未经构建验证的低版本兼容。

用户后续确认 Android 12 优先清晰简化材质、保留 Miuix 动效；优先单 APK 自动选择，兼容验证失败再拆包。正式 0.9.4 AAR 已实际检查：ui/shader minSdk 24，blur minSdk 33，三项 minCompileSdk 均为 37。只加运行时判断不能消除 Manifest 与类加载问题；完整验收条件见《Android兼容与验证方案.md》。

## 6. 达到“已准备好”的验收条件

- [x] 明确全 UI 的 Miuix 依据，核对对应仓库与示例入口。
- [x] 核对上游玻璃、折射、交互动效及 API 33 能力条件。
- [x] 锁定B02实际构建的依赖与示例代码版本，建立可运行的离线材质原型。
- [x] B02代表浮动导航接入真实滚动背景，保留实际菜单／弹层；当前几何及折射A/B另存原始证据，不代表所有浮层均有玻璃或全部状态验收。
- [ ] 在实际 Android 设备上检查亮暗主题、图片背景、拖动、按压、滑块与键盘。
- [ ] 检查连续切页、返回中断、减少动态效果、低版本和性能降级。
- [ ] 将通过的组件映射到 Figma，完成代表页面视觉与原型核查。

当前状态：B02原型已接入增强材质并开展实际验证；完整验收未完成，不能将像素差异或模拟器成功称为vivo兼容、Android17真机通过或HyperOS4官方视觉复刻。
