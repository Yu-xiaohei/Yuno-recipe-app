package com.yunobase.recipe.design

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import com.yunobase.recipe.R
import androidx.compose.ui.graphics.Color
import top.yukonga.miuix.kmp.theme.lightColorScheme
import top.yukonga.miuix.kmp.theme.darkColorScheme
import top.yukonga.miuix.kmp.theme.MiuixTheme
import top.yukonga.miuix.kmp.theme.ThemeController
import top.yukonga.miuix.kmp.theme.defaultTextStyles

/**
 * Original MiSans VF 4.009, without subsetting or binary edits.
 * Semantic Compose weights map explicitly to the original Regular/Medium/Semibold/Bold axes.
 * The full official agreement and copyright notice ship in assets/misans.
 */
@Composable
internal fun PrototypeTheme(content: @Composable () -> Unit) {
    val controller = remember {
        ThemeController(
            lightColors = lightColorScheme(background = Color(0xFFF5F5F5), surfaceContainer = Color.White),
            darkColors = darkColorScheme(
                background = Color(0xFF101010),
                surfaceContainer = Color(0xFF242424),
                surfaceContainerHigh = Color(0xFF303030),
            ),
        )
    }
    val textStyles = remember {
        val original = defaultTextStyles()
        val family = FontFamily(
            Font(R.font.misans_vf, FontWeight.Normal, variationSettings = FontVariation.Settings(FontVariation.weight(330))),
            Font(R.font.misans_vf, FontWeight.Medium, variationSettings = FontVariation.Settings(FontVariation.weight(380))),
            Font(R.font.misans_vf, FontWeight.SemiBold, variationSettings = FontVariation.Settings(FontVariation.weight(520))),
            Font(R.font.misans_vf, FontWeight.Bold, variationSettings = FontVariation.Settings(FontVariation.weight(630))),
        )
        original.copy(
            main = original.main.copy(fontFamily = family),
            paragraph = original.paragraph.copy(fontFamily = family),
            body1 = original.body1.copy(fontFamily = family),
            body2 = original.body2.copy(fontFamily = family),
            button = original.button.copy(fontFamily = family),
            footnote1 = original.footnote1.copy(fontFamily = family),
            footnote2 = original.footnote2.copy(fontFamily = family),
            headline1 = original.headline1.copy(fontFamily = family),
            headline2 = original.headline2.copy(fontFamily = family),
            subtitle = original.subtitle.copy(fontFamily = family),
            title1 = original.title1.copy(fontFamily = family),
            title2 = original.title2.copy(fontFamily = family),
            title3 = original.title3.copy(fontFamily = family),
            title4 = original.title4.copy(fontFamily = family),
        )
    }
    MiuixTheme(controller = controller, textStyles = textStyles, content = content)
}
