# 公共食谱、食材与混合目录契约

状态：已通过B01用户批次复核；本文件定义数据格式，不代表公共源已部署。原始 `data/reference` 保持只读。

## 格式与引用

所有 schema 使用 JSON Schema Draft 2020-12。`https://yuno-recipe.invalid/schemas/` 仅是离线标识，不是联网入口；检查器必须从本地注册 schema，并禁止因缺失引用自动访问网络。启用 `date`、`date-time`、`uri` 格式检查，拒绝重复 JSON 键和 NaN/Infinity。浮点倍数检查使用十进制定点/精确十进制，不能因二进制浮点误差误报 `0.07` 不满足 `multipleOf=0.01`。

| 文件/入口 | 适用范围 |
|---|---|
| [common.schema.json](../../schemas/common.schema.json) | `$defs/id`、`revision`、`contentHash`、`dateTime`（`timestamp` 同义引用）、`localDate`、`safeRelativePath`、`nutrients`、`totals`、`foodState`、`healthWeight`、`sourceRef`、`license` |
| [recipe.schema.json](../../schemas/recipe.schema.json) 根 | 导入识别：旧 v2 与新 canonical profile |
| `recipe.schema.json#/$defs/canonical` | 新规范食谱及公共目录引用的食谱 |
| `recipe.schema.json#/$defs/legacy` | 当前 13 份参考 JSON 的兼容识别，仅进入迁移暂存 |
| [ingredient.schema.json](../../schemas/ingredient.schema.json) 根 | 独立食材 v1；不能把 Recipe.items 当独立食材发布 |
| [catalog.schema.json](../../schemas/catalog.schema.json) 根 | v1 混合目录、逐项摘要/版本/hash/路径及显式删除 |

ID 使用英文、数字、下划线和横线，长度 1–128。库记录身份为 `(originNamespace, libraryEntryId)`；正文的id、显示名称、revision和contentHash分别表示正文标识、名称、修订和字节内容，不代替库记录身份。originNamespace是稳定逻辑库标识，切换OSS/GitHub/Gitee镜像不改变它。revision不按字符串大小或设备时间比较新旧。

## 新规范与旧数据兼容

Recipe 保持 `schemaVersion=2`。新规范额外要求 `profile=canonical-v1` 与 `kind=recipe`，并提供 itemId、foodState、sourceRef、revision、分类、图片路径或 null、发布时间、是否含主食及许可核验信息。旧 v2 不具备这些字段，通过 legacy 分支仅说明可识别，不能绕过迁移预览或直接成为公共发布记录。新规范验证失败的对象不能通过删掉一个字段自动降级为 legacy：legacy 不允许 canonical 字段混入。

旧文件的无时区 generatedAt 原样保留为来源信息，不推断 UTC 或本地时区，更不冒充 publishedAt。缺失来源状态保留未知；迁移只能提出差异、待核实项和稳定 ID 映射，不能猜测生熟、许可、营养、含主食与生成时间。实际迁移实现与原件 hash/diff 属 B03。

`serving` 为正数，可为 0.5。来源配方总重从 100g 起步，通过语义校验约束；这与配餐至少 1g 的保存门槛无关。`totals.weight` 表示当前计量状态食材之和，不表示烹饪后的出餐重量。`targets` 仅是原配方制作参考，不可作为个人营养目标。

## 独立食材与营养

Ingredient 使用 `schemaVersion=1`、`kind=ingredient`、`profile=canonical-v1`。`nutritionBasisWeight=100` 表示 per100 的营养基准；`defaultPortionWeight=100` 表示用户已经确认的首次加入重量。两字段含义独立，不能因都为 100 而省略份量来源。加入后的快照保存当时定义、原始份量与当前份数，后续调整不回写公共定义。

`nutrients` 必须显式提供 energy/carb/protein/fat/vitaminC/fiber/sodium 七项，每项为非负数或 null。energy 单位 kcal；carb/protein/fat/fiber 单位 g；vitaminC/sodium 单位 mg。`null` 为未知，不转为 0；在语义计算中，任何正重量明细的某项营养未知，该项合计也为未知。0g 明细不制造未知贡献，规则由 B03 验证。

`foodState=unknown` 和 `verification=unverified` 可表达未核实事实，不能假装核实通过。sourceRef 记录 id、title、url、locator 与 verification，支持网页或书刊定位；license 单独记录 identifier/url/attribution/verification。verified 必须具有结构上非空的证明定位，但 schema 不证明来源内容真实或使用许可合法，发布时仍须审阅证据。

Recipe.items 的 `weight`、`per100`、`foodState`、边界必须同口径。`healthWeight` 为 [0.01,1] 且最多两位小数；locked 显式保留。默认 false 是解析器政策，schema 的 default 不是自动填值指令。首次规范化补默认时需记录迁移差异。

## 目录更新、删除与 hash

目录根为 `schemaVersion=1`、`kind=catalog`、revision、generatedAt、entries。每项显式 `kind=recipe|ingredient`；upsert带libraryEntryId/id/revision/contentHash/path/summary，delete也必须带libraryEntryId，精确作用于一条库记录。一个逻辑库内libraryEntryId唯一；名称、正文id、revision、contentHash均不设库记录唯一约束。库记录身份放在目录/本地元数据，不塞回被hash的正文，因此两份完全相同正文可有不同libraryEntryId，并各自显示、选择和删除。删除标记与正文更新分别处理，不因某条记录从目录缺席就推断删除。

`contentHash` 是下载全文文件原始 UTF-8 字节的 SHA-256 小写十六进制，位于目录，不嵌入被 hash 的正文，从而避免自引用。Recipe/Ingredient 正文不接受自带 contentHash。快照可从已验证目录保存 `sourceContentHash`；本地导入则保存原文件字节 hash。空白、换行与 BOM 变化也会改变 hash，下载后须先校验再解析/规范化，不能先重序列化再核对。SHA-256 仅验证内容一致，不提供来源身份认证。

已建立上传工具、显式发布计划及GitHub只读检查入口，见[公共食谱哈希与上传校验](../公共食谱哈希与上传校验.md)。生成与核验分开；同记录变更字节必须更新正文及目录revision，删除显式登记。提交前核对计划/目录/正文/引用图片的Git blob原字节；当前空bootstrap不代表正式内容通过，B03业务语义与App下载核验仍待实现。

必须计算并比对hash，不能因名称相同就认定文件重复。hash相同可说明该次内容核验一致，但不能据此合并、隐藏、删除任一独立库记录。即使正文id、revision和hash全相同，两条不同libraryEntryId仍独立；只有在配餐中重复选择同一库记录，才应用数量契约的xN。

path/image 使用安全相对路径：只允许 ASCII 字母、数字、横线、下划线、点与分隔斜线；每段首字符不能为点。禁止绝对地址、盘符、反斜线、`.`/`..` 段、百分号编码、查询和片段。路径以当前选择的公共源根地址解析；下载器仍须检查最终 URL/重定向、HTTPS、凭据和目录范围，不能只因通过正则就信任远端。

逐项先暂存全文，校验类型/版本/库记录身份/正文ID/revision/hash/摘要/结构和语义，再在事务内替换该libraryEntryId的当前正文及摘要。成功后库中直接使用新版，不提供旧版本记录列表；失败保留仍有效的当前正文和摘要，记录partial。不能把另一独立条目覆盖掉；appliedRevision逐条保存，不能仅凭库revision声称全部最新。删除也只针对指定库记录。用户已明确同一Recipe/Ingredient的更新自动传播至已保存配餐及活动草稿，替换来源快照并重算营养，不提供新旧分条或旧版浏览。库提交成功不等于全部配餐已更新：按完整库身份索引建立可恢复更新任务，逐记录提交并记录应用版本；未完成项不得标为最新。具体一致性、D13保留实际总重和D14上下限自动调整见数量及仓储契约。

## Schema 之外必须执行的语义校验

1. 拒绝非有限数、重复键、超出实现数值范围的数据；JSON Schema 的 number 本身没有指定计算精度。
2. itemId在配方内唯一；同逻辑库libraryEntryId唯一，sourceRef引用身份一致；名称/正文id/hash相同不是拒绝独立记录的理由。
3. `minWeight <= 原始weight <= maxWeight`，缺省边界按已确认算法解析；locked 保持原克数。来源总重至少 100g。
4. totals 与 per100×weight/100 的重算一致，未知传播、单位与舍入容差遵守计算契约；macroRatio 必须能由完整营养重算，否则为 null。
5. 目录与全文的 kind/id/revision、摘要、图片和时间一致；全文必须走 canonical 分支，legacy 不得用于发布。
6. 相对路径、最终 HTTPS 地址、下载/解压资源限制与重定向边界；部分导入逐条错误与原子提交按导入契约实施。
7. 来源、计量状态与素材许可核实。unknown/unverified 数据可保留在迁移预览，但不得在发布审阅中标为已核验。
8. 配餐按稳定库记录身份识别重复添加；不同库记录即使hash相同也不合并。Recipe/Ingredient更新自动替换已有配餐/草稿的对应快照并重算；按完整库身份更新，不按名称/hash扩展到别的记录。更新以D13已确认的当前已接受实际总重为目标，D14上下限自动调整已确认，不能由目录格式代替决定。

本批次仅提供机器 schema 与交接政策；算术、迁移器、数据库、OSS、下载器和 Android 运行尚未实现或验证。结构验证通过不等于任何营养或许可结论。

2026-10-30：Ingredient新版也按完整库身份自动维护已有配餐及草稿，直接引用按新版per100线性重算，不按名称改写Recipe内嵌食材。显式delete只下架库项，引用保留最后快照、重量、营养及条目下架证据；详情顶部提醒。首版libraryImport仅开发者测试，暂不可删除，不能绕过正式公共来源管理。
