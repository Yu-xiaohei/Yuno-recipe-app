# B02 已实现范围复核

候选：`B02-candidate-1`；2026-10-30。本记录只覆盖当前原型和工具链，不是整批 G1/G2 完成或用户 G3 接受。

执行者：总负责人及原型 UI 子 Agent。独立只读审查：`b02_independent_review`；总负责人复核并绑定最终清单。审计、开发和设备写入分离，同一时间未由多个 Agent 共写源码或操作同一模拟器。

当前结果：

- 固定版本实际构建 debug/R8 两种 APK；两种 Lint 各 0 错误、7 警告。未加 baseline 或屏蔽检查。
- 原有全套51项回归通过；最终计划/证据调整后受影响29项契约测试再次通过。
- 六份最终设备报告均通过，共166条断言记录，含重复的进程存活断言；不是166项独立功能。安装报告的 APK SHA-256 与当前产物一致。
- 普通 API33 场景同时拒绝异常及清晰回退，避免“曾进入增强分支”误报成功；effect/draw 故障分别验证真实边界、清晰回退和进程存活。
- Slider 锁定检查同时覆盖 disabled 语义和实际拖动不改重量。IME 测试保留组合态阻止提交，并分别验证 committed query、返回、取消。
- R8 mapping 保留 `EnhancedMaterial`、`EnhancedMaterialKt`、`LensKt`；API31/32 压缩包安装和冷启动通过。
- 两变体 merged manifest 均 min31/target37，无 INTERNET、无 blur 启动初始化器，备份禁用并有明确提取规则。
- 两包 `assets/miuix/LICENSE` 与原文件一致；629个依赖校验 artifact 均有 SHA-256。首次信任清单不等于所有第三方内容都已独立审计。
- 总负责人已目视检查 API31/R8 锁定页及 API33/R8 正常、滚动、绘制异常回退截图。未把此原型称为正式 UI、正式食谱业务或 HyperOS 官方效果。
- PNG Git 属性经检查已关闭文本转换，过滤前后 blob hash 一致；B01 三份审阅清单原 hash 未变，参考数据无 Git 差异。

当前已实现范围没有尚未解决的 S0/S1 发现。初轮发现和修复见 `docs/问题复盘与防复发.md` ISSUE-20261030-24～29；失败报告保留，没有修改业务预期来掩盖失败。

尚未完成：MiSans 实际包/许可/字重/覆盖/署名与显示、中文 IME 和完整亮暗/大字矩阵、vivo 型号/系统/真机安装、广泛 GPU/性能、大屏/旋转、正式业务及整批三道关卡。包名与签名均为隔离原型用途。B03、Git 提交/推送、云服务及发布未开始。

数据及执行命令见 [verification.json](verification.json)，绑定文件见 [candidate-manifest.json](candidate-manifest.json)。后续修改字体或源码需重跑受影响检查并更新候选，不能复用旧 APK 的结果证明新包通过。
