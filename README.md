# 于の食谱

面向公众的 Android 食谱与配餐应用，使用 Kotlin、Jetpack Compose 和 Miuix。由 AI Agent 完成设计与开发，首版 App 不接入 AI。

**当前阶段：开发前检查与需求基线。尚无 Android 工程、可安装 APK 或已通过的真机兼容结论。**

## 从这里开始

- [开发前检查与待确认](docs/开发前检查与待确认.md)：检查结果、缺口、开工和发布条件。
- [Android 兼容与验证方案](docs/Android兼容与验证方案.md)：Android 12 简化材质、单 APK 策略和验收矩阵。
- [完整方案](docs/于の食谱-完整方案.md)、[UX](docs/于の食谱%20UX.md)、[接口与字段](docs/接口与字段清单.md)、[实施任务](docs/任务清单.md)。
- [UI 设计要求](docs/UI设计稿需求.md)、[视觉与动效](docs/附录A-视觉与动效设计.md)、[Miuix 基线](docs/Miuix-UI与液态玻璃基线.md)。
- [UX 与 UI 开发交接](docs/ux/README.md)、[P0～P3 实施计划](docs/planning/P0-P3实施计划.md)、[项目规则](AGENTS.md)、[机器任务计划](config/project-plan.json)。
- [Figma](https://www.figma.com/design/gdAAv31ho4RNFgANaMOJl0/)；[Miuix 示例](https://compose-miuix-ui.github.io/miuix-jsCanvas/)；[Miuix 仓库](https://github.com/compose-miuix-ui/miuix)。

## 目录与检查

本目录 `F:\Yuno-Develop\YUNO-recipe-app` 是后续工程、文档和资源的主目录。旧目录 `F:\Yuno-Develop\餐谱\YUNO-recipe` 保留原件与归档，后续修改集中在本目录；未复制旧目录中的凭据和 Git 元数据。

`data/reference` 是原始参考数据，含重复文件和待核实字段，不能直接作为发布数据。`assets` 是现有品牌、图标和占位素材，Android 图标适配及授权清单尚待完成。

只读检查（写入报告，不修改输入数据）：

```powershell
python scripts/check_recipe_preflight.py --source data/reference/recipes --output-dir reports/preflight-2026-10-28
powershell -NoProfile -File scripts/check_android_environment.ps1
```

检查报告位于 `reports/preflight-2026-10-28`。食谱脚本仅检查指定结构和算术，不代替营养来源审核或正式 schema 校验器。

首版简体中文，个人配餐本地保存，仅访问公共食谱源及用户主动配置的 WebDAV，不接入统计或广告 SDK。计划通过 GitHub/Gitee 分发 APK，先验证一个 APK 自动选择材质。

现有 [LICENSE](LICENSE) 保留；软件、食谱与第三方素材的许可在正式发布前复核。
