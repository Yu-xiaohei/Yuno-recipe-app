# MiSans 接入核查

当前候选 `B02-candidate-3`，2026-10-30；字体与许可沿用candidate-2原件，字节在本轮两包重新核对。用户已同意按官方许可集成原始字体，并确认在现有“开源与许可”入口显示“本应用使用 MiSans 字体”。

官方 ZIP 的 21 份字体已审计内部名称、版本、OS/2、fvar、cmap 和原字节 SHA-256，详见 [font-assets.json](font-assets.json)。工程仅打包原始 `MiSans VF 4.009`，未修改、子集化或全局安装字体。Compose 的 Normal/Medium/SemiBold/Bold 分别显式映射原始 VF 轴值 330/380/520/630，不把常用的 400/500/600/700 当成该字体的真实轴值。

ZIP 没有随附协议。字体审计 Agent 和总负责人已阅读官方四页 PDF；完整协议和版权声明随 APK 保留，原件见 [官方协议](../../../third_party/misans/MiSans_Fonts_License.pdf)。授权范围、保留协议和署名、禁止字体改编及单独分发、终止、免责和法律管辖均以该原件为准，不用网页摘要代替完整协议。

应用中的可读协议从原 PDF 提取，统一兼容字符后，另将五处 `⺠/⻄/⻛` 部首替换为原视觉对应的“民/西/风”，防止提取编码引入缺字；原 PDF 没有改变，协议内容没有增删。App Kotlin/XML 与中文日期展开的 292 个去重可见非空白码点全部覆盖；许可修正后的合并覆盖结果见 JSON。没有声称覆盖所有语言、罕见汉字或系统输入法。

14 个 Miuix 文字角色共用一个字体家族。标志中的字形保留 Figma 原始 SVG，属于图形资产。实际 Android 字体日志、署名入口和亮暗/大字截图由本候选重新验证，不能复用 candidate-1 的系统字体截图。vivo 和罕见字回退体验仍待人工验证。

来源：

- <https://hyperos.mi.com/font/zh/download/>
- <https://hyperos.mi.com/font/_next/static/chunks/pages/%5Blocale%5D/download-ef48df2bc9f157b4.js>
- <https://hyperos.mi.com/font-download/MiSans.zip>
- <https://hyperos.mi.com/font-download/MiSans字体知识产权许可协议.pdf>
