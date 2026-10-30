# B02 材质与交互

固定 Miuix 0.9.4；业务设计参考现有 UX，原型没有新增产品命名。三个 Tab 为配餐/食谱/设置，默认食谱；当前原型仅做内存状态切换，完整导航、持久化和草稿保护仍属 B04 及以后。

- API31/32：清晰表面、连续圆角和细边缘，保留 Miuix 控件动效；不使用截图模糊或 CPU 仿玻璃。
- API33：独立增强入口使用上游 `rememberLayerBackdrop` / `layerBackdrop` / `drawBackdrop`，采样真实 LazyColumn；前景不被录入背景，避免反馈。
- 透镜来自固定提交示例 `Lens.kt`，保留版权与适配声明；采用 `CircleShape`，符合其 `CornerBasedShape` 前提，不把任意 squircle 误当可折射形状。
- candidate-2 删除旧的右上“重量 300 g”测试胶囊，恢复 Figma 品牌日期、横向卡片和浮动导航；卡片重量仍是合成 fixture，不作为公共营养数据。
- 减弱动画使用 Compose `MotionDurationScale`，只读跟随系统时长配置；应用开关降为 0，并切换清晰材质。没有更改用户系统动画设置。
- 搜索保留 `TextFieldValue.composition`，仅提交有效输入筛选内存样例。中文拼音排序、真实搜索历史及查询仓储尚未实现。
- 菜单、弹层、滑块、Switch 使用实际 Miuix 组件；重量 200～400g 只验证控件，不冒充 B03 healthWeight 算法。

14 个主题文字角色已绑定原始 MiSans VF，许可、字重、字符覆盖和署名见 [字体核查](font-audit.md)。代表布局见 [Figma对照](ui-alignment.md)。字体和布局变更后重新构建两包，不用旧166条检查替代新运行证据；G3尚未通过。

Miuix Scaffold 保留根弹层宿主，OverlayListPopup/OverlayDialog 不脱离宿主运行。三个菜单均验证真实展开、选项及返回；分类中的“食材”另外验证弹层内滚动可达。B02选项禁用，不能把菜单展开当作目录筛选功能实现。

增强失败保护分为 API/硬件和 shader 探测、实际 effects 初始化异常、绘制异常三个边界。后两者清空当前效果并异步切回清晰材质；仅捕获 RuntimeException / LinkageError，不吞掉 OOM 等致命错误。故障注入验证的是这两个异常边界，不等于穷尽 GPU 驱动、性能或所有设备故障。
