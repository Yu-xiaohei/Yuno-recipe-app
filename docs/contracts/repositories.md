# 仓储与事务接口契约

候选：`B01-candidate-7`；任务 `P0-05`。这是语言无关的端口设计，未选择数据库、未实现 Kotlin 类或服务。正式冻结取决于 B01 三检。

## 公共约定

- 输入输出为有类型值或稳定 ID；UI 路由不携带完整快照、凭据或隐私。
- 写方法必须接收 `operationId` 实现幂等；编辑现有对象同时携带 `expectedRevision`。冲突返回当前候选引用，不按时钟静默覆盖。
- 错误使用内部类型 `InvalidInput / Missing / Locked / RevisionConflict / SlotOccupied / StorageFailure / UnsupportedVersion / CapabilityUnavailable`；新可见提示另行确认，不能直接把枚举放到界面。
- 观察流区分 `loading/content/empty/error` 与已有缓存；网络错误不清空本地内容。本地事务和同步完成是两种独立结果。
- Schema 做结构校验，语义层负责算术、相等键、日期餐次唯一、快照一致性、来源 hash、目标上下界及资源限制。Schema 通过不能直接授权落库。

## RecipeRepository

| 操作 | 输入 → 输出 | 写入和失败边界 |
|---|---|---|
| `observeCatalog` | kind、查询、筛选、排序、分页 → 本地目录视图 | 不要求联网；组合输入由 UI 守卫，不存无效搜索历史 |
| `readDefinition` | originNamespace、libraryEntryId、预期revision/hash → 该库记录当前定义及已核验源字节hash | 不以名称/正文ID/hash代替库身份；预期过期返回冲突，不提供旧版本列表 |
| `stageCatalogItem` | 当前源、目录项、下载字节 → 只读校验候选或逐项错误 | 验证HTTPS/路径/hash/类型/版本/摘要，不覆盖有效缓存 |
| `applyCatalogItem` | 已校验候选、expectedAppliedRevision → 提交结果 | 事务替换正文、摘要、应用版本并持久化引用更新任务；任务失败可恢复，不能据库成功声称配餐全量成功 |
| `applyPublicDeletion` | 已核验originNamespace、可信目录显式delete、libraryEntryId、预期版本 → 删除结果 | 按完整库身份下架并持久化引用维护任务；私人记录/草稿保留最后快照及数量营养，条件写入条目级下架证据和新revision/outbox；不级联删除 |
| `previewLibraryImport` | 开发者能力、原始字节和逐项类型 → 预览token | 首版仅开发者模式；普通入口、深链、文件kind分派及提交均校验能力。不发布公共OSS；测试来源命名空间独立，导入后暂不允许删除 |

同 `(originNamespace,libraryEntryId)` 的本地库记录唯一。正文ID、名称、revision和hash均不设跨库记录唯一约束；完全相同的两个文件记录也各自显示与选择。所有列表、详情、加入和删除端口传稳定库身份，不能只传recipeId/ingredientId。镜像地址变化不改变逻辑命名空间。

公共来源更新替换同一库记录的当前正文/摘要，不创建旧版列表。导入缺少库记录ID时，在预览为每个源索引分配独立libraryEntryId，并与预览token固定；同hash记录不自动去重。重复提交同operationId保持幂等，不能每次重试新增一套记录。导入不能变成云端删除指令；同一库身份的实际更新冲突须显式比较，具体可见选项按B09复核。

## MealRepository

| 操作 | 输入 → 输出 | 不变量 |
|---|---|---|
| `openContext` | LocalDate、mealSlotId → 已有记录/锁定信息/空上下文 | 日期不经UTC零点换算；有效记录唯一 |
| `openDraft` | 上下文、可选已有id和预期版本 → 草稿id与快照 | 已有锁定记录必须显式解锁；草稿独立持久化 |
| `updateDraft` | draftId、draftRevision、事件 → 新草稿或错误 | 可保存0≤重量<1g无效草稿；不自动变1g、不写正式记录 |
| `previewAdjustment` | 不可变原始快照、N、固定锚点、总量请求 → 计算预览 | 纯计算端口，取消无副作用；不反复缩放已舍入明细 |
| `commitDraft` | draftId、expectedRevision、operationId → 本地保存结果 | 至少一项且每项≥1g、语义校验通过；事务写记录、完整快照、revision、同步outbox和草稿消费状态 |
| `setLock` | id、expectedRevision、desiredLock、operationId → 新revision | 事务成功后呈最终状态；显式解锁不另触发来源升级；已确认的自动维护独立执行且保持锁定值 |
| `deleteMeal` | id、expectedRevision、operationId → tombstone | 删除活动索引并持久化删除标记/同步意图；不提前清队列 |
| `observeDate` | LocalDate → 当前有效记录列表 | 冲突副本不进入日期餐次的有效唯一索引 |

`commitDraft` 的事务同时检查 `(date,mealSlotId)` 和 `expectedRevision`；两个并发新建不能同时成功。不同ID占同一槽位返回SlotOccupied，不产生第二份有效记录。配餐条目保留来源命名空间及libraryEntryId；同一库记录在相同基准下重复添加按xN，两个独立库记录不因hash相同而合并。公共Recipe/Ingredient自动更新已保存配餐和正在编辑草稿的对应来源快照及派生营养；目标和餐次快照不变。D13已确认保留已接受actualWeight并按新版重算，不沿用旧请求或原锚点差值；D14已确认越界自动调整至新版有效上下限，不能否定正常自动传播。

当 WebDAV 未配置时，保存不依赖网络，也不创建已同步假象；用户以后开启某记录同步，才建立对应待同步任务。对既有启用同步的记录，保存与 outbox 必须原子一致。

## Recipe引用自动维护

`refreshRecipeReferences(originNamespace,libraryEntryId,targetRevision,targetHash,operationId)`按已验证Recipe版本查找关联记录，使用来源索引分页处理；不按名称/hash扫描合并其他库记录，不一次将全部记录载入内存。任务及每条结果持久化，重试同操作幂等。

对每份正式配餐，条件检查expectedMealRevision，在同一个记录事务中替换来源快照、源revision/hash/计算基准、调整明细、条目和整餐营养，生成新revision及同步意图；保留记录ID/日期/餐次/目标/份数/isLocked，不解锁、不生成第二份同餐记录。对草稿条件检查expectedDraftRevision，保留用户未保存的修改和无效编辑值，废弃旧计算预览并重算；不能因为源更新把草稿自动保存成正式记录。

源版本或私人编辑在计算过程中变化时，丢弃过期结果、重读并重新计算；只成功的记录标记该版本已应用。自动更新取当前已接受actualWeight，并按数量契约将超出新版有效范围的值自动调整到最近上下边界，再完整重算及条件提交；无需逐份确认。范围内求解失败、有效范围为空或提交失败保留上一致结果及待处理任务，不部分覆盖或伪造成功。旧requested不复活，未接受草稿预览与无效输入不被自动消费。

`refreshIngredientReferences`与Recipe维护使用相同完整库身份索引、revision、幂等、事务和outbox边界，但只对直接引用该Ingredient的条目按新版per100线性重算，保留实际克重；不改其他Recipe内嵌食材。锁定配餐可维护但锁定值保持。

显式公共删除产生可恢复的引用下架任务；每条条目保存`sourceAvailability={status:withdrawn, catalogRevision, deletionRevision, deletedAt, observedAt}`，绑定其已有完整库身份。保留的sourceRevision/hash/快照不变，删除证据单独保存；不存在该字段表示尚无确认下架事实，不表示已联网验证可用。字段随草稿、正式记录、同步和配餐备份保留。下架标记不是MealRecord.deletedAt，也不产生MealTombstone；同名/同hash独立记录不受影响。打开对应日期详情时按仍有下架条目显示顶部横幅，不以本次联网成功为条件，固定文案为“部分食谱已删除，已保留原有数据”（D19已确认）。

## GoalRepository、SettingsRepository

`readGoalProfile / previewAllocation / saveGoalProfile(expectedRevision)` 使用版本化目标、餐次稳定 ID 与日/餐范围；不配置任何默认营养值。三个初始餐次仅创建早餐、午餐、晚餐模板。停用保留历史，改名保持 ID。

`previewAllocation` 必须验证每餐最终有效目标；零权重产生非法的0指定值或零宽区间且无合法手动覆盖时，返回 `InvalidInput` 并保留原配置，不部分提交其余餐次。不能将 Schema 允许非负比例误读为所有比例组合都能完成分配。

`SettingsRepository` 仅保存轻量偏好、显示模式、搜索历史及非秘密连接信息。凭据只保存平台安全存储引用，不能放入 GoalProfile、导出或日志。`pruneSearchHistoryToLayout` 接收 UI 实测五行可容纳的最近历史 ID；应用不另造固定条数上限。

`clearRecipeCache` 仅清缓存，按云端权威重新读取；`requestMealClear` 是需要确认范围的删除工作流，事务生成本地与远端删除意图。不能调用“清数据库”顺便删除未完成 outbox、授权或冲突副本。实际清除账户、设备授权等其他含义未获授权，不在本操作内扩展。

## TransferRepository、SyncRepository

`inspectImport` 生成内容 hash 绑定的只读预览：每项有效性、冲突、排除原因、预期本地版本。`commitImport` 接收预览token、用户选择、operationId；文件或本地版本变化使token失效，重新预览。只对选择的有效条目执行一个本地事务；中途失败全部回滚，不回滚此前已有数据。

首版`mealBackup`保留正式用户入口；`libraryImport`仅开发者模式测试，预览和提交均重新校验开发者能力，关闭模式使已有库导入预览不可提交。系统文件/深链不能绕过能力检查。导入的测试库记录暂不允许删除；关闭开发者模式、清缓存不得作为变相删除。配餐备份内嵌Recipe/Ingredient快照仅恢复配餐，不能转为库记录或公共发布。

`createExport` 从一个一致性读取快照生成正式记录与可选目标配置；排除草稿、秘密、日志和内部同步配置。实际文档写出成功后才报告导出完成。

`SyncRepository` 管理待同步、共同基线、强ETag和独立冲突副本；能力探测通过前不无人值守覆盖。网络在数据库事务外执行，返回后再检查预期revision，防止把旧响应标记到新版本。详见 [同步政策](sync-policy.md)。

## 冻结与后续验证

端口命名为内部实现名称，不是新用户文案。B01仅冻结签名含义与错误/事务边界；Kotlin类型和实现由相应批次提供。B03数值/Schema语义测试、B04数据库故障/幂等/唯一性、B09导入回滚、B11双端冲突和真实服务能力都尚未运行。任何端口变更必须回查这些调用方及 UX ID。
