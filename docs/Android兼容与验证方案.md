# Android 兼容与验证方案

> 2026-10-30 更新。用户已确认：Android12优先清晰简化材质、保留Miuix动效，优先单APK。当前candidate-3修正折射和导航并重新取证；用户报告vivo Android12“无法解析安装包”，精确原因尚未确认。任何模拟器成功不等于该真机已修复，详见[B02设备矩阵](reviews/B02/device-matrix.md)。

## 1. Android 12 能否正常使用

可以将 Android 12 作为完整业务功能的支持目标。食谱浏览、搜索、配餐、重量调配、营养目标、JSON 导入导出和 WebDAV 不依赖液态玻璃 Shader。兼容实现通过验收后，用户安装普通 APK 即可使用，无需系统级主题或额外框架。

Android 12 / API 31 与 Android 12L / API 32 使用清晰的着色表面、连续圆角、边缘和适量静态高光；必要时增加不透明度，保证背景滚动时文字清晰。保留可用的 Miuix 按压、弹簧、菜单、弹层及页面转场。系统减弱动画设置和低性能降级应对两个材质分支同样生效。

损失集中在高级材质：不启用当前 `miuix-blur` 的实时背景 Shader 模糊、动态高光/噪声与透镜折射、色散；不能用半透明色块声称已达到同等效果。不承诺 Android 12 获得 Android 13+ 的完整玻璃效果，也不将业务功能删减作为视觉降级的一部分。

Android 13+ / API 33+ 可进入增强材质分支，但仍需验证 GPU、滚动采样、亮暗主题及性能；API 达标并不等于已验收。

## 2. 已核实的依赖限制

2026-10-28 已实际下载并解包 Maven Central 的 0.9.4 正式 Android AAR，记录 Manifest、AAR metadata 和 SHA-256，见 `reports/preflight-2026-10-28/miuix-artifacts.json`。

| 0.9.4 AAR | Manifest minSdk | AAR minCompileSdk |
|---|---:|---:|
| miuix-ui-android | 24 | 37 |
| miuix-shader-android | 24 | 37 |
| miuix-blur-android | 33 | 37 |

`compileSdk` 是构建需要的平台，`minSdk` 是可安装的最低系统，二者不是同一个数。构建使用 SDK 37，不意味着用户手机必须升级到 Android 37。

现有旧稿的 minSdk 29 仅作为待验证的兼容候选保留；本次不擅自提高最低系统。Android 12/12L 是必须覆盖的验收目标，最终 minSdk 随完整依赖图和测试结果锁定。旧稿 target 35 也不直接当作已完成的构建配置。

仅在 Composable 中写 `SDK_INT >= 33` 不足以解决问题：高 minSdk 的依赖首先会影响 Manifest 合并，其次还需排除低版本提前加载高 API 类、静态初始化及非 UI 调用路径。不能仅加 `tools:overrideLibrary` 消除报错后就宣称兼容。

## 3. 单 APK 的工程方案和退出条件

1. 先让基础 UI、业务和简化材质在低版本可构建、冷启动。基础路径不得要求 `miuix-blur` 初始化。
2. 将 API 33+ 材质入口放在独立适配边界内；检查上游及传递依赖的 API 引用、初始化、Manifest 和压缩后行为。低版本选择简化材质，增强路径按系统能力及效果开关启用。
3. 对高 minSdk AAR 的处理需形成可审查方案：审计后的小范围兼容适配、或其他经验证的依赖处理。任何 Manifest 例外必须附源码/API 检查、Lint 及低版本安装运行证据。B02 候选保留原 AAR，使用范围明确的 overrideLibrary 配合独立 API33 入口、R8 保留、实际故障回退及低版本安装检查；[审计](reviews/B02/api-audit.md)不替代真机或 G3。
4. 同一个候选 APK 在 API 31、32、33+ 分别完成安装、冷启动和材质选择；同时检查 release 压缩包。基本功能不得因增强材质失败而崩溃。
5. 如无法在合理维护成本下证明安全，采用已获用户同意的兼容版和增强版：兼容版不包含高版本玻璃依赖，增强版 minSdk 33。拆包时再设计相同应用身份、签名及递增 versionCode 的升级关系，并验证保留本地数据，避免两个包互相无法覆盖。

首版不引入 CPU 截屏模糊或另一套大型渲染库来追求低版本折射；优先稳定清晰的 Miuix 表面。无需为是否存在高级玻璃单独改变配餐数据库、导入格式或同步协议。

## 4. 必须通过的验证矩阵

| 环境 | 最少验证 | 当前状态 |
|---|---|---|
| Android12 / API31 | 安装、冷启动、简化材质、亮暗、键盘与返回 | 当前candidate-3逐包及几何结果见B02矩阵；vivo解析失败未解决，完整业务未验收 |
| Android12L / API32 | 安装／启动、低版本材质，旋转或大屏布局 | 当前candidate-3结果及首次采集失败另见B02；旋转／大屏与完整业务未验收 |
| Android13 / API33 | Shader边界、增强／简化切换、失败回退 | 当前candidate-3逐包、像素A/B及故障注入见B02；广泛GPU／完整业务未验收 |
| Android17 / API37及较新系统 | 实际外观、完整流程、安全区、安装更新 | 用户报告旧包可装但效果偏毛玻璃；当前包尚未真机复测，也未做API37模拟器验证 |
| API 29/30（若保留 minSdk 29） | 安装/启动、基础渲染与核心流程 | 待决定最终支持范围后执行 |
| 真机性能 | 长列表与图片、快速切页、弹层/键盘叠加、连续拖动、持续发热 | 待实测；不预报帧率结论 |

所有支持环境需覆盖：断网启动、保存后杀进程重开、字体放大、手势/三键导航、减弱动画、JSON 错误输入、同步失败、升级保留记录。调试版与正式压缩版分别验证。以安装、日志和运行证据确认，不以截图或能编译代替。

## 5. 依据

- [Miuix blur 文档](https://compose-miuix-ui.github.io/miuix/guide/blur)：API 33 Shader 效果及能力门控。
- [Android AGSL 文档](https://developer.android.com/develop/ui/views/graphics/agsl)：Android 图形 Shader 能力。
- [Android uses-sdk](https://developer.android.com/guide/topics/manifest/uses-sdk-element)：最低系统与目标系统语义。
- [Miuix 0.9.4](https://github.com/compose-miuix-ui/miuix/releases/tag/v0.9.4)：正式版本参照。main、网页示例和正式 AAR 分别记录。
