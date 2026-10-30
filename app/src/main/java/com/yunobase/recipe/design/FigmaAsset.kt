package com.yunobase.recipe.design

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import android.util.Log

/** Exact, local SVG originals. No remote Figma URL, raster tint mask or reconstructed paths. */
@Composable
internal fun FigmaAsset(
    name: String,
    modifier: Modifier,
    tint: Color? = null,
    description: String? = null,
) {
    AsyncImage(
        model = "file:///android_asset/figma/$name.svg",
        contentDescription = description,
        modifier = modifier,
        colorFilter = tint?.let { ColorFilter.tint(it) },
        onError = { Log.e("YunoB02", "asset-error; svg=$name", it.result.throwable) },
    )
}

/** Figma 81:230 / 115:349,351,353,355; original 49×34 geometry and four untouched SVGs. */
@Composable
internal fun BrandWordmark(tint: Color?, description: String) {
    Box(Modifier.width(49.dp).height(34.dp)) {
        FigmaAsset("wordmark_y", Modifier.offset(2.293.dp, 2.601.dp).size(11.0595.dp, 10.9797.dp), tint, description)
        FigmaAsset("wordmark_un", Modifier.offset(14.337.dp, 2.601.dp).size(19.7056.dp, 10.9983.dp), tint)
        FigmaAsset("wordmark_o", Modifier.offset(35.025.dp, 2.614.dp).size(11.0689.dp, 10.9859.dp), tint)
        FigmaAsset("wordmark_recipe", Modifier.offset(1.546.dp, 17.86.dp).size(45.2362.dp, 10.9811.dp), tint)
    }
}
