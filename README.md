# 于の食谱

面向公众的 Android 食谱与配餐应用，使用 Kotlin、Jetpack Compose 和 Miuix。由 AI Agent 完成设计与开发，首版 App 不接入 AI。

**当前阶段：B01共享契约及发布哈希工具补充已人工通过，Git同步等待第二次确认。后续批次最早2026-10-31且等待新开工指令；尚无Android工程、APK或真机兼容结论。**

当前数据规则：库记录独立，不按名称、正文ID或SHA-256自动去重；仅配餐重复加入同一库记录聚合xN。配餐条目最低有效总重1g，低于1g保留红框无效草稿并阻止保存；100g来源/营养口径和±100g滑块不变。

公共Recipe新版核验后自动替换该记录及已保存配餐、编辑草稿中的对应配方并重算营养，无需逐份确认；目标/餐次及锁定状态保留。D13已确认保留当前已接受的实际总重；D14上下限自动调整已确认；独立食材按新版每100g线性重算。公共下架保留配餐条目及最后数据，详情顶部提醒；普通用户库导入首版关闭，仅开发者测试且暂不能删。餐次使用Figma预设，默认三餐2:4:4。这些均为设计契约，尚无自动更新实现。

## 从这里开始

- [开发前检查与待确认](docs/开发前检查与待确认.md)：检查结果、缺口、开工和发布条件。
- [Android 兼容与验证方案](docs/Android兼容与验证方案.md)：Android 12 简化材质、单 APK 策略和验收矩阵。
- [完整方案](docs/于の食谱-完整方案.md)、[UX](docs/于の食谱%20UX.md)、[接口与字段](docs/接口与字段清单.md)、[实施任务](docs/任务清单.md)。
- [UI 设计要求](docs/UI设计稿需求.md)、[视觉与动效](docs/附录A-视觉与动效设计.md)、[Miuix 基线](docs/Miuix-UI与液态玻璃基线.md)。
- [UX 与 UI 开发交接](docs/ux/README.md)、[P0～P3 实施计划](docs/planning/P0-P3实施计划.md)、[项目规则](AGENTS.md)、[机器任务计划](config/project-plan.json)。
- [B01 契约与验证入口](docs/reviews/B01/README.md)、[数据契约](docs/contracts/catalog-data.md)、[仓储契约](docs/contracts/repositories.md)、[测试索引](docs/agent-files.md)。
- [公共食谱哈希与上传校验](docs/公共食谱哈希与上传校验.md)：发布计划、原始字节SHA-256生成、Git暂存/HEAD核验及CI入口。
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
