# Android 构建

B02 是离线、合成数据的兼容原型，不是正式食谱业务。工程与正式应用使用隔离包名，未连接 OSS、WebDAV 或统计 SDK。

## 固定工具链

| 项目 | 本次选择 |
|---|---|
| JDK | 21；本机 Temurin 21.0.9+10 |
| Gradle | 9.7.1；Wrapper JAR 与 ZIP 核对官方 SHA-256 |
| AGP | 9.4.1 |
| Kotlin / Compose compiler | 2.4.20 |
| Compose Multiplatform | 1.12.0 |
| Activity Compose | 1.13.0 |
| Miuix | 0.9.4，源码提交 `39c40f99844227b853f0049a0933b1f3ae6c00ba` |
| 本地图像/SVG | Coil 3.6.3；仅 compose/svg，不引入联网模块 |
| SDK / Build Tools | 稳定 API37.0 revision 2 / 37.0.0 |
| 原型 minSdk / targetSdk | 31 / 37；正式产品基线在 B02 人工接受后冻结 |

AGP 默认内建 KGP 2.2.10，顶层 buildscript 显式提高到 2.4.20，不再叠加 `org.jetbrains.kotlin.android`。此组合沿用固定 Miuix 源码；Kotlin 官方完全支持表不完整覆盖 AGP9.4.1/Gradle9.7.1，实际构建结果和限制以本批证据为准。Lint 的新版本提示不构成自动升级授权。

`gradle/libs.versions.toml` 固定直接版本，`app/gradle.lockfile` 固定已解析的应用依赖，`gradle/verification-metadata.xml` 对构建已用的依赖及元数据实行 SHA-256 校验。校验清单是首次从官方仓库解析后生成的信任起点，不是所有第三方内容均已做独立安全审计；Miuix 三份关键 AAR 另与先前审计 hash 比较。

## 本地配置

使用已有 JDK21，`scripts/android_gradle.ps1` 仅在子进程调整 `JAVA_HOME`，结束恢复；没有改变系统默认 JDK11。其他电脑可在当前 PowerShell 进程指定：

```powershell
$env:YUNO_JAVA_HOME = 'C:\path\to\jdk-21'
```

在被忽略的 `local.properties` 指定自己的 SDK。Windows 盘符冒号也必须转义：

```properties
sdk.dir=F\:/path/to/Android/Sdk
```

本次 SDK 位于 `.agent-tmp/b02_toolchain/tmp_b02_sdk_20261030_133000/`，与系统原 SDK 隔离。工具自动管理的目录/文件保留固定名称。SDK 使用现有已接受许可记录，由官方工具实际检查；没有向许可文件补写伪造接受记录。

本次官方 command-line-tools 23 的 `sdkmanager.bat` 已转发到 Android CLI，旧分号包路径调用未成功安装却返回 0，底层失败原因尚未完全定位。核实帮助后改用实际 CLI（关闭 metrics）：

```powershell
android.exe --no-metrics --sdk=<本地SDK绝对路径> sdk install platforms/android-37.0
android.exe --no-metrics --sdk=<本地SDK绝对路径> sdk install build-tools/37.0.0
```

安装后回读 `source.properties` / `package.xml`，不只依赖退出码。不要执行无范围的 update 或代用户接受新协议。

## 构建与现有检查

```powershell
./scripts/android_gradle.ps1 :app:assembleDebug :app:assembleRelease :app:lintDebug :app:lintRelease --dependency-verification=strict --no-daemon --console=plain
./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py" -v
```

`release` 在本原型中开启 R8 与资源压缩，**仅使用本机 debug 签名做兼容验证**，不是正式签名发行包。正式签名、版本与发布仍按 B12～B14 另行审核。

产物：

- `app/build/outputs/apk/debug/app-debug.apk`：包名 `com.yunobase.recipe.prototype.debug`。
- `app/build/outputs/apk/release/app-release.apk`：包名 `com.yunobase.recipe.prototype`，压缩候选。

两个产物均不提交 Git。生产拟定包名仍为 `com.yunobase.recipe`，本原型不占用该身份，不覆盖用户正式数据。不同 Android 版本验证使用同一份 debug APK、同一份压缩 APK，不按系统重新编译。

更新依赖需重新审阅版本、来源、校验清单及设备结果；普通构建不要加 `--write-verification-metadata` 来消除失配。

candidate-2 为读取原始 SVG 和限制大图解码加入 Coil 3.6.3，Apache-2.0 许可随包保留。其依赖解析使 profileinstaller 1.4.0 对齐到 1.4.1、coroutines-android 1.9.0 对齐到 1.10.2；不是整体升级工具链。新增依赖及这两处对齐均锁入 lockfile，并重新运行 strict 校验、Lint、R8 和低版本安装。原图不修改，缩略图请求尺寸为256×256；检查实际解码尺寸，不能仅凭 Image 的显示尺寸认定未加载大图。

## 设备检查

先启动独立的 API31/32/33 模拟器，再显式运行正式测试脚本：

```powershell
./.venv/Scripts/python.exe tests/test_android_smoke.py --adb <adb.exe路径> --serial emulator-5554 --api 31 --apk app/build/outputs/apk/debug/app-debug.apk --package com.yunobase.recipe.prototype.debug --variant debug --candidate B02-candidate-3 --output-dir docs/reviews/B02/runtime-candidate-3
```

脚本只允许隔离原型包及模拟器；不会在 unittest discovery 时启动设备，也不会清空全设备 logcat。它安装原型、验证冷启动、材质分支、导航、菜单、弹层、滑块/锁定、ASCII 键盘和减弱动画；API33 另做效果初始化及绘制异常注入。失败保留 JSON，不用修改预期掩盖问题。

`tests/test_android_visual.py` 使用相同显式参数，在已安装的同一 APK 上捕获亮暗×字号1.0/1.3/2.0的三个代表页面；不自动判定视觉通过，退出时恢复 AVD 字号与夜间偏好。当前捕获及目视结论见 B02 设备矩阵，不覆盖所有滚动位置、弹层、键盘和旋转状态。

中文 IME composition、vivo 真机、广泛 GPU 性能及正式升级仍须对应证据，不能用模拟器脚本通过代替。

candidate-3 为 `versionCode=2`、`versionName=0.0.2-b02`。SDK、包名、签名及既有依赖不变；Android12仍走清晰材质。原candidate-2及恢复ZIP保留，不能把它的运行报告当作当前版本通过。

几何与玻璃回归需要先安装同一变体的APK，再分别显式执行：

```powershell
python tests/test_android_navigation.py --adb <adb.exe路径> --serial emulator-5558 --api 33 --apk app/build/outputs/apk/release/app-release.apk --package com.yunobase.recipe.prototype --variant release --output-dir docs/reviews/B02/runtime-candidate-3
python -m pip install -r tests/test_android_deps/requirements.txt
python tests/test_android_glass.py --adb <adb.exe路径> --serial emulator-5558 --api 33 --apk app/build/outputs/apk/release/app-release.apk --package com.yunobase.recipe.prototype --variant release --output-dir docs/reviews/B02/runtime-candidate-3
```

`navigation`读取实际布局回调，测量三项等宽、图标／文字居中及真实选中状态，覆盖1.0／2.0字号。`glass`在同一APK中只切换折射，保持背景、主题、字号、几何和其他效果不变，比较排除图标文字的边缘像素。Intent校准入口不在产品导航中，不保存任何用户数据。它证明实际折射与单纯模糊有差异，不证明与Apple或某一HyperOS版本视觉一致。

玻璃驱动分别保存语义外框与按固定上游源码推导的完整表面边界；不能把被裁剪的语义外框当实际胶囊。当前原始截图的离线重算脚本与报告见`docs/agent-files.md`，原始报告未覆盖。`tests/test_android_glass_geometry.py`为4项纯边界回归，可用unittest discovery单独执行，无需设备或Pillow。

测试只操作专用B02模拟器；旧smoke／visual调用前由执行者核对AVD全名，结束后独立回读字号和夜间偏好。新geometry／glass驱动内含归属、安装字节核对及恢复回读。不同驱动不可同时操作同一设备，失败证据必须另存，不能覆盖后继续宣称全量通过。

## 一手依据

- AGP 9.4：<https://developer.android.com/build/releases/agp-9-4-0-release-notes>
- AGP 内建 Kotlin 升级：<https://developer.android.com/build/releases/agp-9-0-0-release-notes>
- Kotlin 兼容表：<https://kotlinlang.org/docs/gradle-configure-project.html>
- Gradle 9.7.1：<https://docs.gradle.org/9.7.1/userguide/compatibility.html>
- Google SDK 稳定清单：<https://dl.google.com/android/repository/repository2-3.xml>
- Miuix 固定源码：<https://github.com/compose-miuix-ui/miuix/tree/39c40f99844227b853f0049a0933b1f3ae6c00ba>
