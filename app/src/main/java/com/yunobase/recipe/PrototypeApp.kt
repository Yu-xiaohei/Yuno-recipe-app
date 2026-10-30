package com.yunobase.recipe

import android.util.Log
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.boundsInRoot
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.yunobase.recipe.compat.MaterialHost
import com.yunobase.recipe.design.MealOverview
import com.yunobase.recipe.design.SettingsOverview
import com.yunobase.recipe.design.FigmaAsset
import com.yunobase.recipe.design.BrandWordmark
import coil3.compose.AsyncImage
import coil3.request.ImageRequest
import top.yukonga.miuix.kmp.basic.*
import top.yukonga.miuix.kmp.overlay.OverlayDialog
import top.yukonga.miuix.kmp.overlay.OverlayListPopup
import top.yukonga.miuix.kmp.theme.MiuixTheme
import top.yukonga.miuix.kmp.utils.PressFeedbackType
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.roundToInt

private const val MEALS = 0
private const val RECIPES = 1
private const val SETTINGS = 2

/** Offline B02 visual/compatibility fixture. No repository, targets, persistence or cloud writes. */
@OptIn(ExperimentalComposeUiApi::class)
@Composable
internal fun PrototypeApp(
    reducedMotion: Boolean,
    onReducedMotionChange: (Boolean) -> Unit,
    forceEffectFailure: Boolean = false,
    forceDrawFailure: Boolean = false,
    disableRefraction: Boolean = false,
    glassCalibration: Boolean = false,
) {
    var tab by rememberSaveable { mutableIntStateOf(RECIPES) }
    var searchExpanded by rememberSaveable { mutableStateOf(false) }
    var query by rememberSaveable(stateSaver = TextFieldValue.Saver) { mutableStateOf(TextFieldValue("")) }
    var submittedQuery by rememberSaveable { mutableStateOf("") }
    var showFilter by rememberSaveable { mutableIntStateOf(-1) }
    var showDialog by rememberSaveable { mutableStateOf(false) }
    var dialogTitle by rememberSaveable { mutableStateOf("") }
    var dialogSummary by rememberSaveable { mutableStateOf("") }
    var showWeight by rememberSaveable { mutableStateOf(false) }
    var showLicenses by rememberSaveable { mutableStateOf(false) }
    var locked by rememberSaveable { mutableStateOf(false) }
    var weight by rememberSaveable { mutableFloatStateOf(300f) }
    val listState = rememberLazyListState()
    val focusManager = LocalFocusManager.current
    val context = LocalContext.current
    val copyright = remember { context.assets.open("misans/COPYRIGHT.txt").bufferedReader().use { it.readText() } }
    val tabs = listOf(stringResource(R.string.tab_meals), stringResource(R.string.tab_recipes), stringResource(R.string.tab_settings))
    val icons = listOf("nav_meals", "nav_recipes", "nav_settings")
    val fixtures = remember { List(30) { fixtureRecipes[it % fixtureRecipes.size] } }
    val names = remember(submittedQuery) {
        fixtures.filter { submittedQuery.isEmpty() || it.name.contains(submittedQuery) }
    }
    val submit: () -> Unit = {
        val text = query.text.trim()
        if (query.composition == null && text.codePointCount(0, text.length) >= 2) {
            submittedQuery = text
            focusManager.clearFocus()
            Log.i("YunoB02", "fixture-search-submitted; composition=false")
        }
    }
    BackHandler(enabled = !showDialog && showFilter < 0 && !searchExpanded && (showWeight || showLicenses || tab != RECIPES)) {
        when {
            showLicenses -> showLicenses = false
            showWeight -> showWeight = false
            else -> tab = RECIPES
        }
    }

    // OverlayListPopup / OverlayDialog require Miuix's root popup host.
    // Insets are handled once by the content and FloatingNavigationBar below.
    Scaffold(
        modifier = Modifier.fillMaxSize().semantics { testTagsAsResourceId = true },
        containerColor = MiuixTheme.colorScheme.background,
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { _ ->
    MaterialHost(
        useEnhanced = !reducedMotion,
        forceEffectFailure = forceEffectFailure,
        forceDrawFailure = forceDrawFailure,
        disableRefraction = disableRefraction,
    ) { background, foreground ->
        Box(
            Modifier.fillMaxSize().background(MiuixTheme.colorScheme.background)
                .semantics { testTagsAsResourceId = true },
        ) {
            Column(
                Modifier.fillMaxSize().then(background)
                    .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top + WindowInsetsSides.Horizontal))
                    .imePadding(),
            ) {
                when {
                    glassCalibration -> GlassCalibration()
                    showLicenses -> Column(
                        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                    ) {
                        BackButton { showLicenses = false }
                        Text(stringResource(R.string.licenses), style = MiuixTheme.textStyles.title1)
                        Card(Modifier.fillMaxWidth(), cornerRadius = 25.dp, insideMargin = PaddingValues(17.dp)) {
                            Text(stringResource(R.string.font_attribution), modifier = Modifier.testTag("b02_font_attribution"))
                            Spacer(Modifier.height(12.dp))
                            Text(copyright, style = MiuixTheme.textStyles.footnote1)
                            Text("MiSans VF 4.009", style = MiuixTheme.textStyles.body2)
                        }
                        Text("MiSans 字体知识产权许可协议", style = MiuixTheme.textStyles.headline1)
                        Text(
                            remember { context.assets.open("misans/LICENSE_readable.txt").bufferedReader().use { it.readText() } },
                            style = MiuixTheme.textStyles.body2,
                        )
                        Spacer(Modifier.height(48.dp))
                    }
                    showWeight -> WeightFixture(weight, { weight = it }, locked, { locked = it }) { showWeight = false }
                    tab == RECIPES -> {
                        if (!searchExpanded) BrandHeader()
                        SearchBar(
                            expanded = searchExpanded,
                            insideMargin = DpSize(0.dp, 0.dp),
                            modifier = Modifier.padding(horizontal = 24.dp).padding(top = if (searchExpanded) 12.dp else 4.dp),
                            onExpandedChange = {
                                searchExpanded = it
                                if (!it) {
                                    submittedQuery = ""
                                    focusManager.clearFocus()
                                }
                            },
                            inputField = {
                                TextField(
                                    value = query,
                                    onValueChange = { query = it },
                                    label = stringResource(R.string.search_placeholder),
                                    useLabelAsPlaceholder = true,
                                    singleLine = true,
                                    cornerRadius = 50.dp,
                                    insideMargin = DpSize(14.dp, 10.dp),
                                    textStyle = MiuixTheme.textStyles.body1.copy(fontSize = 16.sp),
                                    colors = TextFieldDefaults.textFieldColors(
                                        backgroundColor = MiuixTheme.colorScheme.surfaceContainerHigh,
                                        labelColor = MiuixTheme.colorScheme.onSurfaceVariantSummary,
                                    ),
                                    leadingIcon = {
                                        FigmaAsset(
                                            "search",
                                            Modifier.padding(start = 14.dp, end = 8.dp).size(18.dp),
                                            tint = MiuixTheme.colorScheme.onSurfaceVariantSummary,
                                        )
                                    },
                                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                                    keyboardActions = KeyboardActions(onSearch = { submit() }),
                                    modifier = Modifier.fillMaxWidth().testTag("b02_search_input")
                                        .onFocusChanged { if (it.isFocused) searchExpanded = true },
                                )
                            },
                            outsideEndAction = {
                                TextButton(
                                    text = stringResource(R.string.cancel),
                                    onClick = {
                                        searchExpanded = false
                                        submittedQuery = ""
                                        focusManager.clearFocus()
                                    },
                                    modifier = Modifier.testTag("b02_search_close"),
                                )
                            },
                        ) {
                            TextButton(text = stringResource(R.string.search), onClick = submit, modifier = Modifier.testTag("b02_search_submit"))
                            if (query.text.trim().codePointCount(0, query.text.trim().length) < 2) {
                                Text(stringResource(R.string.search_minimum), style = MiuixTheme.textStyles.body2, modifier = Modifier.padding(vertical = 8.dp))
                            }
                        }
                        if (!searchExpanded) {
                            val filterColumns = if (LocalDensity.current.fontScale > 1.4f) 2 else 3
                            BoxWithConstraints(
                                Modifier.fillMaxWidth().padding(horizontal = 24.dp).padding(top = 12.dp, bottom = 16.dp),
                            ) {
                                val filterWidth = (maxWidth - 8.dp * (filterColumns - 1)) / filterColumns
                                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                listOf(R.string.weight_all, R.string.energy_all, R.string.category_all).forEachIndexed { index, label ->
                                    Box(Modifier.width(filterWidth)) {
                                        Card(
                                            modifier = Modifier.fillMaxWidth().heightIn(min = 40.dp)
                                                .testTag(if (index == 2) "b02_menu_open" else "b02_filter_$index"),
                                            cornerRadius = 50.dp,
                                            colors = CardDefaults.defaultColors(color = MiuixTheme.colorScheme.surfaceContainerHigh),
                                            onClick = { showFilter = index },
                                            pressFeedbackType = PressFeedbackType.Sink,
                                            insideMargin = PaddingValues(horizontal = 8.dp, vertical = 5.dp),
                                        ) {
                                            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center) {
                                                Text(stringResource(label), fontSize = 15.sp, maxLines = 1)
                                                FigmaAsset(
                                                    "filter_arrow", Modifier.size(24.dp),
                                                    tint = MiuixTheme.colorScheme.onBackground,
                                                )
                                            }
                                        }
                                        OverlayListPopup(
                                            show = showFilter == index,
                                            onDismissRequest = { showFilter = -1 },
                                            popupModifier = Modifier.testTag(if (index == 2) "b02_category_menu" else "b02_filter_menu_$index"),
                                        ) {
                                            ListPopupColumn {
                                                // Only opening/dismissal in B02; catalog filtering belongs to B04.
                                                filterOptions[index].forEach { text -> BasicComponent(title = text, enabled = false) }
                                            }
                                        }
                                    }
                                }
                                }
                            }
                        }
                        LazyColumn(
                            state = listState,
                            contentPadding = PaddingValues(start = 24.dp, end = 24.dp, top = if (searchExpanded) 12.dp else 0.dp, bottom = 140.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                            modifier = Modifier.fillMaxSize().testTag("b02_recipe_list"),
                        ) {
                            itemsIndexed(names, key = { index, _ -> "b02-fixture-$index" }) { index, recipe ->
                                RecipeCard(recipe, Modifier.testTag("b02_recipe_$index")) {
                                    dialogTitle = recipe.name
                                    dialogSummary = "${recipe.energy} Kcal    ${recipe.weight} g"
                                    showDialog = true
                                }
                            }
                        }
                    }
                    tab == MEALS -> {
                        BrandHeader()
                        MealOverview { showWeight = true }
                    }
                    else -> SettingsOverview(reducedMotion, onReducedMotionChange) { showLicenses = true }
                }
            }
            if (!searchExpanded && !showWeight && !showLicenses) {
                BoxWithConstraints(Modifier.align(Alignment.BottomCenter).fillMaxWidth()) {
                    // Preserve the previous three 78dp cells and two 12dp gaps.
                    val navigationWidth = (maxWidth - 64.dp).coerceAtMost(258.dp)
                    FloatingNavigationBar(
                        modifier = foreground.testTag("b02_material_surface"),
                        color = Color.Transparent,
                        cornerRadius = 50.dp,
                        shadowElevation = 0.dp,
                        defaultWindowInsetsPadding = false,
                    ) {
                        Row(Modifier.width(navigationWidth),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                        tabs.forEachIndexed { index, label ->
                            Card(
                                modifier = Modifier.weight(1f).recordNavGeometry("cell", index)
                                    .testTag("b02_tab_$index").semantics {
                                    selected = tab == index
                                    role = Role.Tab
                                },
                                cornerRadius = 50.dp,
                                colors = CardDefaults.defaultColors(
                                    color = if (tab == index) MiuixTheme.colorScheme.onBackground.copy(alpha = 0.08f) else Color.Transparent,
                                ),
                                insideMargin = PaddingValues(horizontal = 10.dp, vertical = 5.dp),
                                pressFeedbackType = PressFeedbackType.Sink,
                                onClick = { tab = index },
                            ) {
                                Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                                    FigmaAsset(
                                        icons[index], Modifier.size(24.dp).recordNavGeometry("icon", index),
                                        tint = MiuixTheme.colorScheme.onBackground,
                                    )
                                    Text(label, fontSize = 12.sp, lineHeight = 16.sp,
                                        modifier = Modifier.recordNavGeometry("label", index))
                                }
                            }
                        }
                        }
                    }
                }
            }
            OverlayDialog(
                show = showDialog,
                title = dialogTitle,
                onDismissRequest = { showDialog = false },
                modifier = Modifier.testTag("b02_dialog"),
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text(dialogSummary, style = MiuixTheme.textStyles.body1)
                    TextButton(text = stringResource(R.string.confirm), onClick = { showDialog = false }, modifier = Modifier.fillMaxWidth().testTag("b02_dialog_confirm"))
                }
            }
        }
    }
    }
}

/** Measured screen coordinates for the isolated prototype's geometry regression driver. */
private fun Modifier.recordNavGeometry(part: String, index: Int): Modifier =
    onGloballyPositioned { coordinates ->
        val bounds = coordinates.boundsInRoot()
        Log.i("YunoB02", "nav-geometry; part=$part; index=$index; left=${bounds.left}; top=${bounds.top}; right=${bounds.right}; bottom=${bounds.bottom}")
    }

/** Intent-only calibration, never reached through product navigation or saved to user data. */
@Composable
private fun GlassCalibration() {
    Canvas(Modifier.fillMaxSize().testTag("b02_glass_calibration")) {
        val step = 18.dp.toPx()
        val colors = listOf(Color(0xFF173B6B), Color(0xFFFFBD48), Color.White, Color(0xFF172535))
        for (column in 0..(size.width / step).toInt()) {
            for (row in 0..(size.height / step).toInt()) {
                drawRect(colors[(column + row) % colors.size],
                    topLeft = Offset(column * step, row * step), size = Size(step, step))
            }
        }
    }
}

@Composable
internal fun BrandHeader() {
    val today = LocalDate.now()
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 24.dp).padding(top = 6.dp, bottom = 12.dp).heightIn(min = 50.dp)
            .testTag("b02_brand_header"),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        FigmaAsset("brand_logo", Modifier.size(44.dp))
        Spacer(Modifier.width(8.dp))
        BrandWordmark(null, stringResource(R.string.app_name))
        Spacer(Modifier.weight(1f))
        Column(horizontalAlignment = Alignment.End) {
            Text(today.format(DateTimeFormatter.ofPattern("yyyy年M月d日", Locale.CHINA)), fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
            Text(today.format(DateTimeFormatter.ofPattern("EEEE", Locale.CHINA)), fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
        }
    }
}

private data class RecipeFixture(val name: String, val energy: Int, val weight: Int, val tags: List<String>, val image: Int)
private val fixtureRecipes = listOf(
    RecipeFixture("西红柿炒鸡蛋", 351, 350, listOf("热菜", "荤菜"), R.drawable.figma_recipe_tomato),
    RecipeFixture("凉拌西葫芦", 121, 150, listOf("凉菜", "素菜"), R.drawable.figma_recipe_placeholder),
    RecipeFixture("红烧肉", 506, 300, listOf("热菜", "荤菜"), R.drawable.figma_recipe_placeholder),
    RecipeFixture("香烤苹果", 197, 80, listOf("凉菜", "素菜"), R.drawable.figma_recipe_apple),
    RecipeFixture("蒜泥茄子", 120, 150, listOf("凉菜", "素菜"), R.drawable.figma_recipe_eggplant),
    RecipeFixture("清炒小白菜", 50, 200, listOf("热菜", "素菜"), R.drawable.figma_recipe_cabbage),
)

@Composable
private fun RecipeCard(recipe: RecipeFixture, modifier: Modifier, onClick: () -> Unit) {
    val context = LocalContext.current
    val request = remember(recipe.image) {
        ImageRequest.Builder(context).data(recipe.image).size(256, 256).build()
    }
    Card(
        modifier.fillMaxWidth(), cornerRadius = 25.dp,
        insideMargin = PaddingValues(horizontal = 17.dp, vertical = 11.dp),
        pressFeedbackType = PressFeedbackType.Sink, onClick = onClick,
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            AsyncImage(
                model = request, contentDescription = null,
                modifier = Modifier.size(78.dp).clip(RoundedCornerShape(10.dp)), contentScale = ContentScale.Crop,
                onSuccess = {
                    val image = it.result.image
                    Log.i("YunoB02", "thumbnail-decoded; width=${image.width}; height=${image.height}")
                },
                onError = { Log.e("YunoB02", "asset-error; thumbnail", it.result.throwable) },
            )
            Spacer(Modifier.width(16.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(recipe.name, fontSize = 17.sp, fontWeight = FontWeight.Medium)
                Text("${recipe.energy} Kcal    ${recipe.weight} g", fontSize = 14.sp, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    recipe.tags.forEach { tag ->
                        val base = when (tag) {
                            "热菜" -> Color(0xFFFF9D00)
                            "凉菜" -> Color(0xFF0095FF)
                            "荤菜" -> Color(0xFFFF0099)
                            else -> Color(0xFF009905)
                        }
                        val dark = MiuixTheme.colorScheme.background.luminance() < 0.5f
                        Text(
                            tag, fontSize = 11.sp, lineHeight = 15.sp,
                            color = if (dark) lerp(base, Color.White, 0.35f) else base,
                            modifier = Modifier.background(base.copy(alpha = 0.2f), RoundedCornerShape(4.dp))
                                .padding(horizontal = 5.dp, vertical = 1.dp),
                        )
                    }
                }
            }
            Spacer(Modifier.width(8.dp))
            FigmaAsset(
                "chevron", Modifier.width(10.dp).height(24.dp),
                tint = MiuixTheme.colorScheme.onSurfaceVariantActions,
            )
        }
    }
}

@Composable
internal fun BackButton(onClick: () -> Unit) {
    TextButton(text = stringResource(R.string.back), onClick = onClick, modifier = Modifier.testTag("b02_detail_back"))
}

@Composable
private fun WeightFixture(weight: Float, onWeight: (Float) -> Unit, locked: Boolean, onLocked: (Boolean) -> Unit, onBack: () -> Unit) {
    val weightLabel = stringResource(R.string.weight)
    val lockLabel = stringResource(R.string.lock_meal)
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        BackButton(onBack)
        Text(stringResource(R.string.edit_meal), fontSize = 36.sp)
        Text("食谱微调", style = MiuixTheme.textStyles.footnote1, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
        Card(Modifier.fillMaxWidth(), cornerRadius = 25.dp, insideMargin = PaddingValues(17.dp)) {
            Text("香菇木耳时蔬饭", style = MiuixTheme.textStyles.headline1)
            Text("$weightLabel ${weight.roundToInt()} g", modifier = Modifier.testTag("b02_weight_value"))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("-100g", style = MiuixTheme.textStyles.footnote2)
                Text("0", style = MiuixTheme.textStyles.footnote2)
                Text("+100g", style = MiuixTheme.textStyles.footnote2)
            }
            Slider(
                value = weight, onValueChange = onWeight, valueRange = 200f..400f, enabled = !locked,
                modifier = Modifier.testTag("b02_weight_slider").semantics {
                    contentDescription = weightLabel
                    if (locked) disabled()
                },
            )
        }
        Text("更多设置", style = MiuixTheme.textStyles.footnote1, color = MiuixTheme.colorScheme.onSurfaceVariantSummary)
        Card(Modifier.fillMaxWidth(), cornerRadius = 25.dp) {
            BasicComponent(
                title = lockLabel,
                summary = "锁定后可解锁再编辑",
                endActions = {
                    Switch(checked = locked, onCheckedChange = onLocked, modifier = Modifier.testTag("b02_lock_switch").semantics { contentDescription = lockLabel })
                },
            )
        }
    }
}

private val filterOptions = listOf(
    listOf("全部重量", "100 g <", "100~200 g", "200~300 g", "300~400 g", "400~500 g", "500~600 g", "600 g >"),
    listOf("全部热量", "100 Kcal <", "100~200 Kcal", "200~300 Kcal", "300~400 Kcal", "400 Kcal >"),
    listOf("全部分类", "热菜", "凉菜", "熟食", "生鲜", "主食", "荤菜", "素菜", "其它", "食材"),
)
