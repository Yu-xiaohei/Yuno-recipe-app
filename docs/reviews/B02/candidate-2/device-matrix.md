# B02 设备矩阵

环境：Windows、JDK21、固定 Gradle9.7.1/AGP9.4.1；详见 [构建](../../build.md)。专用 AOSP x86_64 API31/32/33 模拟器，Pixel6 配置、1080×2400、WHPX、host GPU；均为项目独立 AVD，不替代 vivo 真机。

当前证据以`runtime-candidate-2/test_b02_api<API>_<variant>.json`和原始截图为准，均绑定深色修正后的同一变体APK。旧`runtime/`及`runtime-candidate-2-before-dark-fix/`仅保留历史及失败链，不作为当前包通过证明。

| 设备 | debug | R8 压缩候选 | 预期材质 |
|---|---|---|---|
| API31 / Android12 | 37条通过 | 37条通过 | 清晰材质 |
| API32 / Android12L | 37条通过 | 37条通过 | 清晰材质 |
| API33 / Android13 | 45条通过 | 45条通过 | 实际背景blur/lens；两处故障回退通过 |
| vivo / Android12 | 未取得设备信息 | 未执行 | 清晰材质 |

每个模拟器用同一份 debug APK、同一份 R8 APK检查安装、冷启动、三Tab、真实滚动、菜单、弹窗、滑块、锁定后不改重量、ASCII键盘与减弱动画；API33 另检查正常场景无静默回退，以及 effects/绘制异常后的清晰降级。

六组共238条检查记录（包含重复进程存活断言，不是238项独立业务测试）。当前新增检查包含Figma首页结构、MiSans运行日志、SVG/图像解码错误、实际缩略图尺寸、三个真实菜单及“食材”滚动可达、署名入口。两份APK的hash见[验证记录](verification.json)。

早期 IME 和返回驱动失败分别保留为各 API 的 `before_ime_driver_fix` / `before_back_driver_fix`；最终脚本保留组合态不提交检查，分别验证返回及取消恢复导航。只对明确的 UI idle/root-node 暂态错误有限重试；次数与原因记在最终报告。

当前R8包另外在API31和API33捕获亮暗×1.0/1.3/2.0字号×首页/配餐/设置，共36张代表视口截图。视觉脚本先比较设备`pm path`实际APK的SHA-256与传入文件，再操作设备；退出恢复原字体和夜间偏好。捕获报告状态保持`captured-pending-human-inspection`，人工目视范围另记verification.json，不把自动截图当作通过。

中文IME、所有滚动/弹层/键盘状态、罕见字回退/TalkBack、性能、vivo和旋转大屏仍未完整验证，本表不构成正式兼容声明或B02人工接受。
