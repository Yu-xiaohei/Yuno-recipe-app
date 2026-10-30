# P0-06 执行者自检

日期：2026-10-28；候选：`B01-ui-1`；所有者：`p0_ui_baseline`。交付文件为 [UI 与字体工程契约](../../contracts/ui-baseline.md)，此文件是长期复核材料，不是临时产物。

## 范围与证据

- 只新增 `docs/contracts/ui-baseline.md` 和本文件；没有修改 UX JSON、规则、台账、日志、素材、Git 或 Android 工程。
- 先读项目 AGENTS、UX README、Miuix 基线、Android 兼容方案及问题复盘；保留既有产品行为和新增名称由用户决定的规则。
- GitHub tag API 回读 `v0.9.4` 的对象类型为 commit，SHA 为 `39c40f99844227b853f0049a0933b1f3ae6c00ba`。
- 当次读取固定提交的主题、字阶、Scaffold、导航、搜索、TextField、Slider、Card、BasicComponent、按钮、开关、TabRow、进度、弹层、设置行及导航预设源码。文档只列真实入口与明确标识为片段的关键参数。
- 当次读取 MiSans 官方首页、下载入口和 FAQ；官方 FAQ 的嵌入与注明要求已记录。未下载字体，不虚构许可证文件、字体版本、hash 或设备覆盖结论。
- 覆盖机器 UX 的全部 33 个组件角色；业务组合与上游 API 分开，现有 `upstreamApi=null` 不被提前改成已构建。
- 本地 PowerShell 内联检查已执行：两份交付均能按严格 UTF-8 解码、无替换字符、Markdown 围栏成对、本地相对链接存在；机器 UX 的 33 个角色 ID 均被覆盖。结果 `PASS`。`git diff --check -- docs/contracts/ui-baseline.md docs/reviews/B01/ui-self-check.md` 无错误；新文件仍未暂存，此命令不能代替对新文件的上述独立内容检查。总负责人需在固定候选上回读并纳入总检。

## 发现与处置

1. `InputField` 的 String 参数不能向外暴露 IME composition。已在契约指定保留组合态的输入适配，并要求后续中文 IME 实测；没有修改上游源码或宣称运行通过。
2. `Slider` 源码要求范围起点严格小于终点。已明确单值可达范围使用禁用交互的结果显示，不向组件传入相等端点；domain 不改变用户确认的重量和无效态规则。
3. `MiuixTheme` 没有已核实的 `fontFamily` 参数。已明确用 `TextStyles` 全 14 个角色注入统一字体，避免后续 Agent 编造参数或只覆盖正文。

上述属于设计阶段提前识别的接入风险，尚未发生 App 运行缺陷。根负责人根据项目记录规则决定与其他问题合并登记；执行者不越权写总日志或复盘。

## 未运行项与回退

- 没有初始化工程、编译 Kotlin、解析 AAR 依赖、安装 APK、启动模拟器或连接 vivo；相应结果均为 `not_run`。
- 字体包、具体条款、文件元数据、字符覆盖、Compose 运行与回退均未执行，D10 不得标为全部解决。
- 没有改 Figma，没有引入新依赖、用户可见名称或对外发送操作。
- 如总检退回，保留当前交付，由当前所有者按明确范围修订并重做受影响自检；本文不授权 B02，也不标记 G2/G3 通过。
