# Agent 测试与临时文件索引

更新日期：2026-10-30。`test_` 为长期复用测试，不能作为自动删除候选；`tmp_` 清理前仍需核实归属、引用和绝对路径。本轮没有保留临时脚本、下载样本或截图。

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
