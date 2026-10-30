# B02 工具链与 Android 兼容原型

用户于 2026-10-30 发出新的开工指令，已开始 B02；[开工记录](start.json)明确替代此前等待明日的安排。B03 及后续未开始，Gitee 重试保持暂停，没有为本批提交或推送。

当前候选`B02-candidate-2`按原Figma恢复食谱首页、今日配餐和设置的代表布局，集成原始MiSans。工程验证固定工具链、Miuix交互、低版本材质隔离和压缩安装。使用合成数据、隔离包名和本机debug签名；食谱仓储、配餐计算、云同步与正式发行尚未实现。

阅读入口：

- [构建与复测](../../build.md)
- [材质与交互范围](material-baseline.md)
- [API 隔离审计](api-audit.md)
- [设备矩阵](device-matrix.md)
- [MiSans 许可核查](font-audit.md)
- [Figma 布局与差异](ui-alignment.md)、[原始资产清单](figma-assets.json)
- [已实现范围复核](review.md)、[验证记录](verification.json)、[候选清单](candidate-manifest.json)
- `runtime-candidate-2/test_b02_*.json` / `.png`：当前APK的实际检查及截图，逐包绑定hash。
- `candidate-1/`、`runtime/`：旧候选评审及原166条检查；`runtime-candidate-2-before-dark-fix/`：深色修正前的238条检查、36张代表截图及菜单失败历史。均不代表当前包通过。

用户已同意按官方许可接入原始字体及“本应用使用 MiSans 字体”署名。21份字体已审计，工程仅包原始VF、完整官方PDF、版权与可读协议；字体没有修改或子集化。

本候选运行、目视和独立总检以当前[验证记录](verification.json)为准。vivo Android12型号及真机安装证据仍未取得；中文IME、全部状态矩阵、罕见字回退和性能仍待验证。整批为`in_progress`，未完成整批G1/G2/G3，不计入已接受的App实现进度；不自动推进B03。独立SDK/AVD和失败日志保留供复测。
