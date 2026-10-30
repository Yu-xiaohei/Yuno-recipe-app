# B02 API 隔离审计

固定版本 0.9.4，提交 `39c40f99844227b853f0049a0933b1f3ae6c00ba`。基础 UI 依赖通过 squircle 传递 shader；blur 是独立依赖。正式 blur AAR minSdk33，ui/shader minSdk24，三者 minCompileSdk37。

本原型保留原 AAR 字节，Manifest 显式使用 `tools:overrideLibrary="top.yukonga.miuix.kmp.blur"`。它只是允许合并的受审计例外，不能独自证明 Android12 兼容。

## 隔离边界

1. 公共调用 `MaterialHost` 只暴露 Compose Modifier 和普通 lambda，先判断 SDK、硬件加速及用户减弱动画状态。
2. `EnhancedMaterial` 的类和方法标注 API33；入口 `@DoNotInline`，R8 显式保留增强类/生成类及 `LensKt`，避免跨边界内联。
3. `RuntimeShader` 构造位于增强对象方法，低版本没有顶层着色器对象或应用初始化器。普通 AndroidX 初始化器与 blur 初始化分开检查。
4. 真实 effects 初始化和绘制各有异常边界；发生可恢复异常后关闭增强路径，不把效果失败变成配餐业务前置条件。
5. 启动 intent 的 `b02.force_effect_failure` / `b02.force_draw_failure` 仅供隔离原型故障注入，不是正式产品配置或用户可见设置。

## 实际检查边界

合并 Manifest、Lint、传递依赖和 APK 内容须与同一候选一起核查。设备矩阵分别保存 debug 与 R8 候选 hash；同一变体在 API31/32/33 不重新打包。运行结果见 [设备矩阵](device-matrix.md)。

本项目没有更改 AAR minSdk、删除上游检测或 vendor 整个库。`Lens.kt` 的包名/内部可见性/API注解变更在原文件中显式标出，着色器原文不变；Apache 许可作为 `assets/miuix/LICENSE` 随包保留。

核心 AAR 原字节 SHA-256 与既有预检再次核对：

| AAR | SHA-256 |
|---|---|
| miuix-ui-android | `3d40628c043c3cf880029ffda689e1b123d9082b4bc8d2907e9437a42e2eb2a9` |
| miuix-shader-android | `a2febd9b7246db07b93cabc82afc26d1b5c1350e90e613fa9560cbff808cf787` |
| miuix-blur-android | `11b68beb90e7a2a6a2b86d4fd0a345c81ba42a3e2ef10bd013ff1c76112cf2f6` |

candidate-2 新增 Coil 3.6.3 本地 SVG/图片解码，无网络模块；锁与671个 artifact 校验记录重新核查。两包合并 Manifest 仍为 min31/target37、无 INTERNET。新增依赖后的低版本 debug/R8 证据以当前 [验证记录](verification.json) 为准，不能继承旧 APK 的运行结论。

字体另见 [字体核查](font-audit.md)；本审计不代表全部 GPU、vivo 真机或正式签名包通过。
