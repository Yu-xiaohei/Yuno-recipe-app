plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.compose.multiplatform)
}

android {
    namespace = "com.yunobase.recipe"
    compileSdk = 37
    buildToolsVersion = "37.0.0"

    defaultConfig {
        // B02 is an isolated compatibility prototype, not the production app.
        applicationId = "com.yunobase.recipe.prototype"
        minSdk = 31
        targetSdk = 37
        versionCode = 2
        versionName = "0.0.2-b02"
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            // Local compatibility checks only; never use this for distribution.
            signingConfig = signingConfigs.getByName("debug")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    sourceSets.getByName("main").assets.srcDir(rootProject.layout.projectDirectory.dir("third_party"))

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
}

kotlin {
    jvmToolchain(21)
}

dependencies {
    implementation(libs.androidx.activity.compose)
    implementation(libs.compose.foundation)
    implementation(libs.compose.ui)
    implementation(libs.miuix.ui)
    // Activated only through the API-33 boundary, after auditing the final APK.
    implementation(libs.miuix.blur)
    // Local SVG fidelity and bounded thumbnail decoding; no networking module.
    implementation(libs.coil.compose)
    implementation(libs.coil.svg)
}
