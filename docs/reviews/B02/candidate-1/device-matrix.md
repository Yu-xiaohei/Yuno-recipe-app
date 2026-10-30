# B02 设备矩阵

环境：Windows、JDK21、固定 Gradle9.7.1/AGP9.4.1；详见 [构建](../../build.md)。专用 AOSP x86_64 API31/32/33 模拟器，Pixel6 配置、1080×2400、WHPX、host GPU；均为项目独立 AVD，不替代 vivo 真机。

运行证据以 `runtime/test_b02_api<API>_<variant>.json` 及对应截图为准。初轮 API31 的锁定语义失败已另存 `test_b02_api31_debug_before_semantics_fix.json`，当前结果不得覆盖该失败历史。

| 设备 | debug | R8 压缩候选 | 预期材质 |
|---|---|---|---|
| API31 / Android12 | 25 项通过 | 25 项通过 | 清晰材质 |
| API32 / Android12L | 25 项通过 | 25 项通过 | 清晰材质 |
| API33 / Android13 | 33 项通过 | 33 项通过 | 实际背景 blur/lens；两处故障回退通过 |
| vivo / Android12 | 未取得设备信息 | 未执行 | 清晰材质 |

每个模拟器用同一份 debug APK、同一份 R8 APK检查安装、冷启动、三Tab、真实滚动、菜单、弹窗、滑块、锁定后不改重量、ASCII键盘与减弱动画；API33 另检查正常场景无静默回退，以及 effects/绘制异常后的清晰降级。

六组检查均通过，累计 166 条检查记录（包含重复的进程存活断言，不是 166 项独立业务测试）。最终报告中的 `apkSha256` 绑定实际安装的 APK；所有 API 共用的两份 APK 哈希另见 [验证记录](verification.json)。总负责人已目视检查 API31/R8 锁定滑块及 API33/R8 初始、滚动、绘制失败回退截图，未据此宣称 HyperOS 官方材质或广泛 GPU 性能验收。

早期 IME 和返回驱动失败分别保留为各 API 的 `before_ime_driver_fix` / `before_back_driver_fix`；最终脚本保留组合态不提交检查，分别验证返回及取消恢复导航。只对明确的 UI idle/root-node 暂态错误有限重试；次数与原因记在最终报告。

MiSans、中文 IME、大字体 1.0/1.3/2.0 与暗色全矩阵、性能和 vivo 实际体验尚无完整证据，不能将本表视为正式兼容性声明或 B02 人工通过。
