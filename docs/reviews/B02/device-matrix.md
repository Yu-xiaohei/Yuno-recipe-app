# B02 设备矩阵

环境：Windows、JDK21、固定 Gradle9.7.1/AGP9.4.1；详见 [构建](../../build.md)。专用 AOSP x86_64 API31/32/33 模拟器，Pixel6 配置、1080×2400、WHPX、host GPU；均为项目独立 AVD，不替代 vivo 真机。

当前候选`B02-candidate-3`，证据以`runtime-candidate-3/test_b02_api<API>_<variant>.json`和原始截图为准，逐包绑定同一变体APK。旧runtime及`runtime-candidate-3-before-width-refinement/`保留历史，不作为当前包通过证明。

| 设备 | debug | R8 压缩候选 | 预期材质 |
|---|---|---|---|
| API31 / Android12 | 38条通过 | 38条通过 | 清晰材质 |
| API32 / Android12L | 38条通过 | 38条通过 | 清晰材质；首轮采集失败单独保留 |
| API33 / Android13 | 47条通过 | 47条通过 | 实际背景blur/lens；两处故障回退通过 |
| vivo / Android12 | 用户报告旧包无法解析 | 当前包未执行 | 预期清晰材质；根因未确定 |
| 用户Android17设备 | 旧包能装、效果偏毛玻璃 | 当前包未复测 | 不以API33模拟器结果代替 |

每个模拟器用同一份 debug APK、同一份 R8 APK检查安装、冷启动、三Tab、真实滚动、菜单、弹窗、滑块、锁定后不改重量、ASCII键盘与减弱动画；API33 另检查正常场景无静默回退，以及 effects/绘制异常后的清晰降级。

当前新增检查包括实际安装APK字节、真实折射管线回调；原Figma结构、MiSans、图像解码、菜单滚动及署名检查保留。断言数含重复进程存活，不是独立业务功能数，最终总数及两包hash见[验证记录](verification.json)。

早期 IME 和返回驱动失败分别保留为各 API 的 `before_ime_driver_fix` / `before_back_driver_fix`；最终脚本保留组合态不提交检查，分别验证返回及取消恢复导航。只对明确的 UI idle/root-node 暂态错误有限重试；次数与原因记在最终报告。

当前R8包另外在API31和API33捕获亮暗×1.0/1.3/2.0字号×首页/配餐/设置，共36张代表视口截图。视觉脚本先比较设备`pm path`实际APK的SHA-256与传入文件，再操作设备；退出恢复原字体和夜间偏好。捕获报告状态保持`captured-pending-human-inspection`，人工目视范围另记verification.json，不把自动截图当作通过。

中文IME、所有滚动/弹层/键盘状态、罕见字回退/TalkBack、性能、vivo和旋转大屏仍未完整验证，本表不构成正式兼容声明或B02人工接受。

专项运行：

- API31／33 R8分别执行1.0／2.0字号×三个真实Tab，共12组几何与选中状态检查。原始cell／icon／label坐标及误差在`*_navigation.json`，不以UI节点外框代替实际内部布局。
- API33 R8明暗两组同APK折射A/B。校准背景、主题、字号和九矩形一致，外部背景像素相同。原语义范围底部裁剪，旧指标保留为历史；当前`test_b02_api33_release_glass_reanalysis.json`按固定源码与实际布局派生完整表面[170,2069,911,2206]，对原始PNG离线重算。排字图的圆角边带28894像素、变化比例19.37%／19.52%、平均差10.22／9.73，未放宽阈值。布局边界非光学轮廓测量，此次非新设备运行；证明存在实际折射，不证明品牌等效或用户视觉接受。
- 两包API31签名、CRC／无重复ZIP项、四ABI和ZIP对齐通过，原件字体及17份SVG一致；`test_b02_apk_audit.json`保留官方工具返回，不据此宣称vivo已修复。
- API32初次debug采集cat失败的报告／四图保留在`test_b02_api32_before_capture_diagnostics/`。只补失败诊断后复测，断言／重试策略及APK均未改；准确原始原因未知。API31／33普通检查在这次诊断字段增强前执行。
