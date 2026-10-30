# B02 工具链与 Android 兼容原型

2026-10-31用户要求收工并同步Git，功能开发暂停；见[收工总结](收工总结-2026-10-31.md)和[同步计划](git-sync-plan.json)。现有G3状态不因归档而改变；实际提交／推送以对应执行结果为准。

用户于 2026-10-30 发出新的开工指令，已开始 B02；[开工记录](start.json)明确替代此前等待明日的安排。B03 及后续未开始，Gitee 重试保持暂停，没有为本批提交或推送。

当前候选`B02-candidate-3`沿用Figma代表布局及原始MiSans，针对用户反馈修订玻璃折射和底栏居中。工程验证固定工具链、Miuix交互、低版本材质隔离和压缩安装。使用合成数据、隔离包名和本机debug签名；食谱仓储、配餐计算、云同步与正式发行尚未实现。

阅读入口：

- [构建与复测](../../build.md)
- [材质与交互范围](material-baseline.md)
- [API 隔离审计](api-audit.md)
- [设备矩阵](device-matrix.md)
- [MiSans 许可核查](font-audit.md)
- [Figma 布局与差异](ui-alignment.md)、[原始资产清单](figma-assets.json)
- [已实现范围复核](review.md)、[验证记录](verification.json)、[候选清单](candidate-manifest.json)
- `runtime-candidate-3/test_b02_*.json`／`.png`：当前APK的检查与截图，逐包绑定hash；含实际居中测量、折射A/B及APK检查。
- `candidate-1/`、`candidate-2/`及旧runtime：历史候选和失败证据；`runtime-candidate-3-before-width-refinement/`是恢复原栏宽前的过渡版本，均不代表当前包通过。

用户已同意按官方许可接入原始字体及“本应用使用 MiSans 字体”署名。21份字体已审计，工程仅包原始VF、完整官方PDF、版权与可读协议；字体没有修改或子集化。

本候选运行、目视和独立总检以当前[验证记录](verification.json)为准。vivo Android12“无法解析安装包”的准确原因未确认，需型号、实际收到的APK及原始报错；Android17效果尚待新包复测。中文IME、完整状态矩阵、罕见字回退和性能仍待验证。整批为`in_progress`，未完成整批G1/G2/G3，不计入已接受的App实现进度；不自动推进B03。暂停记录在[pause-checkpoint.md](pause-checkpoint.md)，用户已明确继续。独立SDK／AVD和失败日志保留。
