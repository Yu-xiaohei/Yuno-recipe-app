package com.yunobase.recipe.design

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.yunobase.recipe.BuildConfig
import com.yunobase.recipe.R
import top.yukonga.miuix.kmp.basic.BasicComponent
import top.yukonga.miuix.kmp.basic.Card
import top.yukonga.miuix.kmp.basic.Switch
import top.yukonga.miuix.kmp.basic.Text
import top.yukonga.miuix.kmp.theme.MiuixTheme
import top.yukonga.miuix.kmp.utils.PressFeedbackType

/** Layout translated from Figma 157:695; values are offline synthetic fixtures, not user targets. */
@Composable
internal fun MealOverview(onOpenWeight: () -> Unit) {
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp).testTag("b02_meal_overview"),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Column(
            Modifier.fillMaxWidth().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(stringResource(R.string.today_meals), fontSize = 20.sp)
                    Text("全天营养信息一览", fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
                }
                FigmaAsset(
                    "calendar",
                    Modifier.background(MiuixTheme.colorScheme.surfaceContainerHigh, CircleShape)
                        .padding(8.dp).size(23.dp),
                    tint = MiuixTheme.colorScheme.onBackground,
                )
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Row(Modifier.weight(1f), verticalAlignment = Alignment.Bottom) {
                    Text("860", fontSize = 64.sp, lineHeight = 72.sp)
                    Text(" Kcal", fontSize = 30.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
                }
                FigmaAsset("energy", Modifier.size(40.dp))
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                FigmaAsset("weight", Modifier.size(40.dp))
                Spacer(Modifier.weight(1f))
                Text("820", fontSize = 64.sp, lineHeight = 72.sp)
                Text(" g", fontSize = 30.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
            }
            val nutrientColumns = if (LocalDensity.current.fontScale > 1.4f) 2 else 3
            BoxWithConstraints(Modifier.fillMaxWidth()) {
                val pillWidth = (maxWidth - 8.dp * (nutrientColumns - 1)) / nutrientColumns
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("protein", "fat", "carbs").forEach { image ->
                    Row(
                        Modifier.width(pillWidth).background(MiuixTheme.colorScheme.surfaceContainerHigh, CircleShape)
                            .padding(horizontal = 6.dp, vertical = 5.dp),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        FigmaAsset(image, Modifier.size(14.dp))
                        Text(" — / — g", fontSize = 12.sp, maxLines = 1, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
                    }
                }
                }
            }
        }
        MealFixtureCard("早餐", "351 Kcal    300 g", listOf("香菇木耳时蔬饭", "清炒小包菜", "魔芋紫菜汤"), Modifier.testTag("b02_meal_open"), onOpenWeight)
        MealFixtureCard("午餐", "509 Kcal    520 g", listOf("蛋炒饭", "凉拌芹菜", "魔芋紫菜汤"))
        MealFixtureCard("晚餐", "—", emptyList())
        Spacer(Modifier.height(140.dp))
    }
}

@Composable
private fun MealFixtureCard(
    title: String,
    summary: String,
    recipes: List<String>,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
) {
    Card(
        modifier.fillMaxWidth(), cornerRadius = 25.dp,
        insideMargin = PaddingValues(horizontal = 17.dp, vertical = 14.dp),
        pressFeedbackType = PressFeedbackType.Sink,
        onClick = onClick,
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(title, fontSize = 20.sp)
                Text(summary, fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
                if (recipes.isNotEmpty()) Text(recipes.joinToString(" | "), fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
            }
            FigmaAsset(
                "chevron", Modifier.width(10.dp).height(24.dp),
                tint = MiuixTheme.colorScheme.onSurfaceVariantActions,
            )
        }
    }
}

/** Figma 437:233 structure. Unimplemented services are disabled and never simulate successful writes. */
@Composable
internal fun SettingsOverview(
    reducedMotion: Boolean,
    onReducedMotionChange: (Boolean) -> Unit,
    onOpenLicenses: () -> Unit,
) {
    val motionLabel = stringResource(R.string.reduce_motion)
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).testTag("b02_settings_list")
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(stringResource(R.string.tab_settings), fontSize = 36.sp, modifier = Modifier.padding(top = 24.dp, start = 15.dp, bottom = 8.dp))
        SettingsGroup("食谱数据") {
            InactiveSetting("上次更新时间", value = "—")
            InactiveSetting("当前食谱版本", value = "—")
            InactiveSetting("食谱源", "食谱信息的云端拉取源", "—")
            InactiveSetting("更新频率", "自动更新食谱信息的频率", "—")
            InactiveSetting("更新食谱", "手动从云端更新食谱信息")
        }
        SettingsGroup("营养目标管理") {
            InactiveSetting("餐次分配比例", value = "2:4:4")
            InactiveSetting("总目标热量", value = "—")
            InactiveSetting("总目标重量", value = "—")
            InactiveSetting("总目标餐数", value = "3")
            InactiveSetting("调整营养目标")
        }
        SettingsGroup("备份与恢复") {
            InactiveSetting("配餐导出", "将配餐 JSON 数据导出至本地")
            InactiveSetting("配餐导入", "将兼容的 JSON 格式配餐数据导入应用")
            InactiveSetting("WebDAV 云同步", "配置 WebDAV 后即可自动备份")
        }
        SettingsGroup("通用") {
            InactiveSetting("深色模式", value = "跟随系统")
            InactiveSetting("省流模式", "开启后将停止加载食谱图片")
            InactiveSetting("清除缓存", "清除食谱图片等应用缓存")
            BasicComponent(
                title = motionLabel,
                endActions = {
                    Switch(
                        checked = reducedMotion,
                        onCheckedChange = onReducedMotionChange,
                        modifier = Modifier.testTag("b02_reduce_motion").semantics { contentDescription = motionLabel },
                    )
                },
            )
        }
        SettingsGroup("关于") {
            InactiveSetting("应用版本", value = BuildConfig.VERSION_NAME)
            InactiveSetting("检查更新")
            InactiveSetting("应用更新源", "检查更新的数据获取与下载源", "—")
            InactiveSetting("开源地址", "喜欢应用就为作者点个 Stars 吧 ~")
            BasicComponent(
                title = stringResource(R.string.licenses),
                summary = stringResource(R.string.font_attribution),
                onClick = onOpenLicenses,
                modifier = Modifier.testTag("b02_licenses_open"),
            )
        }
        Spacer(Modifier.height(140.dp))
    }
}

@Composable
private fun SettingsGroup(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
        Text(title, fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary, modifier = Modifier.padding(start = 17.dp))
        Card(Modifier.fillMaxWidth(), cornerRadius = 25.dp, content = content)
    }
}

@Composable
private fun InactiveSetting(title: String, summary: String? = null, value: String? = null) {
    BasicComponent(
        title = title, summary = summary, enabled = false,
        endActions = {
            if (value != null) Text(value, fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantActions)
        },
    )
}
