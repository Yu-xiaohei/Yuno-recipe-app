# Agent 测试与临时文件索引

更新日期：2026-10-31。`test_` 为长期复用测试，不能作为自动删除候选；`tmp_` 清理前仍需核实归属、引用和绝对路径。B02 保留正式设备证据及被忽略的独立 SDK/AVD、工具和构建日志，见下表。

| 相对路径 | 类型 / 用途 | 使用方法 | 保留或清理条件 |
|---|---|---|---|
| `tests/test_contract_schema.py` | 正式契约回归；Schema、离线引用、格式、缺失值、无效草稿、部分导入结构和关卡证据 | `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py" -v` | B01及后续契约持续复用；规则变更同步用例，不为通过检查删断言 |
| `tests/test_contract_samples.json` | 正式合成夹具；非公共食谱，数值、hash均不作真实性证明 | 测试脚本自动读取 | 跟随契约保留，不发布进APK或公共食谱源 |
| `tests/test_contract_deps/requirements.txt` | 测试依赖版本；含必需格式检查器 | `python -m venv .venv`，再 `.venv/Scripts/python.exe -m pip install -r tests/test_contract_deps/requirements.txt` | 工具固定名称requirements.txt置于test_目录，保留以便重建 |

项目 `.venv/` 是被忽略的工具管理环境，不是交付物或测试源码；没有修改系统 Python 或全局 Java 配置。重复 JSON 键、非有限数和十进制解析的辅助函数目前只服务上述测试，不代表 B03 生产校验器已经实现。

2026-10-29：最低有效重量改为1g，原10g边界方法已更名为`test_subgram_drafts_survive_but_saved_records_are_rejected`；用0/0.1/0.9/0.999g拒绝及1/9/10g接受替换旧预期，另增独立库身份/相同hash和六处正式重量字段检查。新增旧预检工具同ID同hash/异hash非删除审计测试，当前共28项结构与工具测试，不代表生产聚合或UI已实现。

2026-10-30：新增正式测试test_withdrawn_source_evidence_survives_drafts_backup_and_sync，覆盖Recipe/Ingredient条目下架证据的正式记录/草稿/严格备份/同步结构与缺失、非法、敏感字段拒绝；共29项。仅结构回归，不证明实际保存、传输或横幅运行。未保留临时文件。
2026-10-30发布哈希补充：新增`tests/test_catalog_integrity.py`（正式测试，22项），使用上述unittest discover命令或`python -m unittest discover -s tests -p "test_catalog_integrity.py" -v`；覆盖原始字节、独立身份、删除/revision、路径、原子写入和Git沙箱。与原29项合计51项，持续保留复用。沙箱在`.agent-tmp/b01_hash/`以带时间戳`tmp_b01_hash_tests_`命名并自动清理；工具原子写入的`tmp_catalog_integrity_write_<YYYYMMDD_HHmmss>_<ID>.json`正常退出时清理，异常遗留先核实不能直接发布。

| 相对路径 | 类型 / 用途 | 使用方法 | 保留或清理条件 |
|---|---|---|---|
| `.agent-tmp/b01_hash/tmp_b01_pre_hash_snapshot_20261030_014803.zip` | 临时恢复快照，保存哈希补充前candidate-6的49个文件及原manifest；不提交Git | 用ZIP工具只读查看，恢复时先比较当前改动归属 | 两远端回读且交接完成后再核实清理；不自动删除 |
| `.agent-tmp/b01_sync/tmp_b01_sync_github_checkout_20261030_130033/` | 临时GitHub独立检出；58份清单绑定hash及HEAD公共目录核验已通过 | 在此目录用项目`.venv/Scripts/python.exe`运行`scripts/catalog_integrity.py verify --git-mode head --baseline-ref HEAD^`；Git/工程固定名称因独立检出保留，统一置于tmp_目录 | 自动审批拒绝本次递归清理，仅返回策略拦截，现保留；后续核实限制、路径及用途后再处理，不绕过拒绝或自动删除 |

## B02

| 相对路径 | 类型 / 用途 | 使用方法 | 保留或清理条件 |
|---|---|---|---|
| `tests/test_android_smoke.py` | 正式、显式调用的模拟器交互/材质回归；unittest discovery 不触碰设备 | 参数及命令见 `docs/build.md`；只允许隔离原型包及模拟器 | 随 B02 及兼容方案复用；驱动变化不改变业务预期 |
| `tests/test_android_visual.py` | 正式代表页面亮暗/字号捕获；核对设备已安装APK hash，退出恢复设置 | 显式参数同smoke，先安装相同变体；见`docs/build.md` | 截图待人工核对，不能自动当作视觉通过；持续保留 |
| `docs/reviews/B02/runtime/test_b02_*` | 正式设备 JSON、原始截图、失败前证据及 XML；文件名说明 API/变体/检查点 | 阅读 JSON，并用图片查看器核对 PNG；带 `before_*_fix` 的报告是失败历史 | 长期保留，不能用后续成功覆盖早期失败；不进入 APK |
| `docs/reviews/B02/runtime-candidate-2/test_b02_*` | 新候选正式运行报告、Figma参照与原始设备截图 | 同上；只认各报告绑定的新APK hash | 长期保留；不替换旧候选证据 |
| `docs/reviews/B02/runtime-candidate-2-before-dark-fix/test_b02_*` | 深色层次修复前两包的238条检查及36张代表截图，含菜单失败历史 | 只读对比；不是当前APK通过证据 | 保留失败/修正链，不覆盖或自动删除 |
| `docs/reviews/B02/runtime-candidate-2/test_b02_visual_before_configuration_driver_fix/` | 配置切换截图失败及当时已取得视口 | 读取原JSON，失败精确系统原因未确定 | 保留失败链；后续成功不覆盖此目录 |
| `docs/reviews/B02/candidate-1/` | 旧候选只读评审与清单归档；工具/评审固定文件名 | 结合旧`runtime/`阅读，仅证明旧字体/布局 | 历史保留，不冒充当前通过 |
| `docs/reviews/B02/font-assets.json`、`figma-assets.json` | 正式资源审计与hash清单 | JSON阅读；结合font-audit/ui-alignment | 随资源更新重核；不是临时文件 |
| `reports/b02-environment-2026-10-30/android-environment.json` | 首次、安装工具前的环境快照；固定工具报告名 | JSON 只读查看；不冒充最终 SDK 清单 | 保留用于对比；不是当前全量环境 |
| `.agent-tmp/b02_toolchain/tmp_b02_cmdline_tools_20261030_133000.zip` 及同名目录 | Google 官方工具下载与解压；核验 SHA-1 后使用 | 工具固定入口位于 `cmdline-tools/bin/`，见构建文档 | B02 交接完成后核实引用再清理；尚被复测使用 |
| `.agent-tmp/b02_toolchain/tmp_b02_sdk_20261030_133000/` | 本项目独立 API37/BuildTools37、API31/32/33 镜像、emulator/platform-tools；工具管理固定文件名 | 被忽略的 `local.properties` 指向此目录；CLI 使用 `--sdk` 指定 | 未迁移 SDK 前不能清理；删除后必须重建并更新本机路径 |
| `.agent-tmp/b02_toolchain/tmp_b02_avds_20261030_135000/` | 三个专用 AVD，名称分别包含 `tmp_b02_api31/32/33_20261030_135000`；固定 config/镜像文件 | 仅在当前进程设置 `ANDROID_AVD_HOME`；不要修改用户已有 AVD | 先停止对应模拟器，确认无复测用途后再清理；非自动删除授权 |
| `.agent-tmp/b02_toolchain/tmp_b02_*.log` | SDK、AVD、模拟器、Gradle 和测试日志 | UTF-8 文本只读查看；最终日志由 B02 验证记录明确引用 | 保留至 B02 复核完成；失败日志不代表当前结果 |
| `.agent-tmp/b02_toolchain/tmp_b02_emulator_shutdown_20261030_173328.json` | 本轮API31/33专用模拟器归属及设置恢复记录 | 只读JSON；AVD名称核对后执行emu kill，最终设备清单另见verification.json | 保留至B02交接；不是删除SDK或AVD的授权 |
| `.agent-tmp/b02_font/tmp_b02_misans_package_20261030_144447.zip` | 官方原始字体ZIP | hash见font-assets；只读比对原字节 | 不提交Git；本候选复核完再核实清理 |
| `.agent-tmp/b02_font/tmp_b02_misans_metadata_20261030_145010.py` | 一次性SFNT元数据审计脚本 | 全局Python运行会重写font-assets，冻结后不能直接执行 | 留作审计方法，重跑前保留现有集成证据 |
| `.agent-tmp/b02_font/tmp_b02_misans_license_20261030_144725-*.png` | 官方四页许可渲染 | 图片查看器逐页阅读 | 许可复核后仍保留到交接；原件在third_party |
| `.agent-tmp/b02_revision/tmp_b02_candidate1_restore_20261030_150000.zip` | 修改前源码和两包恢复快照 | ZIP只读对比；恢复前核对归属 | 未授权自动删除，不进行整库reset |
| `.agent-tmp/b02_revision/tmp_b02_opaque_exports_20261030_153000/` | 原Figma不透明PNG导出 | 与SVG展示问题复盘对照；保留导出原件 | 不进APK，核实无用途后才清理 |
| `.agent-tmp/b02_revision/tmp_b02_before_coil_20261030_153000_*` | 依赖修改前lock/校验清单 | 与最终文件diff | B02复核及回退依据 |
| `.agent-tmp/b02_revision/tmp_b02_*.png` | 初次黑块、SVG修正、大字与菜单调查截图 | 图片查看器；正式最终截图以runtime-candidate-2为准 | 保留到复核，不当作最终通过 |
| `.agent-tmp/b02_revision/tmp_b02_handoff_20261030_163000.py` | 一次性证据整合脚本 | 全局Python带prepare/finalize/snapshot/close-review；前三者会重写候选，不在冻结后重跑；close-review只核验冻结文件并收尾管理记录 | 保留方法和最终命令；不进行Git/云操作 |

SDK 工具自动创建的 `.knownPackages`、Gradle/Python 缓存及构建产物属于工具管理文件；不为统一命名破坏工具运行。设备内的 `/data/local/tmp/tmp_b02_smoke_*.xml` 是上述正式驱动的临时导出，属于专用 AVD；模拟器不是用户真机。

## B02 candidate-3 修订与恢复登记

- `tests/test_android_navigation.py`：正式几何与选中状态设备回归；显式CLI，详见脚本--help；API31／33 R8已运行，每台六组；保留复用。
- `tests/test_android_glass.py`：正式同APK折射／仅模糊像素对照；显式CLI，需要`tests/test_android_deps/requirements.txt`固定Pillow12.3.0；API33 R8明暗已运行；不自动判定品牌相似度。
- `tests/test_android_glass_geometry.py`：正式纯边界回归，4项；`.venv/Scripts/python.exe -m unittest discover -s tests -p test_android_glass_geometry.py -v`，验证完整范围、正数半像素取整及拒绝不一致布局；保留复用。
- `docs/reviews/B02/candidate-2/`：原candidate-2根目录评审原字节归档，历史相对链接保留旧上下文，不作为当前候选。
- `docs/reviews/B02/runtime-candidate-3-before-width-refinement/test_b02_*`：原栏宽恢复前的两组release报告和截图，仅历史证据，保留不覆盖。
- `.agent-tmp/b02_glass/tmp_b02_*`：本轮恢复ZIP、官方原始资料和固定上游源码、模拟器/构建/回归日志；用途和具体名称见`docs/reviews/B02/pause-checkpoint.md`，仅核实归属及引用后清理，不进入APK或Git。
- `docs/reviews/B02/pause-checkpoint.md`：正式暂停交接入口，恢复时先读，不是临时文件。
- `docs/reviews/B02/runtime-candidate-3/test_b02_*`：当前正式APK审计、逐变体运行、几何、折射像素对照、原始截图／XML／日志及设备恢复关闭记录。具体hash见当前manifest，长期保留，不进APK。
- `docs/reviews/B02/runtime-candidate-3/test_b02_api32_before_capture_diagnostics/`：API32首次采集失败的JSON和四张PNG，原字节归档；精确原因未确定，不能以复测通过覆盖，长期保留。
- `.agent-tmp/b02_glass/tmp_b02_candidate3_evidence_20261030_190000.py`：一次性本地取证／整合脚本；用全局Python显式传`audit`／`freeze`／`static`／`close-review`。前两者会重写候选记录，冻结后不能无条件重跑；`static`只读核对；`close-review`仅在收到绑定清单的独立结论后记录管理闸门，不改冻结输入。保留供复现方法，不提交Git。
- `.agent-tmp/b02_glass/tmp_b02_regression_resumed_20261030_190000.log`：恢复后51项回归的正式运行日志，21.358秒通过；与最终verification绑定。暂存于忽略目录，保留至交接。
- `.agent-tmp/b02_glass/tmp_b02_resume_api<API>_*`：恢复后专用模拟器启动日志，API31／32／33；工具自动输出，不改全局AVD或用户设备，复核归属后才能清理。
- `docs/reviews/B02/runtime-candidate-3/test_b02_api33_release_glass_reanalysis.json`：正式原图离线重算报告，绑定原JSON／PNG／九矩形日志及固定源码hash；只替代原裁剪ROI的像素指标，非新设备运行，长期保留。
- `.agent-tmp/b02_glass/tmp_b02_glass_reanalysis_20261030_230000.py`：一次性离线重算方法，用固定Pillow12.3.0的全局Python运行；不碰设备，拒绝覆盖现有报告，复现需另选明确输出，保留到交接。
- `.agent-tmp/b02_glass/tmp_b02_glass_geometry_tests_20261030_230000.log`：新4项纯边界回归日志，0.001秒通过；与最终verification绑定，保留到交接。

## 2026-10-31 收工与Git预览

- `docs/reviews/B02/git-closeout-2026-10-31/reviewed-gitattributes.txt`：Git收工前属性原件，绑定原candidate-3 `.gitattributes`哈希；只读归档，不能用新属性重算旧清单。
- 同目录`test_b02_*`：正式证据的原字节副本，来源、hash及读取方法见`evidence-locations.json`与收工总结；不进APK，长期保留。
- `.agent-tmp/b02_sync/tmp_b02_closeout_workspace_20261031_000000.zip`：收工准备前702个工作区可提交文件恢复快照，CRC通过；ZIP SHA-256 `f565f0a2fe39c2747c3502ae8d98be0b2b024722180125e3150b6b555fe49e70`。恢复前比较归属／diff，不自动解压覆盖，不提交Git。
- `.agent-tmp/b02_sync/tmp_b02_closeout_refs_20261031_000000.bundle`：收工前本地全部Git引用和可达历史备份；SHA-256 `cfed0c88735e0a01601fb2bdb55fad3efcd9b32cc79c304d8dbab4b117cb9b95`。用`git bundle verify`只读核验，恢复另行授权，不提交Git。
- `.agent-tmp/b02_sync/tmp_b02_closeout_index_20261031_000000.bin`：原空暂存状态的Git索引备份；仅用于核对，不直接覆盖仍在使用的索引，保留到双远端同步交接。
- `.agent-tmp/b02_sync/tmp_b02_remote_<github|gitee>_20261031_000000.json`：本次只读远端main回读；不含凭据，读取成功不代表推送权限通过，保留到交接。
- `.agent-tmp/b02_sync/tmp_b02_closeout_verify_20261031_000000.py`：一次性Git暂存字节核验；全局Python显式传`snapshot`首次生成／`verify`只读比对。核验候选别名、正式证据、JSON／UTF-8、凭据模式、APK排除及两远端祖先，不提交、不推送。快照后不能随意重跑生成来掩盖差异，保留到交接。
- `.agent-tmp/b02_sync/tmp_b02_stage_checkout_20261031_000000/`：Git实际暂存索引导出，用于回读检出后原字节及中文路径；固定源码文件名整体置于tmp_目录。不是新工程，不运行应用；核验后保留到同步交接，未经核实不自动删除。
- `docs/reviews/B02/git-closeout-2026-10-31/test_b02_staged_whitespace.json`：正式Git格式检查原件例外清单，19条精确路径／hash；不能解释为全量格式通过，保留至交接及后续复用。
- 同目录`test_b02_whitespace_diagnostics.json`：两次原始格式诊断的Base64无损归档；用`base64.b64decode`解码对应记录并核对SHA-256后读取，保留原始失败证据，不进APK。
- 同目录`test_b02_catalog_staged_output.txt`：本次公共目录暂存字节核验原始输出；当前0条目录记录，不代表营养／许可审核通过，长期保留。
- `.agent-tmp/b02_sync/tmp_b02_whitespace_diagnostics_20261031_000000.txt`、`tmp_b02_whitespace_after_doc_format_20261031_000000.txt`及`tmp_b02_initial_whitespace_report_20261031_000000.json`：格式问题定位前后原始输出及首轮清单，正式无损副本已归档；用于复查，保留至Git同步交接，不自动清理。
- `.agent-tmp/b02_sync/tmp_b02_catalog_staged_20261031_000000.log`：公共目录暂存校验本地原始日志，正式副本已归档；保留至同步交接。
- `.agent-tmp/b02_sync/tmp_b02_final_index_20261031_000000.json`：最终暂存树与三个管理记录blob／SHA-256的本地回执；在最终核验时生成，避免把自身tree写入自身造成循环。先核对实际索引，不是提交或远端成功证明；保留至双远端同步交接。
