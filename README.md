# 于の食谱 · YUNO Recipe

> 营养餐谱阅读器 · Android 客户端 · 品牌：于の小窝 / YUNO BASE

[![platform](https://img.shields.io/badge/platform-Android%2010%2B-green)]()
[![kotlin](https://img.shields.io/badge/Kotlin-2.x-blue)]()
[![compose](https://img.shields.io/badge/UI-Jetpack%20Compose%20Material3-purple)]()
[![license](https://img.shields.io/badge/license-CC%20BY--NC--ND%204.0-orange)](LICENSE)

**于の食谱**是一款安卓端营养餐谱应用：内置餐谱可离线阅读，支持 GitHub / Gitee 双源同步更新，并按食材营养权重把整餐热量/重量调配到目标值。

---

## 功能特性

- **餐谱浏览** — 列表 + 模糊搜索（汉字子序列 / 全拼 / 首字母，≥3 字符触发）、分类筛选、标签、热量区间
- **营养详情** — 总览三卡、目标对照、供能比、食材明细（每 100g 参考 + 数据来源外链）
- **目标调配** — 设定目标总热量或总重量，系统按 `healthWeight`（0.01–1.00）自动缩放食材
- **份量缩放** — ×0.5 / ×1 / ×2 / 自定义人数，营养等比换算
- **双源更新** — 启动拉取 `version.json` 比对；菜谱静默更新，客户端更新需确认；自动模式按延迟优选 GitHub/Gitee
- **Liquid Glass UI** — Apple Liquid Glass 拟态：玻璃 Tab 栏、玻璃抽屉、全套过场与微动效
- **深色模式** — 跟随系统 / 始终亮 / 始终暗

## 技术栈

| 项 | 选型 |
|---|---|
| 语言 | Kotlin |
| UI | Jetpack Compose + Material 3 |
| 玻璃效果 | Kyant0/Backdrop · Haze · AGSL（API 33+） |
| minSdk / target | 29 (Android 10) / 35 |
| 架构 | 单模块 MVVM |
| 网络 | OkHttp + kotlinx.serialization |
| 本地 | DataStore + filesDir + assets |

## 目录结构

```
YUNO-recipe/
├── android/                 # Android Studio 工程
├── docs/                    # 完整方案、动效附录、skill 改造说明
├── scripts/                 # 餐谱 v1→v2 迁移等脚本
├── cloud/                   # 云端分发内容（version.json / recipes / app）
└── json/                    # 餐谱 JSON 数据源
```

## 快速开始

1. 用 Android Studio 打开 `android/`
2. 同步 Gradle（需 JDK 17）
3. 选择设备（Android 10+）运行，或 `Build APK`

## 数据协议

云端仓库布局（GitHub / Gitee 镜像同构）：

```
version.json          # 总版本：app + recipes
CHANGELOG.md          # 更新日志
app/*.apk             # 安装包
recipes/index.json    # 菜谱索引
recipes/*.json        # 餐谱数据（schema v2）
images/               # 菜谱图（预留）
```

餐谱 JSON 字段说明见 `docs/于の食谱-完整方案.md` §5。

## 仓库

- GitHub：<https://github.com/Yu-xiaohei/Yuno-recipe-app>
- Gitee：<https://gitee.com/Yu_xiaohei/yuno-recipe-app>

两个仓库结构镜像，客户端按延迟自动择优。

## 许可

本项目及餐谱数据基于 **CC BY-NC-ND 4.0** 协议授权。

> © 2024 - 2026 YUNO BASE  
> 未经作者允许，禁止商业用途的二次转载。

## 致谢

- 营养数据：《中国食物成分表》· 中国营养学会 · USDA FoodData Central
- 玻璃材质：[AndroidLiquidGlass (Backdrop)](https://github.com/Kyant0/AndroidLiquidGlass) · [Haze](https://github.com/chrisbanes/haze)
- 设计参考：Apple Human Interface Guidelines — Materials / Motion
