package com.yunobase.recipe.compat

import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.annotation.DoNotInline
import androidx.annotation.RequiresApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import top.yukonga.miuix.kmp.blur.blur
import top.yukonga.miuix.kmp.blur.drawBackdrop
import top.yukonga.miuix.kmp.blur.layerBackdrop
import top.yukonga.miuix.kmp.blur.rememberLayerBackdrop
import top.yukonga.miuix.kmp.blur.highlight.Highlight
import top.yukonga.miuix.kmp.blur.highlight.BloomStroke
import top.yukonga.miuix.kmp.blur.highlight.LightPosition
import top.yukonga.miuix.kmp.blur.highlight.LightSource
import top.yukonga.miuix.kmp.theme.MiuixTheme
import java.util.concurrent.atomic.AtomicBoolean

/**
 * The low-API entry point exposes only Compose types. Never place blur/shader state in this
 * function or a shared application initializer. R8 must preserve EnhancedMaterial separately.
 */
@Composable
internal fun MaterialHost(
    useEnhanced: Boolean = true,
    forceEffectFailure: Boolean = false,
    forceDrawFailure: Boolean = false,
    disableRefraction: Boolean = false,
    content: @Composable (Modifier, Modifier) -> Unit,
) {
    var failed by remember { mutableStateOf(false) }
    val failureScheduled = remember { AtomicBoolean(false) }
    val handler = remember { Handler(Looper.getMainLooper()) }
    val onFailure = remember {
        {
            if (failureScheduled.compareAndSet(false, true)) {
                Log.w("YunoB02", "effect-failed; fallback=clear")
                // Rendering/attachment can run in a snapshot observer; change composition later.
                handler.post { failed = true }
            }
            Unit
        }
    }
    val hardwareAccelerated = LocalView.current.isHardwareAccelerated
    val shaderReady = remember(hardwareAccelerated, useEnhanced) {
        Build.VERSION.SDK_INT >= 33 && useEnhanced && hardwareAccelerated &&
            EnhancedMaterial.probe()
    }
    if (Build.VERSION.SDK_INT >= 33 && shaderReady && !failed) {
        EnhancedMaterial.Content(forceEffectFailure, forceDrawFailure, disableRefraction, onFailure, content)
    } else {
        val surface = MiuixTheme.colorScheme.surface
        LaunchedEffect(Unit) {
            Log.i("YunoB02", "material=clear; api=${Build.VERSION.SDK_INT}")
        }
        content(
            Modifier,
            Modifier.background(surface.copy(alpha = 0.96f), CircleShape)
                .border(1.dp, Color.Gray.copy(alpha = 0.3f), CircleShape),
        )
    }
}

@RequiresApi(33)
internal object EnhancedMaterial {
    @DoNotInline
    fun probe(): Boolean = try {
        // Compile only on the isolated API-33 branch. An unsupported renderer uses clear surfaces.
        android.graphics.RuntimeShader("half4 main(float2 p) { return half4(0.0); }")
        true
    } catch (_: RuntimeException) {
        Log.w("YunoB02", "shader-probe-failed; fallback=clear")
        false
    } catch (_: LinkageError) {
        Log.w("YunoB02", "shader-unavailable; fallback=clear")
        false
    }

    @DoNotInline
    @Composable
    fun Content(
        forceEffectFailure: Boolean,
        forceDrawFailure: Boolean,
        disableRefraction: Boolean,
        onFailure: () -> Unit,
        content: @Composable (Modifier, Modifier) -> Unit,
    ) {
        val backdrop = rememberLayerBackdrop()
        val surface = MiuixTheme.colorScheme.surface
        val pageBackground = MiuixTheme.colorScheme.background
        val dark = pageBackground.luminance() < 0.5f
        val pipelineReported = remember(disableRefraction) { AtomicBoolean(false) }
        val rim = remember(dark) {
            Highlight(
                width = 0.8.dp,
                style = (if (dark) BloomStroke.GlassStrokeSmallDark else BloomStroke.GlassStrokeSmallLight).copy(
                    dualPeak = true,
                    primaryLight = LightSource(LightPosition(0.0f, 0.0f, -0.25f), intensity = 0.75f),
                    secondaryLight = LightSource(LightPosition(1.0f, 1.0f, -0.25f), intensity = 0.15f),
                ),
            )
        }
        LaunchedEffect(Unit) {
            Log.i("YunoB02", "material=enhanced; api=${Build.VERSION.SDK_INT}")
        }
        content(
            // Record the real page color too; transparent gaps are not a valid backdrop.
            Modifier.layerBackdrop(backdrop).background(pageBackground),
            Modifier.shadow(6.dp, CircleShape, clip = false,
                ambientColor = Color.Black.copy(alpha = 0.10f), spotColor = Color.Black.copy(alpha = 0.12f))
                .drawWithContent {
                try {
                    check(!forceDrawFailure) { "B02 injected drawing failure" }
                    drawContent()
                } catch (_: RuntimeException) {
                    drawRect(surface)
                    onFailure()
                } catch (_: LinkageError) {
                    drawRect(surface)
                    onFailure()
                }
            }.drawBackdrop(
                backdrop = backdrop,
                shape = { CircleShape },
                effects = {
                    try {
                        // Test-only launch extra exercises the same failure boundary in debug/R8.
                        check(!forceEffectFailure) { "B02 injected effect initialization failure" }
                        blur(2.dp.toPx())
                        if (!disableRefraction) {
                            lens(24.dp.toPx(), 20.dp.toPx(), chromaticAberration = 0.06f)
                        }
                        if (pipelineReported.compareAndSet(false, true)) {
                            Log.i("YunoB02", "glass-pipeline; refraction=${!disableRefraction}; blurDp=2; lensDp=20")
                        }
                    } catch (_: RuntimeException) {
                        renderEffect = null
                        onFailure()
                    } catch (_: LinkageError) {
                        renderEffect = null
                        onFailure()
                    }
                },
                highlight = { rim },
                onDrawSurface = {
                    drawRect(surface.copy(alpha = if (dark) 0.20f else 0.12f))
                    drawRect(Brush.verticalGradient(
                        listOf(Color.White.copy(alpha = 0.10f), Color.Transparent, Color.Black.copy(alpha = 0.04f)),
                    ))
                },
            ),
        )
    }
}
