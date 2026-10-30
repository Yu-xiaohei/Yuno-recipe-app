package com.yunobase.recipe

import android.database.ContentObserver
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.MotionDurationScale
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.createLifecycleAwareWindowRecomposer
import com.yunobase.recipe.design.PrototypeTheme
import coil3.ImageLoader
import coil3.SingletonImageLoader
import coil3.svg.SvgDecoder

/** Isolated, offline B02 compatibility harness. No repository or meal data is persisted here. */
class MainActivity : ComponentActivity() {
    private lateinit var motionScale: PrototypeMotionScale

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        SingletonImageLoader.setSafe { context ->
            ImageLoader.Builder(context).components { add(SvgDecoder.Factory()) }.build()
        }
        enableEdgeToEdge()
        motionScale = PrototypeMotionScale()
        val composeView = ComposeView(this)
        setContentView(composeView)
        composeView.setParentCompositionContext(
            composeView.createLifecycleAwareWindowRecomposer(
                coroutineContext = motionScale,
                lifecycle = lifecycle,
            ),
        )
        composeView.setContent {
            PrototypeTheme {
                PrototypeApp(
                    reducedMotion = motionScale.reduceMotion,
                    onReducedMotionChange = { motionScale.reduceMotion = it },
                    forceEffectFailure = intent.getBooleanExtra("b02.force_effect_failure", false),
                    forceDrawFailure = intent.getBooleanExtra("b02.force_draw_failure", false),
                    disableRefraction = intent.getBooleanExtra("b02.disable_refraction", false),
                    glassCalibration = intent.getBooleanExtra("b02.glass_calibration", false),
                )
            }
        }
        Log.i("YunoB02", "prototype-created; font=MiSans-VF-4.009")
    }

    override fun onDestroy() {
        if (::motionScale.isInitialized) motionScale.close()
        super.onDestroy()
    }

    private inner class PrototypeMotionScale : MotionDurationScale, AutoCloseable {
        var reduceMotion by mutableStateOf(false)
        private var systemScale by mutableFloatStateOf(readSystemScale())
        override val scaleFactor: Float
            get() = if (reduceMotion) 0f else systemScale

        private val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
            override fun onChange(selfChange: Boolean) {
                systemScale = readSystemScale()
            }
        }

        init {
            contentResolver.registerContentObserver(
                Settings.Global.getUriFor(Settings.Global.ANIMATOR_DURATION_SCALE),
                false,
                observer,
            )
        }

        private fun readSystemScale() =
            Settings.Global.getFloat(contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
                .takeIf { it.isFinite() && it >= 0f } ?: 1f

        override fun close() = contentResolver.unregisterContentObserver(observer)
    }
}
